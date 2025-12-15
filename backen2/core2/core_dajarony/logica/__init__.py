# -*- coding: utf-8 -*-
"""
SUME DOCBLOCK

Nombre: Módulo de Lógica Core Dajarony
Tipo: Paquete / Interfaz

Entradas:
- Solicitudes de importación de componentes lógicos desde otros módulos (ej: `from core_dajarony.logica import Container`).
- Argumentos opcionales para la función `create_core_services` (`config_path`, `log_file`, `log_level`).

Acciones:
- Importa las clases y funciones principales de los sub-módulos de la capa lógica (`Container`, `EventBus`, `Store`, `SumeLogger`, `Config`, `Validator`, etc.).
- Define la interfaz pública del paquete `logica` a través de `__all__`.
- Establece metadatos del paquete (`__version__`, `__author__`, `__description__`).
- Proporciona una función de fábrica (`create_core_services`) para instanciar, configurar y registrar los servicios lógicos básicos dentro de un contenedor de forma conveniente y ordenada.

Salidas:
- Expone los componentes lógicos listados en `__all__` para ser importados y utilizados por otras partes del sistema.
- Expone la variable `__version__`.
- Expone la función `create_core_services` que devuelve una instancia del `Container` con los servicios lógicos básicos inicializados y registrados.
"""

# Importar componentes desde los sub-módulos de la capa lógica
# Asegúrate de que estas rutas coincidan con tu estructura de proyecto real
from typing import Optional
from .container import Container, create_container
from .event_bus import EventBus
from .store import Store
from .logger import SumeLogger
from .config import Config
from .validator import Validator, ValidationRule, DataType, ValidationError
from .interaction_manager import InteractionManager, SecurityContext, PermissionLevel
from .core_manager import CoreManager, SystemState
from .telemetry_collector import TelemetryCollector, AlertType, AlertSeverity
from .version_manager import VersionManager, VersionInfo, ChangeType
from .circuit_breaker import CircuitBreaker

# Definir versión del paquete de lógica
__version__ = "1.0.0"

# Definir explícitamente la API pública del paquete
__all__ = [
    # --- Componentes Principales ---
    'Container',                # Clase base del contenedor de servicios
    'create_container',         # Función fábrica para crear contenedor básico (logger, config)
    'EventBus',                 # Gestor central de eventos
    'Store',                    # Almacén de datos clave-valor (con persistencia opcional)
    'SumeLogger',               # Implementación del logger estandarizado
    'Config',                   # Gestor de configuración
    'Validator',                # Validador de datos basado en reglas
    'ValidationRule',           # Clase para definir reglas de validación
    'DataType',                 # Enum para tipos de datos en validación
    'ValidationError',          # Excepción para errores de validación
    'InteractionManager',       # Gestor de interacciones y seguridad
    'SecurityContext',          # Contexto de seguridad para interacciones
    'PermissionLevel',          # Enum para niveles de permiso
    'CoreManager',              # Gestor del ciclo de vida de módulos/core (si aplica)
    'SystemState',              # Enum para estados del sistema
    'TelemetryCollector',       # Colector de telemetría y alertas
    'AlertType',                # Enum para tipos de alerta
    'AlertSeverity',            # Enum para severidad de alerta
    'VersionManager',           # Gestor de versiones y cambios
    'VersionInfo',              # Información de versión
    'ChangeType',               # Enum para tipos de cambio
    'CircuitBreaker',           # Patrón Circuit Breaker para servicios externos

    # --- Metadatos ---
    '__version__'               # Versión del paquete
]

# ------------------------------------------------- #
# UAF - CREATE_CORE_SERVICES - Fábrica de Servicios Lógicos Básicos
# ------------------------------------------------- #
def create_core_services(config_path: Optional[str] = None,
                         log_file: Optional[str] = None,
                         log_level: str = "info") -> Container:
    """
    Crea e inicializa los servicios lógicos principales del sistema Core Dajarony.

    Esta función actúa como un ensamblador conveniente para la infraestructura
    básica, asegurando que los componentes se creen y registren en el
    orden correcto con sus dependencias iniciales.

    Args:
        config_path: Ruta opcional al archivo de configuración principal.
        log_file: Ruta opcional al archivo donde escribir los logs.
        log_level: Nivel mínimo de log a registrar (debug, info, warning, error).

    Returns:
        Una instancia del Container con los servicios básicos registrados.
        (Nota: Los servicios registrados aquí aún pueden necesitar su propio
         método init() si tienen lógica de inicialización adicional).
    """
    # 1. Crear contenedor base (ya incluye logger y config)
    container = create_container(config_path, log_file, log_level)
    logger = container.get("logger") # Logger ya está disponible

    logger.info(f"Creando servicios core v{__version__}...")

    # 2. Crear y registrar EventBus (depende de logger)
    event_bus = EventBus(logger)
    container.register("event_bus", event_bus, {'priority': 0}) # Prioridad alta

    # 3. Crear y registrar Store (depende de event_bus, logger, config)
    config = container.get("config") # Config ya está disponible
    persist_dir = config.get("system.store.persist_dir", "./.sume_store") # Ejemplo de clave config
    store = Store(event_bus, logger, persist_dir)
    container.register("store", store, {'priority': 1, 'dependencies': ['event_bus', 'logger', 'config']})

    # 4. Crear y registrar Validator (depende de logger)
    validator = Validator(logger)
    container.register("validator", validator, {'priority': 1, 'dependencies': ['logger']})

    # 5. Crear y registrar TelemetryCollector (depende de event_bus, store, logger, config)
    telemetry = TelemetryCollector(event_bus, store, logger, config)
    container.register("telemetry_collector", telemetry, {'priority': 2, 'dependencies': ['event_bus', 'store', 'logger', 'config']})

    # 6. Crear y registrar VersionManager (depende de event_bus, store, logger)
    version_manager = VersionManager(event_bus, store, logger)
    container.register("version_manager", version_manager, {'priority': 2, 'dependencies': ['event_bus', 'store', 'logger']})

    # 7. Crear y registrar CircuitBreaker (depende de event_bus, store, logger)
    circuit_breaker = CircuitBreaker(event_bus, store, logger)
    container.register("circuit_breaker", circuit_breaker, {'priority': 2, 'dependencies': ['event_bus', 'store', 'logger']})

    # 8. Crear y registrar InteractionManager (depende de event_bus, store, logger, circuit_breaker)
    interaction_manager = InteractionManager(event_bus, store, logger, circuit_breaker)
    container.register("interaction_manager", interaction_manager, {'priority': 3, 'dependencies': ['event_bus', 'store', 'logger', 'circuit_breaker']})

    # 9. Crear y registrar CoreManager (depende del propio container)
    # Nota: CoreManager podría tener una inicialización más compleja o realizarla él mismo
    core_manager = CoreManager(container) # Pasa el contenedor completo
    container.register("core_manager", core_manager, {'priority': 10}) # Prioridad baja, se inicializa al final

    logger.info(f"Servicios lógicos básicos registrados en el contenedor.")

    # Nota: Esta función solo REGISTRA los servicios.
    # Todavía es necesario llamar a container.init() externamente
    # para que se resuelvan las dependencias y se llamen los métodos init() de cada servicio.
    return container


# Información adicional del módulo
__author__ = "Equipo Core Dajarony"
__description__ = "Módulo centralizado para los componentes lógicos del sistema Core Dajarony (SUME)."
__email__ = "core-dev@dajarony.com" # Ejemplo
__status__ = "Development"