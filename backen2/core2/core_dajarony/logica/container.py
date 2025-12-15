"""
SUME DOCBLOCK

Nombre: Container
Tipo: Lógica

Entradas:
- Solicitudes de registro de servicios (nombre, instancia)
- Solicitudes de obtención de servicios (nombre)
- Configuración del sistema (ruta de archivo)

Acciones:
- Registrar servicios e instancias
- Mantener un registro único de servicios disponibles
- Resolver dependencias entre servicios
- Proporcionar acceso a servicios mediante nombre
- Inicializar componentes principales del sistema
- Gestionar ciclo de vida de los servicios

Salidas:
- Instancias de servicios solicitados
- Estado actual del contenedor (diagnóstico)
- Registro de dependencias resueltas
"""
import logging
import asyncio
import yaml
from typing import Dict, Any, Optional, List, Set, Callable
from pathlib import Path


class Container:
    """Contenedor de inyección de dependencias para el sistema SUME."""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._initializing: Set[str] = set()  # Para detectar dependencias circulares
        self._initialized: Set[str] = set()
        self._logger = logging.getLogger(__name__)

    def register(self, name: str, instance: Any) -> None:
        """
        Registra un servicio en el contenedor.

        Args:
            name: Nombre único del servicio
            instance: Instancia del servicio a registrar
        """
        if name in self._services:
            self._logger.warning(f"Servicio '{name}' ya registrado, será sobrescrito")
        
        self._services[name] = instance
        self._logger.debug(f"Servicio '{name}' registrado: {type(instance).__name__}")

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Registra una fábrica que creará el servicio bajo demanda.

        Args:
            name: Nombre único del servicio
            factory: Función que crea una instancia del servicio
        """
        self._factories[name] = factory
        self._logger.debug(f"Fábrica para '{name}' registrada")

    def get(self, name: str) -> Any:
        """
        Obtiene un servicio del contenedor. Si no existe pero hay una fábrica
        registrada, lo crea.

        Args:
            name: Nombre del servicio a obtener

        Returns:
            Instancia del servicio solicitado

        Raises:
            KeyError: Si el servicio no está registrado ni tiene fábrica
            RuntimeError: Si se detecta una dependencia circular
        """
        # Si ya existe el servicio, devolverlo directamente
        if name in self._services:
            return self._services[name]
        
        # Si no existe pero hay una fábrica registrada, crearlo
        if name in self._factories:
            # Detectar dependencias circulares
            if name in self._initializing:
                path = " -> ".join(self._initializing) + f" -> {name}"
                raise RuntimeError(f"Dependencia circular detectada: {path}")
            
            self._initializing.add(name)
            try:
                instance = self._factories[name]()
                self.register(name, instance)
                self._initializing.remove(name)
                self._initialized.add(name)
                return instance
            except Exception as e:
                self._initializing.remove(name)
                self._logger.error(f"Error al crear servicio '{name}': {str(e)}")
                raise
        
        # Si no existe ni hay fábrica, lanzar excepción
        raise KeyError(f"Servicio '{name}' no registrado en el contenedor")

    def has(self, name: str) -> bool:
        """
        Verifica si un servicio está registrado o tiene fábrica.

        Args:
            name: Nombre del servicio a verificar

        Returns:
            True si el servicio está disponible, False en caso contrario
        """
        return name in self._services or name in self._factories

    def get_all_services(self) -> List[str]:
        """
        Obtiene la lista de todos los servicios disponibles.

        Returns:
            Lista de nombres de servicios registrados o con fábrica
        """
        # Unir conjuntos de claves sin duplicados
        return list(set(self._services.keys()) | set(self._factories.keys()))

    def get_container_state(self) -> Dict[str, Any]:
        """
        Retorna el estado actual del contenedor para diagnóstico.

        Returns:
            Diccionario con información de estado
        """
        return {
            'registered_services': list(self._services.keys()),
            'registered_factories': list(self._factories.keys()),
            'initialized_services': list(self._initialized),
            'initializing': list(self._initializing)
        }


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Carga la configuración del sistema desde un archivo YAML.

    Args:
        config_path: Ruta al archivo de configuración. Si es None, 
                    se usa la configuración por defecto.

    Returns:
        Diccionario con la configuración cargada
    """
    default_config = {
        'logging': {
            'level': 'info',
            'file': None,
        },
        'system': {
            'name': 'core_dajarony',
            'version': '1.0.0',
        }
    }
    
    if not config_path:
        return default_config
    
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            logging.warning(f"Archivo de configuración {config_path} no encontrado, usando valores por defecto")
            return default_config
        
        with open(config_file, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f)
            
        # Combinar configuraciones (la del usuario tiene prioridad)
        merged_config = default_config.copy()
        for section, values in user_config.items():
            if section in merged_config and isinstance(merged_config[section], dict):
                merged_config[section].update(values)
            else:
                merged_config[section] = values
                
        return merged_config
    except Exception as e:
        logging.error(f"Error al cargar configuración: {str(e)}")
        return default_config


