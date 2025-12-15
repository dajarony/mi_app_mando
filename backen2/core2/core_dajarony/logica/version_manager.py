"""
SUME DOCBLOCK

Nombre: Version Manager
Tipo: Lógica

Entradas:
- Declaraciones de versiones de componentes
- Reglas de compatibilidad
- Mapeos de migración de formatos
- Historial de versiones disponibles
- Especificaciones de APIs/interfaces

Acciones:
- Registrar versiones de componentes y sus APIs
- Verificar compatibilidad entre componentes
- Realizar conversiones entre versiones de datos
- Mantener registro histórico de cambios
- Emitir advertencias sobre incompatibilidades
- Migrar automáticamente datos entre versiones
- Proveer información de breaking changes
- Resolver conflictos de versiones

Salidas:
- Verificaciones de compatibilidad (éxito/conflicto)
- Datos convertidos entre versiones
- Registro de versiones cargadas en el sistema
- Eventos de cambios de versión
- Notificaciones de compatibilidad
- Metadatos de APIs disponibles
"""
import re
import logging
import copy
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple, Callable, Union
import semver
from dataclasses import dataclass


class ChangeType(Enum):
    """Tipos de cambios en versiones."""
    PATCH = "patch"          # Cambios compatibles hacia atrás (correcciones)
    MINOR = "minor"          # Cambios compatibles hacia atrás (adiciones)
    MAJOR = "major"          # Cambios no compatibles hacia atrás
    BREAKING = "breaking"    # Cambios que requieren migración explícita


@dataclass
class VersionInfo:
    """Información de una versión de componente."""
    component: str           # Nombre del componente
    version: str             # Versión SemVer (X.Y.Z)
    released_at: datetime    # Fecha de liberación
    api_spec: Dict[str, Any] # Especificación de API
    changes: List[Dict[str, Any]]  # Lista de cambios en esta versión
    dependencies: Dict[str, str]   # Dependencias con versiones requeridas
    mappings: Dict[str, Callable]  # Funciones de conversión para migración
    metadata: Dict[str, Any] # Metadatos adicionales


class VersionConflict(Exception):
    """Excepción para conflictos de versión."""
    
    def __init__(self, message: str, component: str, required_version: str, available_version: str):
        """
        Inicializa un error de conflicto de versiones.
        
        Args:
            message: Mensaje de error
            component: Componente afectado
            required_version: Versión requerida
            available_version: Versión disponible
        """
        super().__init__(message)
        self.component = component
        self.required_version = required_version
        self.available_version = available_version


