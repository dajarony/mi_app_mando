"""
SUME DOCBLOCK

Nombre: Config
Tipo: Lógica

Entradas:
- Ruta a archivo de configuración
- Variables de entorno
- Valores por defecto
- Configuración en memoria

Acciones:
- Cargar configuración desde archivos (YAML, JSON, etc.)
- Combinar configuración de múltiples fuentes
- Validar estructura y tipos de configuración
- Resolver variables y referencias
- Gestionar jerarquía de configuración
- Notificar cambios en la configuración

Salidas:
- Valores de configuración solicitados
- Notificaciones de cambios vía EventBus
- Errores de validación
"""
import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Set
import re


class Config:
    """
    Gestor de configuración para el sistema.
    
    Proporciona acceso unificado a la configuración del sistema,
    combinando múltiples fuentes como archivos, variables de entorno,
    y valores en memoria.
    """
    
    def __init__(self, event_bus=None, logger=None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            event_bus: EventBus para emitir notificaciones (opcional)
            logger: Logger para registrar actividad (opcional)
        """
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(__name__)
        
        # Diccionario principal para almacenar la configuración
        self._config: Dict[str, Any] = {}
        
        # Diccionario de configuración por defecto
        self._defaults: Dict[str, Any] = {}
        
        # Conjunto de claves que no deben ser sobrescritas
        self._locked_keys: Set[str] = set()
        
        # Rutas de archivos cargados
        self._loaded_files: List[str] = []
        
        # Patrones para variables de entorno
        self._env_patterns: Dict[str, str] = {}
        
        self.logger.debug("Config inicializado")
    
    def set_defaults(self, defaults: Dict[str, Any]):
        """
        Establece valores por defecto para la configuración.
        
        Args:
            defaults: Diccionario con valores por defecto
        """
        self._defaults = defaults.copy()
        
        # Aplicar defaults a la configuración actual solo para claves no existentes
        for key, value in self._defaults.items():
            if key not in self._config:
                self._config[key] = value
        
        self.logger.debug("Valores por defecto establecidos")
    
    def load_file(self, file_path: Union[str, Path], required: bool = False) -> bool:
        """
        Carga configuración desde un archivo.
        
        Args:
            file_path: Ruta al archivo (YAML o JSON)
            required: Si es True, lanza una excepción si el archivo no existe
        
        Returns:
            True si el archivo se cargó correctamente
        
        Raises:
            FileNotFoundError: Si required=True y el archivo no existe
            ValueError: Si el formato del archivo no es compatible
        """
        path = Path(file_path)
        
        # Verificar si el archivo existe
        if not path.exists():
            msg = f"Archivo de configuración no encontrado: {path}"
            if required:
                self.logger.error(msg)
                raise FileNotFoundError(msg)
            else:
                self.logger.warning(msg)
                return False
        
        try:
            # Determinar formato por extensión
            if path.suffix.lower() in ('.yaml', '.yml'):
                with open(path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                msg = f"Formato de archivo de configuración no soportado: {path.suffix}"
                self.logger.error(msg)
                raise ValueError(msg)
            
            # Combinar con la configuración actual
            self._merge_config(config_data)
            
            # Guardar ruta del archivo cargado
            self._loaded_files.append(str(path))
            
            self.logger.info(f"Configuración cargada desde {path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error al cargar configuración desde {path}: {str(e)}")
            if required:
                raise
            return False
    
    def _merge_config(self, new_config: Dict[str, Any], prefix: str = ""):
        """
        Combina nueva configuración con la existente.
        
        Args:
            new_config: Nueva configuración a combinar
            prefix: Prefijo para claves anidadas
        """
        for key, value in new_config.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            # Si la clave está bloqueada, no sobrescribir
            if full_key in self._locked_keys:
                self.logger.warning(f"Ignorando actualización de clave bloqueada: {full_key}")
                continue
            
            # Si ambos son diccionarios, combinar recursivamente
            if (full_key in self._config and isinstance(self._config[full_key], dict) and 
                isinstance(value, dict)):
                # Crear nuevo prefijo para claves anidadas
                new_prefix = f"{full_key}." if prefix else f"{key}."
                self._merge_config(value, new_prefix)
            else:
                # Verificar si hay cambio real
                old_value = self._config.get(full_key)
                if old_value != value:
                    # Almacenar nuevo valor
                    self._config[full_key] = value
                    
                    # Emitir evento de cambio
                    if self.event_bus:
                        self.event_bus.emit("config:changed", {
                            'key': full_key,
                            'old_value': old_value,
                            'new_value': value
                        })
    
    def load_env_vars(self, prefix: str = "APP_", pattern: str = None):
        """
        Carga configuración desde variables de entorno.
        
        Args:
            prefix: Prefijo para las variables (se elimina de la clave)
            pattern: Patrón regex opcional para filtrar variables
        """
        if pattern:
            # Compilar patrón y guardar para futuras referencias
            regex = re.compile(pattern)
            self._env_patterns[prefix] = pattern
        else:
            regex = None
        
        # Recorrer todas las variables de entorno
        env_configs = {}
        for key, value in os.environ.items():
            # Verificar prefijo
            if key.startswith(prefix):
                # Eliminar prefijo
                config_key = key[len(prefix):].lower()
                
                # Aplicar patrón si existe
                if regex and not regex.match(key):
                    continue
                
                # Convertir guiones bajos a puntos para crear estructura anidada
                if '_' in config_key:
                    sections = config_key.split('_')
                    current = env_configs
                    for i, section in enumerate(sections):
                        if i == len(sections) - 1:
                            # Último nivel, asignar valor
                            current[section] = self._parse_env_value(value)
                        else:
                            # Nivel intermedio, crear diccionario si no existe
                            if section not in current:
                                current[section] = {}
                            current = current[section]
                else:
                    # Clave simple
                    env_configs[config_key] = self._parse_env_value(value)
        
        # Combinar con configuración existente
        if env_configs:
            self._merge_config(env_configs)
            self.logger.info(f"Configuración cargada desde variables de entorno con prefijo {prefix}")
    
    def _parse_env_value(self, value: str) -> Any:
        """
        Convierte el valor string de una variable de entorno al tipo apropiado.
        
        Args:
            value: Valor string de la variable
            
        Returns:
            Valor convertido al tipo adecuado
        """
        # Valores booleanos
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # Valores numéricos
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Listas separadas por comas
        if ',' in value:
            return [self._parse_env_value(v.strip()) for v in value.split(',')]
        
        # Por defecto, es una string
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración (puede usar puntos para acceso anidado)
            default: Valor a devolver si la clave no existe
            
        Returns:
            Valor de configuración o default si no existe
        """
        # Si la clave existe directamente, devolverla
        if key in self._config:
            return self._config[key]
        
        # Verificar acceso anidado con puntos
        if '.' in key:
            parts = key.split('.')
            current = self._config
            
            # Navegar por la estructura anidada
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    # Si alguna parte no existe, devolver default
                    return default
                current = current[part]
            
            # Si llegamos aquí, encontramos el valor
            return current
        
        # Clave no encontrada
        return default
    
    def set(self, key: str, value: Any, lock: bool = False) -> bool:
        """
        Establece un valor de configuración en memoria.
        
        Args:
            key: Clave de configuración (puede usar puntos para acceso anidado)
            value: Valor a establecer
            lock: Si es True, la clave no podrá ser modificada posteriormente
            
        Returns:
            True si se estableció correctamente
        """
        # Determinar si es una clave anidada
        if '.' in key:
            parts = key.split('.')
            current = self._config
            
            # Navegar y crear estructura si es necesario
            for i, part in enumerate(parts[:-1]):
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            
            # Último nivel
            last_key = parts[-1]
            old_value = current.get(last_key)
            
            # Verificar cambio real
            if old_value != value:
                current[last_key] = value
                
                # Emitir evento de cambio
                if self.event_bus:
                    self.event_bus.emit("config:changed", {
                        'key': key,
                        'old_value': old_value,
                        'new_value': value
                    })
        else:
            # Clave simple
            old_value = self._config.get(key)
            
            # Verificar cambio real
            if old_value != value:
                self._config[key] = value
                
                # Emitir evento de cambio
                if self.event_bus:
                    self.event_bus.emit("config:changed", {
                        'key': key,
                        'old_value': old_value,
                        'new_value': value
                    })
        
        # Bloquear clave si se solicitó
        if lock:
            self._locked_keys.add(key)
        
        self.logger.debug(f"Configuración establecida: {key}")
        return True
    
    def lock_key(self, key: str) -> bool:
        """
        Bloquea una clave para evitar modificaciones.
        
        Args:
            key: Clave a bloquear
            
        Returns:
            True si la clave existe y fue bloqueada
        """
        if key in self._config or '.' in key:
            self._locked_keys.add(key)
            self.logger.debug(f"Clave bloqueada: {key}")
            return True
        return False
    
    def unlock_key(self, key: str) -> bool:
        """
        Desbloquea una clave para permitir modificaciones.
        
        Args:
            key: Clave a desbloquear
            
        Returns:
            True si la clave estaba bloqueada y fue desbloqueada
        """
        if key in self._locked_keys:
            self._locked_keys.remove(key)
            self.logger.debug(f"Clave desbloqueada: {key}")
            return True
        return False
    
    def has(self, key: str) -> bool:
        """
        Verifica si una clave existe en la configuración.
        
        Args:
            key: Clave a verificar
            
        Returns:
            True si la clave existe
        """
        # Verificar existencia directa
        if key in self._config:
            return True
        
        # Verificar acceso anidado
        if '.' in key:
            parts = key.split('.')
            current = self._config
            
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    return False
                current = current[part]
            
            return True
        
        return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        Obtiene una copia de toda la configuración.
        
        Returns:
            Diccionario con toda la configuración
        """
        return self._config.copy()
    
    def get_loaded_files(self) -> List[str]:
        """
        Obtiene la lista de archivos de configuración cargados.
        
        Returns:
            Lista de rutas de archivos
        """
        return self._loaded_files.copy()
    
    def get_locked_keys(self) -> List[str]:
        """
        Obtiene la lista de claves bloqueadas.
        
        Returns:
            Lista de claves bloqueadas
        """
        return list(self._locked_keys)
    
    def save_to_file(self, file_path: Union[str, Path], sections: List[str] = None) -> bool:
        """
        Guarda la configuración actual a un archivo.
        
        Args:
            file_path: Ruta donde guardar el archivo
            sections: Lista de secciones a guardar (None para todas)
            
        Returns:
            True si se guardó correctamente
        """
        path = Path(file_path)
        
        try:
            # Preparar datos a guardar
            if sections:
                data = {}
                for section in sections:
                    if section in self._config:
                        data[section] = self._config[section]
            else:
                data = self._config.copy()
            
            # Crear directorio si no existe
            if path.parent and not path.parent.exists():
                path.parent.mkdir(parents=True)
            
            # Guardar según formato
            if path.suffix.lower() in ('.yaml', '.yml'):
                with open(path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            elif path.suffix.lower() == '.json':
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                self.logger.error(f"Formato no soportado para guardar: {path.suffix}")
                return False
            
            self.logger.info(f"Configuración guardada en {path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error al guardar configuración en {path}: {str(e)}")
            return False