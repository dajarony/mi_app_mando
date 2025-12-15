"""
SUME DOCBLOCK

Nombre: Logger
Tipo: Lógica

Entradas:
- Mensajes de log con nivel (debug, info, warning, error, critical)
- Configuración de salidas (consola, archivo, eventbus)
- Contexto de componente (nombre, id)

Acciones:
- Formatear mensajes de log con timestamp, nivel, componente
- Enrutar mensajes a las salidas configuradas
- Filtrar mensajes según nivel configurado
- Emitir eventos para logs de ciertos niveles
- Capturar excepciones no manejadas
- Mantener contexto por componente

Salidas:
- Mensajes formateados en consola
- Mensajes almacenados en archivos
- Eventos emitidos al EventBus
"""
import logging
import sys
import os
import time
import traceback
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List, Set, Union, Callable


class ContextAdapter(logging.LoggerAdapter):
    """Adaptador que añade contexto a los mensajes de log."""
    
    def process(self, msg, kwargs):
        # Añadir contexto al mensaje
        context_str = " ".join(f"{k}={v}" for k, v in self.extra.items())
        if context_str:
            return f"{msg} [{context_str}]", kwargs
        return msg, kwargs


class SumeLogger:
    """
    Sistema de logging avanzado para el Core Dajarony.
    
    Proporciona capacidades de registro con múltiples salidas,
    filtrado por nivel, y emisión de eventos.
    """
    
    # Mapeo de nombres de nivel a valores numéricos
    LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'warn': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    def __init__(self, event_bus=None, config=None):
        """
        Inicializa el sistema de logging.
        
        Args:
            event_bus: EventBus para emitir eventos de log (opcional)
            config: Configuración del sistema (opcional)
        """
        self.event_bus = event_bus
        self.config = config or {}
        
        # Configuración por defecto
        self.level = self.LEVELS.get(
            self.config.get('logging', {}).get('level', 'info').lower(),
            logging.INFO
        )
        
        # Archivo de log
        self.log_file = self.config.get('logging', {}).get('file')
        
        # Crear directorio para logs si es necesario
        if self.log_file:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
        
        # Configurar logger raíz
        self._setup_root_logger()
        
        # Logger principal para este módulo
        self._logger = logging.getLogger('core_dajarony')
        
        # Diccionario para almacenar loggers por componente
        self._component_loggers: Dict[str, logging.LoggerAdapter] = {}
        
        # Bloqueo para operaciones concurrentes
        self._lock = threading.RLock()
        
        # Auto-log de inicialización
        self._logger.info(f"Sistema de logging inicializado (nivel: {self.level_name})")
    
    @property
    def level_name(self) -> str:
        """Obtiene el nombre del nivel de log actual."""
        for name, value in self.LEVELS.items():
            if value == self.level and name not in ('warn',):  # Excluir alias
                return name
        return 'unknown'
    
    def _setup_root_logger(self):
        """Configura el logger raíz con los handlers necesarios."""
        # Reset de la configuración anterior
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        
        # Establecer nivel
        root.setLevel(self.level)
        
        # Formatter estándar
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler de consola
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(self.level)
        console.setFormatter(formatter)
        root.addHandler(console)
        
        # Handler de archivo si está configurado
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(self.level)
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
    
    def get_logger(self, component_name: str, **context) -> logging.LoggerAdapter:
        """
        Obtiene un logger para un componente específico con contexto.
        
        Args:
            component_name: Nombre del componente
            **context: Pares clave-valor para añadir como contexto
        
        Returns:
            Logger adaptado con el contexto
        """
        with self._lock:
            # Crear una clave única para el componente + contexto
            context_values = tuple(sorted(context.items()))
            key = (component_name, context_values)
            
            # Devolver logger existente si ya fue creado
            if key in self._component_loggers:
                return self._component_loggers[key]
            
            # Crear nuevo logger
            logger = logging.getLogger(f'core_dajarony.{component_name}')
            
            # Añadir contexto
            adapter = ContextAdapter(logger, context)
            
            # Almacenar y devolver
            self._component_loggers[key] = adapter
            return adapter
    
    def set_level(self, level: Union[str, int]):
        """
        Cambia el nivel de log.
        
        Args:
            level: Nivel de log (nombre o valor numérico)
        """
        if isinstance(level, str):
            level = self.LEVELS.get(level.lower(), logging.INFO)
        
        self.level = level
        
        # Actualizar logger raíz
        root = logging.getLogger()
        root.setLevel(level)
        
        # Actualizar handlers
        for handler in root.handlers:
            handler.setLevel(level)
        
        self._logger.info(f"Nivel de log cambiado a {self.level_name}")
    
    def emit_log_event(self, level: int, msg: str, component: str, **context):
        """
        Emite un evento de log al EventBus si está disponible.
        
        Args:
            level: Nivel numérico del log
            msg: Mensaje de log
            component: Nombre del componente
            **context: Contexto adicional
        """
        if not self.event_bus:
            return
        
        # Convertir nivel a nombre
        level_name = logging.getLevelName(level).lower()
        
        # Solo emitir eventos para warning y superiores
        if level >= logging.WARNING:
            try:
                self.event_bus.emit(f"log:{level_name}", {
                    'message': msg,
                    'component': component,
                    'timestamp': datetime.now().isoformat(),
                    'context': context
                })
            except Exception as e:
                # Evitar recursión si hay error al emitir
                if not msg.startswith("Error al emitir evento de log"):
                    self._logger.error(f"Error al emitir evento de log: {str(e)}")
    
    def install_exception_handler(self):
        """
        Instala un manejador global de excepciones no capturadas.
        """
        def handle_exception(exc_type, exc_value, exc_traceback):
            """Manejador de excepciones no capturadas."""
            if issubclass(exc_type, KeyboardInterrupt):
                # Permitir que Ctrl+C cierre la aplicación normalmente
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Log de la excepción
            self._logger.critical(
                "Excepción no capturada:",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            # Emitir evento si hay EventBus
            if self.event_bus:
                tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                self.event_bus.emit("system:uncaught_exception", {
                    'type': exc_type.__name__,
                    'value': str(exc_value),
                    'traceback': tb_str,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Instalar el manejador
        sys.excepthook = handle_exception
        self._logger.info("Manejador de excepciones no capturadas instalado")
    
    def debug(self, msg, *args, **kwargs):
        """Log a nivel debug."""
        self._logger.debug(msg, *args, **kwargs)
        self.emit_log_event(logging.DEBUG, msg, 'core_dajarony')
    
    def info(self, msg, *args, **kwargs):
        """Log a nivel info."""
        self._logger.info(msg, *args, **kwargs)
        self.emit_log_event(logging.INFO, msg, 'core_dajarony')
    
    def warning(self, msg, *args, **kwargs):
        """Log a nivel warning."""
        self._logger.warning(msg, *args, **kwargs)
        self.emit_log_event(logging.WARNING, msg, 'core_dajarony')
    
    def warn(self, msg, *args, **kwargs):
        """Alias para warning."""
        self.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """Log a nivel error."""
        self._logger.error(msg, *args, **kwargs)
        self.emit_log_event(logging.ERROR, msg, 'core_dajarony')
    
    def critical(self, msg, *args, **kwargs):
        """Log a nivel critical."""
        self._logger.critical(msg, *args, **kwargs)
        self.emit_log_event(logging.CRITICAL, msg, 'core_dajarony')
    
    def exception(self, msg, *args, exc_info=True, **kwargs):
        """Log a nivel error con información de excepción."""
        self._logger.exception(msg, *args, exc_info=exc_info, **kwargs)
        self.emit_log_event(logging.ERROR, msg, 'core_dajarony')