def setup_logging(log_file: Optional[str], log_level: str) -> logging.Logger:
    """
    Configura el sistema de logging.

    Args:
        log_file: Ruta al archivo de log. Si es None, se usa solo consola.
        log_level: Nivel de log (debug, info, warning, error)

    Returns:
        Logger configurado
    """
    levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'warn': logging.WARNING,
        'error': logging.ERROR,
    }
    level = levels.get(log_level.lower(), logging.INFO)
    
    # Configuración básica
    log_config = {
        'level': level,
        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    }
    
    if log_file:
        log_config['filename'] = log_file
        log_config['filemode'] = 'a'
    
    logging.basicConfig(**log_config)
    logger = logging.getLogger("core_dajarony")
    
    # Si se especificó archivo pero también queremos output en consola
    if log_file:
        console = logging.StreamHandler()
        console.setLevel(level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        console.setFormatter(formatter)
        logger.addHandler(console)
    
    logger.info(f"Sistema de logging inicializado (nivel: {log_level})")
    return logger


def create_container(config_path: Optional[str] = None, 
                     log_file: Optional[str] = None, 
                     log_level: str = "info") -> Container:
    """
    Crea e inicializa el contenedor con los servicios principales.

    Args:
        config_path: Ruta al archivo de configuración
        log_file: Ruta al archivo de log
        log_level: Nivel de log

    Returns:
        Contenedor inicializado con servicios básicos
    """
    # Crear contenedor
    container = Container()
    
    # Cargar configuración
    config = load_config(config_path)
    container.register("config", config)
    
    # Si hay configuración personalizada de logs, usarla
    if log_file is None and "logging" in config:
        log_file = config["logging"].get("file")
    
    if log_level == "info" and "logging" in config:
        log_level = config["logging"].get("level", "info")
    
    # Configurar logging
    logger = setup_logging(log_file, log_level)
    container.register("logger", logger)
    
    # Registrar el propio contenedor para que sea accesible
    container.register("container", container)
    
    logger.info("Contenedor básico creado e inicializado")
    
    return container


async def start_core(container: Container) -> None:
    """
    Inicia los servicios principales del sistema de forma asíncrona.

    Args:
        container: Contenedor con los servicios registrados
    """
    logger = container.get("logger")
    logger.info("Iniciando servicios principales del sistema...")
    
    # Obtener el core_manager debería iniciarlo automáticamente
    core_manager = container.get("core_manager")
    
    # Iniciar el core
    await core_manager.start()
    
    try:
        # Mantener el sistema en ejecución hasta que se interrumpa
        logger.info("Sistema iniciado correctamente, en ejecución...")
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Tarea de inicio cancelada, deteniendo el sistema...")
        await core_manager.stop()
    
    logger.info("Sistema detenido correctamente")


# Función para pruebas rápidas del módulo
if __name__ == "__main__":
    container = create_container()
    print("Servicios disponibles:", container.get_all_services())
    print("Estado del contenedor:", container.get_container_state())