"""
SUME DOCBLOCK

Nombre: Store
Tipo: Lógica

Entradas:
- Solicitudes de almacenamiento (set): key, value, ttl
- Solicitudes de recuperación (get): key
- Solicitudes de eliminación (delete): key
- Consultas de filtrado: pattern, max_results

Acciones:
- Almacenar pares clave-valor en memoria o persistencia
- Recuperar valores por clave o patrón
- Establecer caducidad (TTL) para entradas
- Notificar cambios mediante eventos
- Persistir datos críticos (opcional)
- Mantener historial de cambios para keys seleccionadas
- Proporcionar estadísticas de uso

Salidas:
- Valores recuperados
- Notificaciones de cambios vía EventBus
- Estadísticas de operaciones
"""
import time
import fnmatch
import json
import logging
import os
import threading
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple, Union, Iterator


class Store:
    """
    Almacén clave-valor con soporte para eventos, TTL y persistencia opcional.
    
    Proporciona un mecanismo unificado para que los componentes almacenen
    y compartan datos, con notificaciones de cambios y caducidad automática.
    """

    def __init__(self, event_bus=None, logger=None, persist_dir=None):
        """
        Inicializa un nuevo Store.
        
        Args:
            event_bus: EventBus para emitir notificaciones (opcional)
            logger: Logger para registrar actividad (opcional)
            persist_dir: Directorio para persistencia de datos (opcional)
        """
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(__name__)
        self.persist_dir = persist_dir
        
        # Diccionario principal para almacenar los datos
        self._data: Dict[str, Any] = {}
        
        # Diccionario para almacenar metadatos (TTL, etc.)
        self._metadata: Dict[str, Dict[str, Any]] = {}
        
        # Conjunto de claves que requieren historial de cambios
        self._versioned_keys: Set[str] = set()
        
        # Bloqueo para operaciones concurrentes
        self._lock = threading.RLock()
        
        # Estadísticas
        self._stats = {
            'sets': 0,
            'gets': 0,
            'hits': 0,
            'misses': 0,
            'deletes': 0,
            'expirations': 0
        }
        
        # Inicializar persistencia si está configurada
        if self.persist_dir:
            self._init_persistence()
        
        # Iniciar tarea de limpieza de TTL
        self._start_ttl_cleanup()
        
        self.logger.debug("Store inicializado")

    def _init_persistence(self):
        """Inicializa el sistema de persistencia si está habilitado."""
        try:
            # Crear directorio de persistencia si no existe
            persist_path = Path(self.persist_dir)
            persist_path.mkdir(parents=True, exist_ok=True)
            
            # Cargar datos persistentes existentes
            self._load_persisted_data()
            
            self.logger.info(f"Persistencia inicializada en {self.persist_dir}")
        except Exception as e:
            self.logger.error(f"Error al inicializar persistencia: {str(e)}")

    def _load_persisted_data(self):
        """Carga datos persistentes desde disco."""
        persist_path = Path(self.persist_dir)
        for file_path in persist_path.glob("*.json"):
            try:
                key = file_path.stem  # Nombre del archivo sin extensión
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Si hay metadatos, cargarlos también
                value = data.get('value')
                metadata = data.get('metadata', {})
                
                # Verificar TTL
                if 'expires_at' in metadata and metadata['expires_at'] <= time.time():
                    # Expirado, eliminar archivo
                    os.remove(file_path)
                    continue
                
                # Almacenar en memoria
                self._data[key] = value
                self._metadata[key] = metadata
                
                # Registrar historial si es necesario
                if metadata.get('versioned', False):
                    self._versioned_keys.add(key)
                
                self.logger.debug(f"Cargado de persistencia: {key}")
            except Exception as e:
                self.logger.error(f"Error al cargar {file_path}: {str(e)}")

    def _persist_key(self, key: str):
        """
        Persiste una clave específica a disco si la persistencia está habilitada.
        
        Args:
            key: Clave a persistir
        """
        if not self.persist_dir or key not in self._data:
            return
        
        try:
            persist_path = Path(self.persist_dir) / f"{key}.json"
            metadata = self._metadata.get(key, {})
            
            # Si tiene historial, añadir también la versión actual
            if key in self._versioned_keys and 'history' in metadata:
                metadata = metadata.copy()  # Evitar modificar el original
                metadata['current_version'] = len(metadata.get('history', []))
            
            # Preparar datos para persistencia
            data = {
                'value': self._data[key],
                'metadata': metadata
            }
            
            # Escribir a disco
            with open(persist_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"Persistido: {key}")
        except Exception as e:
            self.logger.error(f"Error al persistir {key}: {str(e)}")

    def _start_ttl_cleanup(self):
        """Inicia un hilo para limpiar entradas caducadas periódicamente."""
        def cleanup_worker():
            while True:
                try:
                    self._cleanup_expired()
                except Exception as e:
                    self.logger.error(f"Error en limpieza TTL: {str(e)}")
                
                # Ejecutar cada 10 segundos
                time.sleep(10)
        
        # Iniciar hilo en modo daemon
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        self.logger.debug("Iniciada tarea de limpieza TTL")

    def _cleanup_expired(self):
        """Elimina entradas que han alcanzado su TTL."""
        current_time = time.time()
        keys_to_delete = []
        
        with self._lock:
            # Identificar claves expiradas
            for key, metadata in self._metadata.items():
                if 'expires_at' in metadata and metadata['expires_at'] <= current_time:
                    keys_to_delete.append(key)
            
            # Eliminar claves expiradas
            for key in keys_to_delete:
                self._delete_internal(key, expired=True)

    def _delete_internal(self, key: str, expired: bool = False):
        """
        Implementación interna de eliminación de claves.
        
        Args:
            key: Clave a eliminar
            expired: True si la eliminación se debe a expiración por TTL
        """
        if key in self._data:
            # Obtener valor antes de eliminar (para el evento)
            old_value = self._data.get(key)
            
            # Eliminar de los diccionarios
            del self._data[key]
            if key in self._metadata:
                del self._metadata[key]
            
            # Eliminar del conjunto de versionados si existe
            if key in self._versioned_keys:
                self._versioned_keys.remove(key)
            
            # Actualizar estadísticas
            if expired:
                self._stats['expirations'] += 1
            else:
                self._stats['deletes'] += 1
            
            # Eliminar archivo persistente si existe
            if self.persist_dir:
                persist_path = Path(self.persist_dir) / f"{key}.json"
                if persist_path.exists():
                    try:
                        os.remove(persist_path)
                    except Exception as e:
                        self.logger.error(f"Error al eliminar archivo persistente {key}: {str(e)}")
            
            # Emitir evento
            if self.event_bus:
                event_type = 'expired' if expired else 'deleted'
                self.event_bus.emit(f"store:key:{event_type}", {
                    'key': key,
                    'old_value': old_value
                })
                
                # Evento genérico de cambio
                self.event_bus.emit(f"store:key:changed", {
                    'key': key,
                    'type': event_type,
                    'old_value': old_value,
                    'new_value': None
                })
            
            self.logger.debug(f"Clave {key} {'expirada' if expired else 'eliminada'}")
            return True
        
        return False

    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            persist: Optional[bool] = None, versioned: bool = False) -> bool:
        """
        Almacena un valor asociado a una clave.
        
        Args:
            key: Clave única para identificar el valor
            value: Valor a almacenar (debe ser serializable si se usa persistencia)
            ttl: Tiempo de vida en segundos (None para sin caducidad)
            persist: Forzar o evitar persistencia para esta clave
                    (None para usar configuración global)
            versioned: Si es True, mantiene historial de cambios para esta clave
        
        Returns:
            True si la operación fue exitosa
        """
        with self._lock:
            # Comprobar si hay cambio real
            old_value = self._data.get(key, None)
            is_update = key in self._data
            value_changed = old_value != value if is_update else True
            
            # Guardar el valor
            self._data[key] = value
            
            # Calcular tiempo de expiración si se especificó TTL
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            
            # Preparar o actualizar metadatos
            if key not in self._metadata:
                self._metadata[key] = {}
            
            # Actualizar metadatos
            metadata = self._metadata[key]
            if expires_at is not None:
                metadata['expires_at'] = expires_at
            elif 'expires_at' in metadata:
                del metadata['expires_at']  # Eliminar TTL anterior
            
            # Configurar versionado
            if versioned and key not in self._versioned_keys:
                self._versioned_keys.add(key)
                metadata['versioned'] = True
                metadata['history'] = []
            
            # Si la clave es versionada y hay cambio real, añadir al historial
            if key in self._versioned_keys and value_changed:
                if 'history' not in metadata:
                    metadata['history'] = []
                
                # Añadir versión anterior al historial
                if is_update:
                    metadata['history'].append({
                        'value': old_value,
                        'timestamp': time.time()
                    })
            
            # Actualizar estadísticas
            self._stats['sets'] += 1
            
            # Persistir si es necesario
            should_persist = persist if persist is not None else (self.persist_dir is not None)
            if should_persist and self.persist_dir:
                self._persist_key(key)
            
            # Emitir eventos si hay cambio real
            if self.event_bus and value_changed:
                event_type = 'updated' if is_update else 'created'
                self.event_bus.emit(f"store:key:{event_type}", {
                    'key': key,
                    'old_value': old_value,
                    'new_value': value
                })
                
                # Evento genérico de cambio
                self.event_bus.emit(f"store:key:changed", {
                    'key': key,
                    'type': event_type,
                    'old_value': old_value,
                    'new_value': value
                })
            
            # Log
            log_msg = f"Clave {key} {'actualizada' if is_update else 'creada'}"
            if ttl is not None:
                log_msg += f" (TTL: {ttl}s)"
            self.logger.debug(log_msg)
            
            return True

    def get(self, key: str, default: Any = None) -> Any:
        """
        Recupera el valor asociado a una clave.
        
        Args:
            key: Clave a buscar
            default: Valor a devolver si la clave no existe
        
        Returns:
            Valor asociado a la clave o default si no existe
        """
        with self._lock:
            self._stats['gets'] += 1
            
            if key in self._data:
                # Verificar TTL
                metadata = self._metadata.get(key, {})
                if 'expires_at' in metadata and metadata['expires_at'] <= time.time():
                    # Expirado, eliminar y devolver default
                    self._delete_internal(key, expired=True)
                    self._stats['misses'] += 1
                    return default
                
                # Clave válida, devolver valor
                self._stats['hits'] += 1
                return self._data[key]
            
            # Clave no encontrada
            self._stats['misses'] += 1
            return default

    def delete(self, key: str) -> bool:
        """
        Elimina una clave del almacén.
        
        Args:
            key: Clave a eliminar
        
        Returns:
            True si la clave existía y fue eliminada, False en caso contrario
        """
        with self._lock:
            return self._delete_internal(key)

    def has(self, key: str) -> bool:
        """
        Verifica si una clave existe en el almacén.
        
        Args:
            key: Clave a verificar
        
        Returns:
            True si la clave existe y no ha expirado, False en caso contrario
        """
        with self._lock:
            if key not in self._data:
                return False
            
            # Verificar TTL
            metadata = self._metadata.get(key, {})
            if 'expires_at' in metadata and metadata['expires_at'] <= time.time():
                # Expirado, eliminar
                self._delete_internal(key, expired=True)
                return False
            
            return True

    def get_many(self, pattern: str) -> Dict[str, Any]:
        """
        Recupera múltiples valores cuyas claves coinciden con un patrón.
        
        Args:
            pattern: Patrón glob para filtrar claves (e.g., 'user:*')
        
        Returns:
            Diccionario con las claves y valores que coinciden
        """
        result = {}
        current_time = time.time()
        
        with self._lock:
            # Buscar claves que coincidan con el patrón
            for key in self._data.keys():
                if fnmatch.fnmatch(key, pattern):
                    # Verificar TTL
                    metadata = self._metadata.get(key, {})
                    if 'expires_at' in metadata and metadata['expires_at'] <= current_time:
                        # Expirado, eliminar
                        self._delete_internal(key, expired=True)
                        continue
                    
                    # Clave válida, añadir al resultado
                    result[key] = self._data[key]
        
        self._stats['gets'] += 1
        return result

    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        Obtiene las claves que coinciden con un patrón opcional.
        
        Args:
            pattern: Patrón glob para filtrar claves, None para todas
        
        Returns:
            Lista de claves que coinciden con el patrón
        """
        result = []
        current_time = time.time()
        
        with self._lock:
            # Verificar todas las claves
            for key in list(self._data.keys()):  # Lista para permitir modificación durante iteración
                # Verificar TTL
                metadata = self._metadata.get(key, {})
                if 'expires_at' in metadata and metadata['expires_at'] <= current_time:
                    # Expirado, eliminar
                    self._delete_internal(key, expired=True)
                    continue
                
                # Verificar patrón si se especificó
                if pattern is None or fnmatch.fnmatch(key, pattern):
                    result.append(key)
        
        return result

    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Elimina todas las claves que coinciden con un patrón opcional.
        
        Args:
            pattern: Patrón glob para filtrar claves a eliminar, None para todas
        
        Returns:
            Número de claves eliminadas
        """
        count = 0
        
        with self._lock:
            # Identificar claves a eliminar
            keys_to_delete = self.keys(pattern)
            
            # Eliminar cada clave
            for key in keys_to_delete:
                if self._delete_internal(key):
                    count += 1
        
        return count

    def get_version_history(self, key: str) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de versiones para una clave versionada.
        
        Args:
            key: Clave versionada
        
        Returns:
            Lista de versiones anteriores con timestamps, más reciente primero
        """
        with self._lock:
            # Verificar si la clave existe y está versionada
            if key not in self._versioned_keys or key not in self._data:
                return []
            
            # Obtener historial
            metadata = self._metadata.get(key, {})
            history = metadata.get('history', [])
            
            # Crear entrada para la versión actual
            current_version = {
                'value': self._data[key],
                'timestamp': time.time(),
                'is_current': True
            }
            
            # Devolver historial en orden inverso (más reciente primero)
            result = [current_version]
            result.extend(reversed(history))
            return result

    def get_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas del almacén.
        
        Returns:
            Diccionario con estadísticas de operaciones
        """
        with self._lock:
            stats = self._stats.copy()
            
            # Añadir conteo actual de claves
            stats['key_count'] = len(self._data)
            stats['versioned_keys'] = len(self._versioned_keys)
            
            # Calcular hit ratio
            if stats['gets'] > 0:
                stats['hit_ratio'] = stats['hits'] / stats['gets']
            else:
                stats['hit_ratio'] = 0
                
            return stats


# Función para pruebas rápidas del módulo
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    store = Store()
    
    # Pruebas básicas
    store.set("test_key", "test_value")
    print("test_key:", store.get("test_key"))
    
    # Prueba de TTL
    store.set("ttl_key", "expires_soon", ttl=2)
    print("ttl_key (inicial):", store.get("ttl_key"))
    time.sleep(3)
    print("ttl_key (después de TTL):", store.get("ttl_key"))
    
    # Estadísticas
    print("Estadísticas:", store.get_stats())