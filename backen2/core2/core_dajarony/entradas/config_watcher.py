"""
SUME DOCBLOCK
Nombre: Config Watcher
Tipo: Entrada

Entradas:
- Archivo config.yml
Acciones:
- Recarga y valida la configuración en caliente
Salidas:
- Actualiza servicio 'config' en el contenedor
"""

import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Any, Dict

class _ReloadHandler(FileSystemEventHandler):
    def __init__(self, container):
        self._container = container

    def on_modified(self, event):
        if event.src_path.endswith("config.yml"):
            cfg: Dict[str, Any] = yaml.safe_load(open(event.src_path))
            self._container.register("config", cfg)
            print("Configuración recargada:", cfg)

def _reload_config_now(path: str, container):
    """Recarga la configuración inmediatamente sin esperar cambios en el archivo."""
    try:
        with open(path, 'r') as f:
            cfg: Dict[str, Any] = yaml.safe_load(f)
        container.register("config", cfg)
        print("Configuración recargada forzadamente:", cfg)
    except Exception as e:
        print(f"Error al recargar configuración: {e}")

def start_config_watcher(path: str, container, force_reload: bool = False) -> None:
    """
    Inicia watchdog en 'path' para recarga en caliente.
    
    Args:
        path: Ruta al archivo de configuración
        container: Contenedor de dependencias
        force_reload: Si es True, recarga la configuración inmediatamente
    """
    # Si se solicita recarga forzada, hacerla primero
    if force_reload:
        _reload_config_now(path, container)
    
    # Configurar el watcher para cambios futuros
    handler = _ReloadHandler(container)
    obs = Observer()
    obs.schedule(handler, ".", recursive=False)
    obs.daemon = True
    obs.start()