# core_dajarony/salidas/__init__.py
"""
SUME DOCBLOCK

Nombre: Módulo de Salidas Core Dajarony
Tipo: Paquete

Entradas:
- Importaciones de módulos de salida

Acciones:
- Exponer componentes de salida del sistema
- Proporcionar acceso centralizado a funcionalidades de salida

Salidas:
- Módulos disponibles para importación
"""

from .output_handler import OutputHandler
from .metrics_exporter import MetricsExporter

__all__ = [
    'OutputHandler',
    'MetricsExporter'
]

__version__ = "1.0.0"
__author__ = "Core Dajarony Team"