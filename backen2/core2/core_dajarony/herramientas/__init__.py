"""
SUME DOCBLOCK

Nombre: Módulo de Herramientas Core Dajarony
Tipo: Paquete

Entradas:
- Solicitudes de acceso a herramientas de desarrollo

Acciones:
- Exponer herramientas de desarrollo y utilidades
- Proporcionar acceso centralizado a funcionalidades auxiliares
- Establecer versión del paquete de herramientas

Salidas:
- Funciones y clases de utilidad
- Información de versión
"""
from core_dajarony.herramientas.doc_generator import DocGenerator, generate_documentation
from core_dajarony.herramientas.version_manager import bump_version, generate_changelog
from core_dajarony.herramientas.diagnostics_dashboard import create_dashboard

# Definir versión
__version__ = "1.0.0"

# Definir componentes públicos
__all__ = [
    # Generador de documentación
    'DocGenerator', 'generate_documentation',
    
    # Gestor de versiones
    'bump_version', 'generate_changelog',
    
    # Dashboard de diagnóstico
    'create_dashboard',
    
    # Versión
    '__version__'
]

# Información del módulo
__author__ = "Equipo Core Dajarony"
__description__ = "Herramientas de desarrollo y utilidades para Core Dajarony"