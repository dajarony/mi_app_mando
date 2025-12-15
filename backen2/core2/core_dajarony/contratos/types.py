# core_dajarony/contratos/types.py
"""
SUME DOCBLOCK

Nombre: Definiciones de Tipos Core
Tipo: Contrato

Entradas:
- N/A (definiciones de tipos)

Acciones:
- Definir estructuras de datos del sistema
- Establecer enumeraciones y constantes
- Proporcionar tipos para validación
- Mantener compatibilidad de interfaces

Salidas:
- Tipos y estructuras de datos
- Enumeraciones del sistema
- Constantes globales
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from datetime import datetime

class ComponentType(Enum):
    """Tipos de componentes en el sistema SUME."""
    ENTRADA = "entrada"
    LOGICA = "logica"
    SALIDA = "salida"
    CONTRATO = "contrato"
    HERRAMIENTA = "herramienta"

class ComponentStatus(Enum):
    """Estados posibles de un componente."""
    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DEGRADED = "degraded"

class LogLevel(Enum):
    """Niveles de logging del sistema."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class CircuitBreakerState(Enum):
    """Estados del circuit breaker."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class EventMetadata:
    """Metadata para eventos del sistema."""
    event_id: str
    timestamp: datetime
    source: str
    destination: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: int = 0
    ttl: Optional[int] = None  # Time to live in seconds
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la metadata a diccionario."""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'destination': self.destination,
            'correlation_id': self.correlation_id,
            'priority': self.priority,
            'ttl': self.ttl,
            'retry_count': self.retry_count
        }

@dataclass
class ModuleMetadata:
    """Metadata para módulos del sistema."""
    name: str
    version: str
    type: ComponentType
    dependencies: List[str]
    status: ComponentStatus = ComponentStatus.UNKNOWN
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None
    description: Optional[str] = None
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la metadata a diccionario."""
        return {
            'name': self.name,
            'version': self.version,
            'type': self.type.value,
            'dependencies': self.dependencies,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'description': self.description,
            'author': self.author
        }

@dataclass
class ValidationResult:
    """Resultado de una validación."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Optional[Dict[str, Any]] = None
    
    def is_valid(self) -> bool:
        """Verifica si el resultado es válido."""
        return self.valid and not self.errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata
        }

@dataclass
class ContractVersion:
    """Información de versión de un contrato."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    
    def __str__(self) -> str:
        """Representación en formato string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    @classmethod
    def from_string(cls, version_string: str) -> 'ContractVersion':
        """Crea una versión a partir de un string."""
        import re
        pattern = r'^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        match = re.match(pattern, version_string)
        if not match:
            raise ValueError(f"Invalid version string: {version_string}")
        
        return cls(
            major=int(match.group('major')),
            minor=int(match.group('minor')),
            patch=int(match.group('patch')),
            prerelease=match.group('prerelease'),
            build=match.group('build')
        )
    
    def is_compatible_with(self, other: 'ContractVersion') -> bool:
        """Verifica si esta versión es compatible con otra."""
        # Compatibilidad basada en semver
        if self.major != other.major:
            return False
        if self.minor < other.minor:
            return False
        return True

# Constantes globales del sistema
DEFAULT_TIMEOUT = 30  # segundos
MAX_RETRY_ATTEMPTS = 3
DEFAULT_BUFFER_SIZE = 1000
DEFAULT_BATCH_SIZE = 100
MAX_EVENT_AGE = 3600  # segundos
METRIC_AGGREGATION_INTERVAL = 60  # segundos
DEFAULT_LOG_LEVEL = LogLevel.INFO