# core_dajarony/contratos/security.py
"""
SUME DOCBLOCK

Nombre: Contratos de Seguridad
Tipo: Contrato

Entradas:
- N/A (definiciones de seguridad)

Acciones:
- Definir niveles de permisos
- Establecer estructuras de seguridad
- Proporcionar contextos de autenticación
- Mantener políticas de acceso

Salidas:
- Tipos de seguridad
- Modelos de autenticación
- Interfaces de autorización
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from datetime import datetime, timedelta

class PermissionLevel(Enum):
    """Niveles de permiso en el sistema."""
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3
    SUPER_ADMIN = 4

class AccessType(Enum):
    """Tipos de acceso para recursos."""
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    RESTRICTED = "restricted"

@dataclass
class Credential:
    """Credencial de autenticación."""
    identifier: str
    secret: str
    type: str = "basic"
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def is_expired(self) -> bool:
        """Verifica si la credencial ha expirado."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la credencial a diccionario (omitiendo el secreto)."""
        return {
            'identifier': self.identifier,
            'type': self.type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.metadata
        }

@dataclass
class SecurityContext:
    """Contexto de seguridad para una operación."""
    principal: str
    level: PermissionLevel
    roles: Set[str]
    attributes: Dict[str, Any]
    created_at: datetime = datetime.utcnow()
    expires_at: Optional[datetime] = None
    parent_context: Optional['SecurityContext'] = None
    
    def has_permission(self, required_level: PermissionLevel) -> bool:
        """Verifica si tiene el nivel de permiso requerido."""
        return self.level.value >= required_level.value
    
    def has_role(self, role: str) -> bool:
        """Verifica si tiene el rol especificado."""
        return role in self.roles
    
    def is_expired(self) -> bool:
        """Verifica si el contexto ha expirado."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def derive_context(self, scope_reduction: Optional[PermissionLevel] = None,
                      additional_attributes: Optional[Dict[str, Any]] = None) -> 'SecurityContext':
        """Crea un contexto derivado con permisos reducidos."""
        new_level = min(self.level, scope_reduction) if scope_reduction else self.level
        new_attributes = self.attributes.copy()
        if additional_attributes:
            new_attributes.update(additional_attributes)
        
        return SecurityContext(
            principal=self.principal,
            level=new_level,
            roles=self.roles.copy(),
            attributes=new_attributes,
            created_at=datetime.utcnow(),
            expires_at=self.expires_at,
            parent_context=self
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el contexto a diccionario."""
        return {
            'principal': self.principal,
            'level': self.level.name,
            'roles': list(self.roles),
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired()
        }

@dataclass
class SecurityPolicy:
    """Política de seguridad para recursos."""
    resource_id: str
    access_type: AccessType
    required_level: PermissionLevel
    allowed_roles: Set[str]
    conditions: Dict[str, Any]
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None
    
    def evaluate(self, context: SecurityContext) -> bool:
        """Evalúa si un contexto de seguridad satisface esta política."""
        # Verificar nivel de permiso
        if not context.has_permission(self.required_level):
            return False
        
        # Verificar roles si hay alguno definido
        if self.allowed_roles and not any(context.has_role(role) for role in self.allowed_roles):
            return False
        
        # Verificar condiciones adicionales
        for condition_key, condition_value in self.conditions.items():
            if condition_key not in context.attributes:
                return False
            if context.attributes[condition_key] != condition_value:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la política a diccionario."""
        return {
            'resource_id': self.resource_id,
            'access_type': self.access_type.value,
            'required_level': self.required_level.name,
            'allowed_roles': list(self.allowed_roles),
            'conditions': self.conditions,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AccessControl:
    """Control de acceso basado en políticas."""
    
    def __init__(self):
        self.policies: Dict[str, SecurityPolicy] = {}
        self.default_policy = SecurityPolicy(
            resource_id="*",
            access_type=AccessType.INTERNAL,
            required_level=PermissionLevel.READ,
            allowed_roles=set(),
            conditions={}
        )
    
    def add_policy(self, policy: SecurityPolicy) -> None:
        """Agrega una política de seguridad."""
        self.policies[policy.resource_id] = policy
    
    def remove_policy(self, resource_id: str) -> None:
        """Elimina una política de seguridad."""
        if resource_id in self.policies:
            del self.policies[resource_id]
    
    def check_access(self, resource_id: str, context: SecurityContext) -> bool:
        """Verifica el acceso a un recurso."""
        # Verificar si el contexto ha expirado
        if context.is_expired():
            return False
        
        # Buscar política específica para el recurso
        policy = self.policies.get(resource_id, self.default_policy)
        
        # Evaluar la política
        return policy.evaluate(context)
    
    def get_accessible_resources(self, context: SecurityContext) -> List[str]:
        """Obtiene la lista de recursos accesibles para un contexto dado."""
        accessible = []
        for resource_id, policy in self.policies.items():
            if policy.evaluate(context):
                accessible.append(resource_id)
        return accessible