class VersionManager:
    """
    Gestor de versiones para componentes del sistema.
    
    Proporciona herramientas para manejar la compatibilidad entre diferentes
    versiones de APIs y componentes, así como migración de datos.
    """
    
    def __init__(self, event_bus=None, store=None, logger=None):
        """
        Inicializa el gestor de versiones.
        
        Args:
            event_bus: EventBus para emitir eventos (opcional)
            store: Store para almacenamiento persistente (opcional)
            logger: Logger para registro de actividad (opcional)
        """
        self.event_bus = event_bus
        self.store = store
        self.logger = logger or logging.getLogger(__name__)
        
        # Registro de versiones por componente
        self._versions: Dict[str, Dict[str, VersionInfo]] = {}
        
        # Versiones actualmente en uso
        self._active_versions: Dict[str, str] = {}
        
        # Matriz de compatibilidad en caché
        self._compatibility_cache: Dict[str, Dict[str, bool]] = {}
        
        # Historial de cambios de versión
        self._version_history: List[Dict[str, Any]] = []
        
        # Inicializar
        self._initialize()
        
        self.logger.debug("VersionManager inicializado")
    
    def _initialize(self):
        """Inicializa el gestor de versiones con datos persistentes."""
        # Cargar datos desde el store si está disponible
        if self.store and self.store.has("version_manager.active_versions"):
            stored_versions = self.store.get("version_manager.active_versions")
            if stored_versions:
                self._active_versions = stored_versions
                self.logger.debug(f"Cargadas {len(self._active_versions)} versiones activas desde el store")
        
        # Cargar historial si está disponible
        if self.store and self.store.has("version_manager.history"):
            stored_history = self.store.get("version_manager.history")
            if stored_history:
                self._version_history = stored_history
                self.logger.debug(f"Cargado historial de versiones desde el store: {len(self._version_history)} entradas")
    
    def register_version(self, component: str, version: str, api_spec: Dict[str, Any],
                       dependencies: Dict[str, str] = None, changes: List[Dict[str, Any]] = None,
                       mappings: Dict[str, Callable] = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Registra una versión de un componente.
        
        Args:
            component: Nombre del componente
            version: Versión SemVer (X.Y.Z)
            api_spec: Especificación de la API
            dependencies: Dependencias del componente {componente: versión_requerida}
            changes: Lista de cambios en esta versión
            mappings: Funciones de conversión para migración
            metadata: Metadatos adicionales
            
        Returns:
            True si se registró correctamente
            
        Raises:
            ValueError: Si la versión no es válida
        """
        # Validar formato de versión SemVer
        try:
            semver.VersionInfo.parse(version)
        except ValueError:
            self.logger.error(f"Formato de versión inválido para {component}: {version}")
            raise ValueError(f"La versión debe seguir el formato SemVer (X.Y.Z): {version}")
        
        # Inicializar diccionario para este componente si no existe
        if component not in self._versions:
            self._versions[component] = {}
        
        # Valores por defecto
        dependencies = dependencies or {}
        changes = changes or []
        mappings = mappings or {}
        metadata = metadata or {}
        
        # Crear información de versión
        version_info = VersionInfo(
            component=component,
            version=version,
            released_at=datetime.utcnow(),
            api_spec=api_spec,
            changes=changes,
            dependencies=dependencies,
            mappings=mappings,
            metadata=metadata
        )
        
        # Registrar versión
        self._versions[component][version] = version_info
        
        # Log
        self.logger.info(f"Registrada versión {version} para componente {component}")
        
        # Establecer como versión activa si es la primera o mayor que la actual
        if component not in self._active_versions:
            self._set_active_version(component, version, "Primera versión registrada")
        else:
            current_version = self._active_versions[component]
            if semver.compare(version, current_version) > 0:
                # Es una versión más reciente
                self._set_active_version(component, version, "Actualización automática a versión mayor")
        
        # Limpiar caché de compatibilidad
        self._compatibility_cache = {}
        
        # Emitir evento
        if self.event_bus:
            self.event_bus.emit("version:registered", {
                "component": component,
                "version": version,
                "changes": changes,
                "dependencies": dependencies
            })
        
        return True
    
    def get_version(self, component: str, version: Optional[str] = None) -> Optional[VersionInfo]:
        """
        Obtiene información de una versión específica de un componente.
        
        Args:
            component: Nombre del componente
            version: Versión a consultar, None para versión activa
            
        Returns:
            Información de la versión o None si no existe
        """
        if component not in self._versions:
            return None
        
        # Si no se especifica versión, usar la activa
        if version is None:
            version = self.get_active_version(component)
            if not version:
                return None
        
        # Buscar la versión
        return self._versions[component].get(version)
    
    def get_active_version(self, component: str) -> Optional[str]:
        """
        Obtiene la versión activa de un componente.
        
        Args:
            component: Nombre del componente
            
        Returns:
            Versión activa o None si el componente no está registrado
        """
        return self._active_versions.get(component)
    
    def set_active_version(self, component: str, version: str, reason: str = "") -> bool:
        """
        Establece una versión como activa para un componente.
        
        Args:
            component: Nombre del componente
            version: Versión a activar
            reason: Razón del cambio
            
        Returns:
            True si se activó correctamente
            
        Raises:
            ValueError: Si la versión no existe
            VersionConflict: Si hay conflictos de dependencias
        """
        # Verificar que el componente y la versión existen
        if component not in self._versions:
            self.logger.error(f"Componente {component} no está registrado")
            raise ValueError(f"Componente {component} no está registrado")
        
        if version not in self._versions[component]:
            self.logger.error(f"Versión {version} no está registrada para {component}")
            raise ValueError(f"Versión {version} no está registrada para {component}")
        
        # Verificar dependencias
        conflicts = self._check_dependency_conflicts(component, version)
        if conflicts:
            conflict_str = ", ".join([f"{c}: requiere {r} pero tiene {a}" 
                                    for c, r, a in conflicts])
            self.logger.error(f"Conflictos de dependencia al activar {component} {version}: {conflict_str}")
            
            # Si hay algún conflicto, arrojamos excepción con el primero
            first_conflict = conflicts[0]
            raise VersionConflict(
                f"Conflicto de dependencia: {first_conflict[0]} requiere {first_conflict[1]} pero tiene {first_conflict[2]}",
                first_conflict[0],
                first_conflict[1],
                first_conflict[2]
            )
        
        return self._set_active_version(component, version, reason)
    
    def _set_active_version(self, component: str, version: str, reason: str) -> bool:
        """
        Implementación interna para establecer versión activa.
        
        Args:
            component: Nombre del componente
            version: Versión a activar
            reason: Razón del cambio
            
        Returns:
            True si se activó correctamente
        """
        # Obtener versión anterior
        previous_version = self._active_versions.get(component)
        
        # Establecer nueva versión
        self._active_versions[component] = version
        
        # Guardar en el store si está disponible
        if self.store:
            self.store.set("version_manager.active_versions", self._active_versions)
        
        # Registrar en historial
        history_entry = {
            "component": component,
            "from_version": previous_version,
            "to_version": version,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        }
        self._version_history.append(history_entry)
        
        # Guardar historial si hay store
        if self.store:
            self.store.set("version_manager.history", self._version_history)
        
        # Emitir evento
        if self.event_bus:
            self.event_bus.emit("version:activated", {
                "component": component,
                "version": version,
                "previous_version": previous_version,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Limpiar caché de compatibilidad
        self._compatibility_cache = {}
        
        self.logger.info(f"Versión {version} activada para componente {component} ({reason})")
        return True
    
    def _check_dependency_conflicts(self, component: str, version: str) -> List[Tuple[str, str, str]]:
        """
        Verifica conflictos de dependencia al activar una versión.
        
        Args:
            component: Nombre del componente
            version: Versión a activar
            
        Returns:
            Lista de conflictos (componente, versión_requerida, versión_activa)
        """
        conflicts = []
        
        # Obtener dependencias de la versión
        version_info = self._versions[component][version]
        
        # Comprobar que las dependencias requeridas estén activas y sean compatibles
        for dep_component, dep_version_req in version_info.dependencies.items():
            # Si no está activo, no es un conflicto (se puede activar después)
            if dep_component not in self._active_versions:
                continue
            
            # Verificar compatibilidad con versión activa
            active_version = self._active_versions[dep_component]
            if not self._is_version_compatible(dep_version_req, active_version):
                conflicts.append((dep_component, dep_version_req, active_version))
        
        # Comprobar que los componentes que dependen de éste sean compatibles
        active_component_version = self._active_versions.get(component)
        for other_component, versions in self._versions.items():
            # Omitir el propio componente
            if other_component == component:
                continue
            
            # Si no está activo, no es un conflicto
            if other_component not in self._active_versions:
                continue
            
            # Verificar dependencias del otro componente
            other_version = self._active_versions[other_component]
            other_version_info = self._versions[other_component][other_version]
            
            # Si el otro componente depende de éste
            if component in other_version_info.dependencies:
                required_version = other_version_info.dependencies[component]
                
                # Verificar compatibilidad con la nueva versión
                if not self._is_version_compatible(required_version, version):
                    conflicts.append((other_component, required_version, version))
        
        return conflicts
    
    def _is_version_compatible(self, required: str, available: str) -> bool:
        """
        Verifica si una versión disponible es compatible con una requerida.
        
        Args:
            required: Versión requerida (puede incluir rangos)
            available: Versión disponible
            
        Returns:
            True si es compatible
        """
        # Verificar caché
        cache_key = f"{required}:{available}"
        if cache_key in self._compatibility_cache:
            return self._compatibility_cache[cache_key]
        
        # Casos especiales
        if required == "*" or required == "any":
            return True
        
        # Lógica para diferentes formatos de versión requerida
        result = False
        
        try:
            # Versión exacta (1.2.3)
            if re.match(r'^\d+\.\d+\.\d+$', required):
                result = semver.compare(available, required) == 0
            
            # Versión mínima (>=1.2.3)
            elif required.startswith(">="):
                min_version = required[2:]
                result = semver.compare(available, min_version) >= 0
            
            # Versión máxima (<=1.2.3)
            elif required.startswith("<="):
                max_version = required[2:]
                result = semver.compare(available, max_version) <= 0
            
            # Rango entre versiones (1.2.3-2.0.0)
            elif "-" in required and not required.startswith(">") and not required.startswith("<"):
                min_version, max_version = required.split("-")
                result = (semver.compare(available, min_version) >= 0 and 
                        semver.compare(available, max_version) <= 0)
            
            # Compatibilidad con versión mayor (~1.2.3 -> compatible con 1.x.x)
            elif required.startswith("~"):
                base_version = required[1:]
                major = semver.VersionInfo.parse(base_version).major
                result = semver.VersionInfo.parse(available).major == major
            
            # Compatibilidad con versión menor (^1.2.3 -> compatible con 1.2.x)
            elif required.startswith("^"):
                base_version = required[1:]
                parsed_base = semver.VersionInfo.parse(base_version)
                parsed_available = semver.VersionInfo.parse(available)
                result = (parsed_available.major == parsed_base.major and 
                        parsed_available.minor == parsed_base.minor)
            
            # Por defecto, tratar como versión exacta
            else:
                result = semver.compare(available, required) == 0
                
        except ValueError:
            self.logger.warning(f"Formato de versión inválido: {required} o {available}")
            result = False
        
        # Guardar en caché
        self._compatibility_cache[cache_key] = result
        return result
    
    def get_api_spec(self, component: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene la especificación de API de un componente.
        
        Args:
            component: Nombre del componente
            version: Versión específica o None para versión activa
            
        Returns:
            Especificación de API o None si no existe
        """
        version_info = self.get_version(component, version)
        if not version_info:
            return None
        
        return copy.deepcopy(version_info.api_spec)
    
    def list_versions(self, component: str) -> List[str]:
        """
        Lista todas las versiones disponibles de un componente.
        
        Args:
            component: Nombre del componente
            
        Returns:
            Lista de versiones ordenadas semánticamente
        """
        if component not in self._versions:
            return []
        
        # Obtener y ordenar versiones
        versions = list(self._versions[component].keys())
        return sorted(versions, key=lambda v: semver.VersionInfo.parse(v))
    
    def list_components(self) -> List[str]:
        """
        Lista todos los componentes registrados.
        
        Returns:
            Lista de nombres de componentes
        """
        return list(self._versions.keys())
    
    def get_dependencies(self, component: str, version: Optional[str] = None) -> Dict[str, str]:
        """
        Obtiene las dependencias de un componente.
        
        Args:
            component: Nombre del componente
            version: Versión específica o None para versión activa
            
        Returns:
            Diccionario de dependencias {componente: versión_requerida}
        """
        version_info = self.get_version(component, version)
        if not version_info:
            return {}
        
        return copy.deepcopy(version_info.dependencies)
    
    def get_dependent_components(self, component: str) -> List[str]:
        """
        Obtiene los componentes que dependen de uno específico.
        
        Args:
            component: Nombre del componente
            
        Returns:
            Lista de componentes que dependen del especificado
        """
        dependents = []
        
        # Recorrer todos los componentes activos
        for other_component, version in self._active_versions.items():
            # Omitir el propio componente
            if other_component == component:
                continue
            
            # Verificar si tiene dependencia
            version_info = self._versions[other_component][version]
            if component in version_info.dependencies:
                dependents.append(other_component)
        
        return dependents
    
    def convert_data(self, component: str, data: Any, 
                    from_version: str, to_version: str) -> Any:
        """
        Convierte datos entre diferentes versiones de un componente.
        
        Args:
            component: Nombre del componente
            data: Datos a convertir
            from_version: Versión de origen
            to_version: Versión de destino
            
        Returns:
            Datos convertidos
            
        Raises:
            ValueError: Si no hay ruta de conversión disponible
        """
        # Verificar que ambas versiones existen
        if (component not in self._versions or 
            from_version not in self._versions[component] or 
            to_version not in self._versions[component]):
            raise ValueError(f"Versión no encontrada para componente {component}")
        
        # Si las versiones son iguales, no hay conversión
        if from_version == to_version:
            return copy.deepcopy(data)
        
        # Encontrar ruta de conversión
        conversion_path = self._find_conversion_path(component, from_version, to_version)
        if not conversion_path:
            raise ValueError(f"No hay ruta de conversión disponible de {from_version} a {to_version}")
        
        # Aplicar conversiones en secuencia
        current_data = copy.deepcopy(data)
        
        for i in range(len(conversion_path) - 1):
            source_version = conversion_path[i]
            target_version = conversion_path[i + 1]
            
            # Buscar función de conversión directa
            conversion_key = f"{source_version}->{target_version}"
            version_info = self._versions[component][source_version]
            
            if conversion_key in version_info.mappings:
                # Aplicar conversión
                try:
                    current_data = version_info.mappings[conversion_key](current_data)
                except Exception as e:
                    self.logger.error(f"Error en conversión {conversion_key}: {str(e)}")
                    raise ValueError(f"Error en conversión {conversion_key}: {str(e)}")
            else:
                self.logger.warning(f"No hay función de conversión para {conversion_key}, intentando conversión implícita")
                # Intentar encontrar función de conversión automática
                # (podrías implementar lógica adicional aquí si es necesario)
        
        return current_data
    
    def _find_conversion_path(self, component: str, from_version: str, to_version: str) -> List[str]:
        """
        Encuentra una ruta de conversión entre versiones.
        
        Args:
            component: Nombre del componente
            from_version: Versión de origen
            to_version: Versión de destino
            
        Returns:
            Lista de versiones que forman la ruta de conversión
        """
        # Implementación simple: ordenar todas las versiones y encontrar camino
        all_versions = self.list_versions(component)
        
        # Encontrar índices
        try:
            from_index = all_versions.index(from_version)
            to_index = all_versions.index(to_version)
        except ValueError:
            return []
        
        # Determinar dirección de conversión
        if from_index < to_index:
            # Conversión hacia adelante (a versión más reciente)
            return all_versions[from_index:to_index + 1]
        else:
            # Conversión hacia atrás (a versión anterior)
            return all_versions[to_index:from_index + 1][::-1]
    
    def register_conversion_function(self, component: str, from_version: str, 
                                   to_version: str, func: Callable) -> bool:
        """
        Registra una función de conversión entre versiones.
        
        Args:
            component: Nombre del componente
            from_version: Versión de origen
            to_version: Versión de destino
            func: Función de conversión (data -> converted_data)
            
        Returns:
            True si se registró correctamente
            
        Raises:
            ValueError: Si alguna versión no existe
        """
        # Verificar que ambas versiones existen
        if (component not in self._versions or 
            from_version not in self._versions[component]):
            raise ValueError(f"Versión {from_version} no encontrada para componente {component}")
        
        # Registrar función de conversión
        conversion_key = f"{from_version}->{to_version}"
        version_info = self._versions[component][from_version]
        version_info.mappings[conversion_key] = func
        
        self.logger.debug(f"Registrada función de conversión {conversion_key} para componente {component}")
        return True
    
    def get_version_history(self, component: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de cambios de versión.
        
        Args:
            component: Nombre del componente o None para todos
            
        Returns:
            Lista de entradas de historial
        """
        # Si no se especifica componente, devolver todo el historial
        if not component:
            return copy.deepcopy(self._version_history)
        
        # Filtrar por componente
        return [entry for entry in self._version_history if entry["component"] == component]
    
    def get_version_changes(self, component: str, from_version: str, 
                          to_version: str) -> List[Dict[str, Any]]:
        """
        Obtiene los cambios entre dos versiones.
        
        Args:
            component: Nombre del componente
            from_version: Versión de origen
            to_version: Versión de destino
            
        Returns:
            Lista de cambios
        """
        # Verificar que ambas versiones existen
        if (component not in self._versions or 
            from_version not in self._versions[component] or 
            to_version not in self._versions[component]):
            return []
        
        # Encontrar versiones intermedias
        conversion_path = self._find_conversion_path(component, from_version, to_version)
        if not conversion_path:
            return []
        
        # Recopilar cambios
        all_changes = []
        
        for version in conversion_path[1:]:  # Excluir la versión inicial
            version_info = self._versions[component][version]
            all_changes.extend(version_info.changes)
        
        return all_changes
    
    def check_system_compatibility(self) -> List[Dict[str, Any]]:
        """
        Verifica la compatibilidad de todos los componentes activos.
        
        Returns:
            Lista de conflictos
        """
        conflicts = []
        
        # Verificar cada componente activo
        for component, version in self._active_versions.items():
            # Verificar que la versión existe
            if component not in self._versions or version not in self._versions[component]:
                conflicts.append({
                    "component": component,
                    "version": version,
                    "type": "missing_version",
                    "message": f"Versión {version} no encontrada para componente {component}"
                })
                continue
            
            # Verificar dependencias
            version_info = self._versions[component][version]
            for dep_component, dep_version_req in version_info.dependencies.items():
                # Si la dependencia no está activa
                if dep_component not in self._active_versions:
                    conflicts.append({
                        "component": component,
                        "depends_on": dep_component,
                        "required_version": dep_version_req,
                        "type": "missing_dependency",
                        "message": f"{component} {version} requiere {dep_component} {dep_version_req}, pero no está activo"
                    })
                    continue
                
                # Verificar compatibilidad
                dep_active_version = self._active_versions[dep_component]
                if not self._is_version_compatible(dep_version_req, dep_active_version):
                    conflicts.append({
                        "component": component,
                        "depends_on": dep_component,
                        "required_version": dep_version_req,
                        "active_version": dep_active_version,
                        "type": "incompatible_version",
                        "message": f"{component} {version} requiere {dep_component} {dep_version_req}, pero tiene {dep_active_version}"
                    })
        
        return conflicts
    
    def find_compatible_versions(self, components: Dict[str, str]) -> Dict[str, str]:
        """
        Encuentra un conjunto de versiones compatibles para varios componentes.
        
        Args:
            components: Diccionario de {componente: versión} requeridos
            
        Returns:
            Diccionario de {componente: versión} compatibles
        """
        # Copiar versiones activas como punto de partida
        suggested_versions = self._active_versions.copy()
        
        # Aplicar restricciones
        for component, version in components.items():
            # Omitir componentes no registrados
            if component not in self._versions:
                continue
            
            # Aplicar versión requerida
            suggested_versions[component] = version
        
        # Verificar y resolver conflictos iterativamente
        MAX_ITERATIONS = 10
        for i in range(MAX_ITERATIONS):
            conflicts = []
            
            # Verificar cada componente
            for component, version in suggested_versions.items():
                # Omitir si no existe
                if component not in self._versions or version not in self._versions[component]:
                    continue
                
                # Verificar dependencias
                version_info = self._versions[component][version]
                for dep_component, dep_version_req in version_info.dependencies.items():
                    # Si la dependencia no está activa
                    if dep_component not in suggested_versions:
                        # Buscar mejor versión compatible
                        best_version = self._find_best_version(dep_component, dep_version_req)
                        if best_version:
                            suggested_versions[dep_component] = best_version
                        else:
                            conflicts.append((component, dep_component, dep_version_req, None))
                        continue
                    
                    # Verificar compatibilidad
                    dep_version = suggested_versions[dep_component]
                    if not self._is_version_compatible(dep_version_req, dep_version):
                        # Buscar mejor versión compatible
                        best_version = self._find_best_version(dep_component, dep_version_req)
                        if best_version:
                            suggested_versions[dep_component] = best_version
                        else:
                            conflicts.append((component, dep_component, dep_version_req, dep_version))
            
            # Si no hay conflictos, terminamos
            if not conflicts:
                break
            
            # Si no se pudieron resolver todos los conflictos, terminamos
            if i == MAX_ITERATIONS - 1 and conflicts:
                self.logger.warning(f"No se pudieron resolver todos los conflictos después de {MAX_ITERATIONS} iteraciones")
                break
        
        return suggested_versions
    
    def _find_best_version(self, component: str, version_req: str) -> Optional[str]:
        """
        Encuentra la mejor versión de un componente que cumple un requisito.
        
        Args:
            component: Nombre del componente
            version_req: Requisito de versión
            
        Returns:
            Mejor versión o None si no hay compatible
        """
        if component not in self._versions:
            return None
        
        # Obtener todas las versiones ordenadas
        all_versions = self.list_versions(component)
        
        # Buscar versiones compatibles
        compatible_versions = [v for v in all_versions 
                             if self._is_version_compatible(version_req, v)]
        
        if not compatible_versions:
            return None
        
        # Devolver la más reciente
        return compatible_versions[-1]
    
    def get_compatibility_matrix(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Genera una matriz de compatibilidad entre componentes.
        
        Returns:
            Matriz de compatibilidad {componente: {dependencia: [versiones_compatibles]}}
        """
        matrix = {}
        
        # Para cada componente
        for component in self._versions:
            matrix[component] = {}
            
            # Para cada versión del componente
            for version, version_info in self._versions[component].items():
                # Para cada dependencia
                for dep_component, dep_version_req in version_info.dependencies.items():
                    # Inicializar entrada si no existe
                    if dep_component not in matrix[component]:
                        matrix[component][dep_component] = []
                    
                    # Añadir requisito
                    if dep_version_req not in matrix[component][dep_component]:
                        matrix[component][dep_component].append(dep_version_req)
        
        return matrix
    
    def get_system_version_status(self) -> Dict[str, Any]:
        """
        Obtiene un informe completo del estado de versiones del sistema.
        
        Returns:
            Informe de estado
        """
        # Verificar compatibilidad
        conflicts = self.check_system_compatibility()
        
        # Recopilar información
        status = {
            "components": {},
            "conflicts": conflicts,
            "compatible": len(conflicts) == 0,
            "dependency_graph": self.get_compatibility_matrix(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Información por componente
        for component in self._versions:
            active_version = self.get_active_version(component)
            latest_version = self.list_versions(component)[-1] if self.list_versions(component) else None
            
            status["components"][component] = {
                "active_version": active_version,
                "latest_version": latest_version,
                "all_versions": self.list_versions(component),
                "up_to_date": active_version == latest_version,
                "dependencies": self.get_dependencies(component, active_version) if active_version else {},
                "dependents": self.get_dependent_components(component)
            }
        
        return status