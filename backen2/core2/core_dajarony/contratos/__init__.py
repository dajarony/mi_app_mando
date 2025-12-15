# core_dajarony/contratos/__init__.py
"""
SUME DOCBLOCK

Nombre: Módulo de Contratos Core Dajarony
Tipo: Paquete

Entradas:
- Importaciones de tipos y modelos

Acciones:
- Exponer interfaces y tipos del sistema
- Proporcionar acceso a definiciones de seguridad

Salidas:
- Tipos disponibles para importación
"""

from .types import (
    ComponentType,
    ComponentStatus,
    EventMetadata,
    ModuleMetadata,
    ValidationResult,
    CircuitBreakerState,
    LogLevel,
    ContractVersion
)

from .security import (
    PermissionLevel,
    SecurityContext,
    Credential,
    SecurityPolicy,
    AccessControl
)

__all__ = [
    # Types
    'ComponentType',
    'ComponentStatus',
    'EventMetadata',
    'ModuleMetadata',
    'ValidationResult',
    'CircuitBreakerState',
    'LogLevel',
    'ContractVersion',
    
    # Security
    'PermissionLevel',
    'SecurityContext',
    'Credential',
    'SecurityPolicy',
    'AccessControl'
]

__version__ = "1.0.0"
__author__ = "Core Dajarony Team"