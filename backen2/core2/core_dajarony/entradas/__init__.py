# core_dajarony/entradas/__init__.py
"""
SUME DOCBLOCK

Nombre: Módulo de Entradas Core Dajarony
Tipo: Paquete

Entradas:
- Importaciones de módulos de entrada

Acciones:
- Exponer componentes de entrada del sistema
- Proporcionar acceso centralizado a puntos de entrada

Salidas:
- Módulos disponibles para importación
"""

from .main import main
from .health_endpoints import HealthEndpoints

__all__ = [
    'main',
    'HealthEndpoints'
]

__version__ = "1.0.0"
__author__ = "Core Dajarony Team"