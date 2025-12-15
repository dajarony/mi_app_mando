"""
SUME DOCBLOCK

Nombre: Punto de Entrada Principal
Tipo: Entrada

Entradas:
- Argumentos de línea de comandos
- Variables de entorno
- Archivo de configuración inicial
- Señales del sistema operativo

Acciones:
- Parsear argumentos y configuración
- Inicializar el contenedor de dependencias
- Configurar y registrar servicios principales
- Iniciar el CoreManager
- Manejar señales para cierre limpio
- Mantener el bucle principal

Salidas:
- Sistema completamente inicializado y funcionando
- Logs de estado durante el arranque
- Código de salida al terminar la ejecución
"""
import os
import sys
import signal
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).parent.parent))

from logica import create_core_services, Container

class SystemBootstrapper:
    """Clase encargada de inicializar y arrancar todo el sistema."""
    
    def __init__(self, container: Container):
        self.container = container
        self.running = False
        self.shutdown_event = asyncio.Event()
        
    async def start(self):
        """Inicia el sistema completo."""
        try:
            # Obtener servicios del container
            logger = self.container.get("logger")
            event_bus = self.container.get("event_bus")
            core_manager = self.container.get("core_manager")
            
            logger.info("Iniciando sistema Core Dajarony...")
            
            # Emitir evento de inicio
            event_bus.emit("system:starting", {"timestamp": datetime.utcnow().isoformat()})
            
            # Iniciar CoreManager
            await core_manager.start()
            self.running = True
            
            logger.info("Sistema arrancado exitosamente.")
            event_bus.emit("system:started", {"timestamp": datetime.utcnow().isoformat()})
            
            # Mantener el sistema en ejecución
            await self.run_forever()
            
        except Exception as e:
            logger = self.container.get("logger", None)
            if logger:
                logger.critical(f"Error crítico durante el arranque: {e}")
            else:
                print(f"Error crítico durante el arranque: {e}")
            sys.exit(1)
    
    async def run_forever(self):
        """Mantiene el sistema en ejecución hasta recibir señal de cierre."""
        try:
            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            pass
    
    async def stop(self):
        """Detiene el sistema de forma controlada."""
        logger = self.container.get("logger")
        event_bus = self.container.get("event_bus")
        core_manager = self.container.get("core_manager")
        
        logger.info("Iniciando cierre controlado del sistema...")
        event_bus.emit("system:stopping", {"timestamp": datetime.utcnow().isoformat()})
        
        # Detener CoreManager
        await core_manager.stop()
        
        self.running = False
        self.shutdown_event.set()
        
        logger.info("Sistema detenido exitosamente.")
        event_bus.emit("system:stopped", {"timestamp": datetime.utcnow().isoformat()})


class GracefulKiller:
    """Manejador de señales para cierre limpio del sistema."""
    
    def __init__(self, bootstrapper: SystemBootstrapper):
        self.bootstrapper = bootstrapper
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
    
    def exit_gracefully(self, signum, frame):
        """Maneja las señales para un cierre limpio."""
        print(f"\nRecibida señal {signum}. Iniciando cierre limpio...")
        asyncio.create_task(self.bootstrapper.stop())


def parse_arguments() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Core Dajarony - Sistema Universal de Modularización Estratégica'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Ruta al archivo de configuración. Si no se especifica, se buscará config.yaml en el directorio actual.'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='info',
        help='Nivel de logging (default: info)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Ruta al archivo de log. Si no se especifica, se logueará solo a consola.'
    )
    
    parser.add_argument(
        '--metrics-export',
        action='store_true',
        help='Habilitar exportación de métricas'
    )
    
    parser.add_argument(
        '--health-port',
        type=int,
        default=8080,
        help='Puerto para los endpoints de health check (default: 8080)'
    )
    
    return parser.parse_args()


def setup_environment():
    """Configura variables de entorno necesarias."""
    # Establecer variables de entorno por defecto si no están definidas
    os.environ.setdefault('CORE_DAJARONY_ENV', 'production')
    os.environ.setdefault('CORE_DAJARONY_BASE_PATH', str(Path(__file__).parent.parent))


async def main():
    """Función principal que arranca todo el sistema."""
    # Parsear argumentos
    args = parse_arguments()
    
    # Configurar entorno
    setup_environment()
    
    # Determinar ruta de configuración
    config_path = args.config
    if not config_path:
        default_config = Path(__file__).parent.parent / "config.yaml"
        if default_config.exists():
            config_path = str(default_config)
    
    # Crear servicios principales usando la función helper
    try:
        container, core_services = create_core_services(
            config_path=config_path,
            log_file=args.log_file,
            log_level=args.log_level
        )
    except Exception as e:
        print(f"Error inicializando servicios principales: {e}")
        sys.exit(1)
    
    # Configuraciones adicionales basadas en argumentos
    if args.metrics_export:
        telemetry = container.get("telemetry_collector")
        # Aquí se configurarían las exportaciones de métricas cuando implementemos el MetricsExporter
    
    # Inicializar el sistema
    bootstrapper = SystemBootstrapper(container)
    
    # Configurar manejo de señales para cierre limpio
    killer = GracefulKiller(bootstrapper)
    
    # Arrancar el sistema
    await bootstrapper.start()


if __name__ == "__main__":
    """Punto de entrada del programa."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSistema detenido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)