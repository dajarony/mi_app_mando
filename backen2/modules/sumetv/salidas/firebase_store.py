"""
SUME DOCBLOCK

Nombre: Almacén de Datos en Firebase Firestore
Tipo: Salida / Persistencia

Entradas:
- Diccionarios de datos de dispositivos (ej. TVDevice serializado).
- IDs de dispositivos para consultas y eliminaciones.

Acciones:
- Inicializa y gestiona la conexión con Firebase Firestore.
- Proporciona métodos asíncronos para operaciones CRUD (Crear, Leer, Actualizar, Eliminar) en la colección 'devices'.
- Implementa una caché offline básica para mejorar la resiliencia y el rendimiento.
- Recopila estadísticas de rendimiento de las operaciones de Firebase.

Salidas:
- Datos de dispositivos recuperados o confirmación de operaciones.
- Logs detallados sobre el estado de la conexión y las operaciones de Firebase.
"""
import os
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore

# Configurar logging
logger = logging.getLogger("firebase_store")

# Inicializar conexión solo una vez
try:
    if not len(firebase_admin._apps):
        # Usar ruta directa a las credenciales
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if not cred_path:
            # Buscar credenciales en ubicaciones típicas
            potential_paths = [
                "./credenciales/sumetv-94c4a-firebase.json",
                "../credenciales/sumetv-94c4a-firebase.json",
                "../../credenciales/sumetv-94c4a-firebase.json",
                "C:/Users/gatak/Desktop/sumetv terminado.mado con multiples funcionaliades/credenciales/sumetv-94c4a-firebase.json"
            ]
            
            for path in potential_paths:
                if os.path.exists(path):
                    cred_path = path
                    break
            
            if not cred_path:
                logger.warning("No se encontró archivo de credenciales, usando modo offline")
                cred_path = None
        
        if cred_path:
            logger.info(f"Usando credenciales de Firebase en: {cred_path}")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Conexión a Firebase inicializada correctamente")
        else:
            # Inicializar app sin credenciales para modo offline
            firebase_admin.initialize_app()
            logger.warning("Firebase inicializado en modo offline (sin credenciales)")
except Exception as e:
    logger.error(f"Error al inicializar Firebase: {e}")
    logger.warning("Firebase operará en modo fallback")

# Instancia global de Firestore
try:
    db = firestore.client()
    logger.info("Cliente Firestore creado correctamente")
except Exception as e:
    logger.error(f"Error al crear cliente Firestore: {e}")
    db = None

# Caché para operaciones offline
OFFLINE_CACHE = {
    "devices": {}
}

class FirebaseStore:
    """Gestiona la persistencia de datos en Firebase."""
    
    def __init__(self):
        """Inicializa el FirebaseStore, configurando la referencia a la colección de dispositivos."""
        # Referencia a la colección de dispositivos
        if db:
            self.devices_ref = db.collection('devices')
            logger.info("FirebaseStore inicializado, colección 'devices' lista")
        else:
            self.devices_ref = None
            logger.warning("FirebaseStore inicializado en modo offline")
        
        # Estadísticas de rendimiento
        self.last_operation_time = 0
        self.operation_count = 0
        self.total_operation_time = 0
        
    async def save_device(self, device_data: dict) -> dict:
        """Guarda o actualiza un dispositivo en Firestore.

        Args:
            device_data (dict): Datos del dispositivo a guardar.

        Returns:
            dict: Datos guardados.

        Raises:
            ValueError: Si device_id es obligatorio y no se proporciona.
        """
        start_time = time.time()
        device_id = device_data.get("device_id")
        
        if not device_id:
            logger.error("Intento de guardar dispositivo sin device_id")
            raise ValueError("device_id es obligatorio")
        
        try:
            # Guardar en caché offline como respaldo
            OFFLINE_CACHE["devices"][device_id] = device_data.copy()
            
            # Si no hay conexión a Firestore, retornar los datos guardados en caché
            if not db or not self.devices_ref:
                logger.info(f"Dispositivo guardado en caché offline: {device_id}")
                return device_data
            
            # Establecer timestamp si no existe
            if "registered_at" not in device_data:
                device_data["registered_at"] = firestore.SERVER_TIMESTAMP
            
            # Función para ejecutar en un hilo separado
            def _save_to_firestore():
                self.devices_ref.document(device_id).set(device_data)
                return device_data
            
            # Ejecutar en un hilo para no bloquear
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _save_to_firestore)
            
            # Actualizar estadísticas
            operation_time = time.time() - start_time
            self.last_operation_time = operation_time
            self.operation_count += 1
            self.total_operation_time += operation_time
            
            logger.info(f"Dispositivo guardado en Firestore: {device_id} (tiempo: {operation_time:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"Error al guardar dispositivo en Firestore: {e}")
            # Devolver los datos de la caché como fallback
            logger.info(f"Usando caché offline como fallback para: {device_id}")
            return OFFLINE_CACHE["devices"].get(device_id, device_data)
    
    async def get_device(self, device_id: str) -> Optional[dict]:
        """Obtiene un dispositivo por su ID desde Firestore o la caché offline.

        Args:
            device_id (str): El ID del dispositivo a obtener.

        Returns:
            Optional[dict]: Un diccionario con los datos del dispositivo si se encuentra, o None.
        """
        start_time = time.time()
        
        # Optimización: Verificar primero la caché offline
        if device_id in OFFLINE_CACHE["devices"]:
            logger.info(f"Dispositivo recuperado desde caché offline: {device_id}")
            return OFFLINE_CACHE["devices"][device_id]
        
        # Si no hay conexión a Firestore, retornar None
        if not db or not self.devices_ref:
            logger.warning(f"No hay conexión a Firestore, no se puede recuperar: {device_id}")
            return None
        
        try:
            # Función para ejecutar en un hilo separado
            def _get_from_firestore():
                doc = self.devices_ref.document(device_id).get()
                return doc.to_dict() if doc.exists else None
            
            # Ejecutar en un hilo para no bloquear
            logger.info(f"[DIAGNOSTICO] get_device: Antes de ejecutar en el executor.")
            # Función para ejecutar en un hilo separado
            def _get_from_firestore():
                logger.info(f"[DIAGNOSTICO] _get_from_firestore: Entrando al hilo para device_id: {device_id}")
                doc = self.devices_ref.document(device_id).get()
                logger.info(f"[DIAGNOSTICO] _get_from_firestore: La llamada .get() para {device_id} ha finalizado.")
                return doc.to_dict() if doc.exists else None
            
            # Ejecutar en un hilo para no bloquear
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _get_from_firestore)
            logger.info(f"[DIAGNOSTICO] get_device: Después de ejecutar en el executor.")
            
            # Actualizar estadísticas
            operation_time = time.time() - start_time
            self.last_operation_time = operation_time
            self.operation_count += 1
            self.total_operation_time += operation_time
            
            if result:
                # Actualizar caché offline
                OFFLINE_CACHE["devices"][device_id] = result
                logger.info(f"Dispositivo recuperado de Firestore: {device_id} (tiempo: {operation_time:.2f}s)")
            else:
                logger.info(f"Dispositivo no encontrado en Firestore: {device_id}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error al obtener dispositivo {device_id} de Firestore: {e}")
            return None
    
    async def list_devices(self) -> List[Dict[str, Any]]:
        """Lista todos los dispositivos desde Firestore o la caché offline.

        Returns:
            List[Dict[str, Any]]: Una lista de diccionarios, cada uno representando un dispositivo.
        """
        start_time = time.time()
        logger.info("Firebase Store: Iniciando consulta de dispositivos")
        
        # Si no hay conexión a Firestore, retornar la caché offline
        if not db or not self.devices_ref:
            devices = list(OFFLINE_CACHE["devices"].values())
            logger.info(f"Listando {len(devices)} dispositivos desde caché offline")
            return devices
        
        try:
            # Función para ejecutar en un hilo separado
            def _list_from_firestore():
                return list(self.devices_ref.stream())
            
            # Ejecutar en un hilo para no bloquear
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, _list_from_firestore)
            
            # Convertir documentos a diccionarios
            result = [d.to_dict() for d in docs]
            
            # Actualizar caché offline
            for device in result:
                if "device_id" in device:
                    OFFLINE_CACHE["devices"][device["device_id"]] = device
            
            # Actualizar estadísticas
            operation_time = time.time() - start_time
            self.last_operation_time = operation_time
            self.operation_count += 1
            self.total_operation_time += operation_time
            
            logger.info(f"Recuperados {len(result)} dispositivos de Firestore (tiempo: {operation_time:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"Error al listar dispositivos desde Firestore: {e}")
            # Devolver datos de caché offline como fallback
            devices = list(OFFLINE_CACHE["devices"].values())
            logger.info(f"Fallback: Listando {len(devices)} dispositivos desde caché offline")
            return devices
    
    async def delete_device(self, device_id: str) -> bool:
        """Elimina un dispositivo por su ID de Firestore y la caché offline.

        Args:
            device_id (str): El ID del dispositivo a eliminar.

        Returns:
            bool: True si se eliminó correctamente, False si no existe o hubo un error.
        """
        start_time = time.time()
        
        # Eliminar de la caché offline
        was_in_cache = device_id in OFFLINE_CACHE["devices"]
        if was_in_cache:
            del OFFLINE_CACHE["devices"][device_id]
        
        # Si no hay conexión a Firestore, retornar resultado basado en caché
        if not db or not self.devices_ref:
            logger.info(f"Dispositivo eliminado solo de caché offline: {device_id}")
            return was_in_cache
        
        try:
            # Verificar si existe primero
            doc_exists = False
            
            try:
                def _check_exists():
                    doc = self.devices_ref.document(device_id).get()
                    return doc.exists
                
                loop = asyncio.get_event_loop()
                doc_exists = await loop.run_in_executor(None, _check_exists)
            except Exception as e:
                logger.error(f"Error al verificar existencia para eliminar {device_id}: {e}")
                # Asumir que existe si hay error para intentar eliminar de todos modos
                doc_exists = True
            
            if not doc_exists:
                logger.warning(f"Intento de eliminar dispositivo inexistente: {device_id}")
                return False
            
            # Función para ejecutar en un hilo separado
            def _delete_from_firestore():
                self.devices_ref.document(device_id).delete()
                return True
            
            # Ejecutar en un hilo para no bloquear
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _delete_from_firestore)
            
            # Actualizar estadísticas
            operation_time = time.time() - start_time
            self.last_operation_time = operation_time
            self.operation_count += 1
            self.total_operation_time += operation_time
            
            logger.info(f"Dispositivo eliminado de Firestore: {device_id} (tiempo: {operation_time:.2f}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar dispositivo {device_id} de Firestore: {e}")
            # Si eliminamos de caché, considerarlo eliminado parcialmente
            return was_in_cache
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Obtiene estadísticas de rendimiento de las operaciones de Firebase.

        Returns:
            Dict[str, float]: Un diccionario con las estadísticas de rendimiento.
        """
        return {
            "last_operation_time_seconds": self.last_operation_time,
            "operation_count": self.operation_count,
            "average_operation_time_seconds": (
                self.total_operation_time / self.operation_count 
                if self.operation_count > 0 else 0
            )
        }
