"""
SUME DOCBLOCK

Nombre: Interaction Manager
Tipo: Lógica

Entradas:
- Declaraciones de interacción (registro)
- Solicitudes de interacción: source_module, target_module, payload
- Credenciales y contexto de seguridad

Acciones:
- Registrar relaciones permitidas entre módulos
- Mediar invocaciones entre módulos
- Validar permisos de interacción
- Aplicar políticas de seguridad
- Verificar autenticación y autorización 
- Emitir logs/trazas de cada interacción y resultados
- Gestionar errores y notificar al sistema
- Medir latencia y aplicar timeouts
- Gestionar circuitos con módulos de resiliencia

Salidas:
- Ejecución de la acción en el módulo destino
- Registro de trazabilidad en Store
- Emisión de eventos de éxito o fallo
- Métricas de latencia y éxito/fallo
"""
import logging
import time
from datetime import datetime
from typing import Dict, Set, Any, Optional, List, Callable, Union
import asyncio
from enum import Enum


class PermissionLevel(Enum):
    """Niveles de permiso para interacciones entre módulos."""
    NONE = 0        # Sin permisos
    READ = 10       # Solo lectura
    NORMAL = 20     # Operaciones normales
    ELEVATED = 30   # Operaciones privilegiadas
    ADMIN = 40      # Operaciones administrativas
    SYSTEM = 50     # Operaciones del sistema


class SecurityContext:
    """Contexto de seguridad para interacciones."""
    
    def __init__(self, level: PermissionLevel = PermissionLevel.NORMAL, **attributes):
        """
        Inicializa un contexto de seguridad.
        
        Args:
            level: Nivel de permiso
            **attributes: Atributos adicionales (roles, claims, etc.)
        """
        self.level = level
        self.attributes = attributes


class InteractionManager:
    """
    Mediador de interacciones entre módulos del sistema.
    
    Proporciona un mecanismo centralizado para controlar y auditar
    todas las comunicaciones entre componentes, aplicando políticas
    de seguridad y resiliencia.
    """
    
    def __init__(self, event_bus, store, logger=None, circuit_breaker=None):
        """
        Inicializa el gestor de interacciones.
        
        Args:
            event_bus: EventBus para emisión de eventos
            store: Store para almacenamiento de trazas
            logger: Logger para registro de actividad (opcional)
            circuit_breaker: CircuitBreaker para manejo de fallos (opcional)
        """
        self.event_bus = event_bus
        self.store = store
        self.logger = logger or logging.getLogger(__name__)
        self.circuit_breaker = circuit_breaker
        
        # Relaciones permitidas entre módulos
        self.registry: Dict[str, Dict[str, PermissionLevel]] = {}
        
        # Estadísticas de interacciones
        self._stats: Dict[str, Dict[str, int]] = {}
        
        # Timeouts configurados
        self._timeouts: Dict[str, float] = {}
        
        # Habilitar telemetría por defecto
        self.telemetry_enabled = True
        
        self.logger.debug("InteractionManager inicializado")
    
    def register_interaction(self, source: str, target: str, 
                             permission_level: PermissionLevel = PermissionLevel.NORMAL) -> None:
        """
        Registra que 'source' puede interactuar con 'target' con nivel de permiso específico.
        
        Args:
            source: Módulo origen
            target: Módulo destino
            permission_level: Nivel de permiso requerido
        """
        # Inicializar diccionario para source si no existe
        if source not in self.registry:
            self.registry[source] = {}
        
        # Registrar permiso
        self.registry[source][target] = permission_level
        
        # Registrar también en el circuit breaker si está disponible
        if self.circuit_breaker:
            self.circuit_breaker.register_circuit(source, target)
        
        self.logger.debug(f"Registered interaction: {source} -> {target} (level: {permission_level.name})")
    
    def set_timeout(self, source: str, target: str, timeout_seconds: float) -> None:
        """
        Establece un timeout para interacciones específicas.
        
        Args:
            source: Módulo origen
            target: Módulo destino
            timeout_seconds: Timeout en segundos
        """
        self._timeouts[f"{source}:{target}"] = timeout_seconds
        self.logger.debug(f"Timeout set for {source}->{target}: {timeout_seconds}s")
    
    async def call(self, source: str, target: str, payload: Any, 
                  security_context: Optional[SecurityContext] = None) -> Any:
        """
        Mediador de interacción entre módulos con trazabilidad y seguridad.
        
        Args:
            source: Módulo origen
            target: Módulo destino
            payload: Datos para la interacción
            security_context: Contexto de seguridad (opcional)
            
        Returns:
            Resultado de la interacción
            
        Raises:
            PermissionError: Si la interacción no está permitida
            TimeoutError: Si la interacción supera el timeout
            RuntimeError: Si hay un error en la interacción
        """
        # Generar identificadores
        circuit_id = f"{source}:{target}"
        timestamp = datetime.utcnow().isoformat()
        trace_key = f"interaction.{source}.{target}.{timestamp}"
        
        # Metadata extendida para trazabilidad
        metadata = {
            'status': 'pending',
            'timestamp': timestamp,
            'source': source,
            'target': target,
            'payload_summary': str(payload)[:100] if payload else None,
            'security_level': security_context.level.name if security_context else 'NONE'
        }
        
        # Guardar metadatos iniciales para registro completo
        self.store.set(trace_key, metadata)
        
        # Incrementar contador de solicitudes
        self._update_stats(source, target, "requests")
        
        # Obtener timeout configurado o usar valor por defecto
        timeout = self._timeouts.get(circuit_id, self._timeouts.get(f"{source}:*", 10.0))
        
        # Verificar permisos básicos de interacción
        target_permission = self.registry.get(source, {}).get(target)
        if not target_permission:
            error = f"Interaction not permitted: {source} -> {target}"
            self._handle_error(trace_key, metadata, error, "PERMISSION_ERROR")
            self._update_stats(source, target, "permission_errors")
            raise PermissionError(error)
        
        # Verificar credenciales de seguridad si están habilitadas
        if security_context and target_permission.value > security_context.level.value:
            error = f"Security level insufficient: required {target_permission.name}, got {security_context.level.name}"
            self._handle_error(trace_key, metadata, error, "SECURITY_ERROR")
            self._update_stats(source, target, "security_errors")
            raise PermissionError(error)
        
        # Ejecutar con protección de circuit breaker si está disponible
        try:
            start_time = time.perf_counter_ns()
            
            if self.circuit_breaker:
                return await self.circuit_breaker.execute(
                    circuit_id,
                    self._do_call,
                    source, target, payload, trace_key, metadata, timeout,
                    fallback=lambda *args: self._fallback_handler(source, target, payload)
                )
            else:
                return await self._do_call(source, target, payload, trace_key, metadata, timeout)
        
        except Exception as e:
            # Registrar excepción específica
            if isinstance(e, asyncio.TimeoutError):
                error_type = "TIMEOUT_ERROR"
                self._update_stats(source, target, "timeouts")
            elif isinstance(e, PermissionError):
                error_type = "PERMISSION_ERROR"
            else:
                error_type = "EXECUTION_ERROR"
                self._update_stats(source, target, "errors")
            
            self._handle_error(trace_key, metadata, str(e), error_type)
            raise
        
        finally:
            # Medir y registrar latencia
            if start_time:
                duration_ms = (time.perf_counter_ns() - start_time) / 1_000_000
                self._record_latency(source, target, duration_ms)
    
    async def _do_call(self, source, target, payload, trace_key, metadata, timeout):
        """
        Ejecuta la llamada real al módulo destino.
        
        Args:
            source: Módulo origen
            target: Módulo destino
            payload: Datos para la interacción
            trace_key: Clave para trazabilidad
            metadata: Metadatos de la interacción
            timeout: Timeout en segundos
            
        Returns:
            Resultado de la interacción
        """
        try:
            # Notificar inicio de la llamada
            self.event_bus.emit(f"module:call:{target}", {'from': source, 'payload': payload})
            
            # Ejecutar la llamada con timeout
            try:
                result = await asyncio.wait_for(
                    self.event_bus.emit_async(f"module:handle:{target}", payload),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"Interaction timeout after {timeout}s: {source}->{target}")
            
            # Actualizar metadatos con éxito
            metadata.update({
                'status': 'success',
                'completed_at': datetime.utcnow().isoformat(),
            })
            self.store.set(trace_key, metadata)
            
            # Incrementar contador de éxitos
            self._update_stats(source, target, "successes")
            
            # Emitir métricas si la telemetría está habilitada
            if self.telemetry_enabled:
                self.event_bus.emit("telemetry:interaction", {
                    'trace_key': trace_key,
                    'source': source,
                    'target': target,
                    'success': True
                })
            
            return result
        
        except Exception as e:
            # Si no es TimeoutError, es un error de ejecución
            if not isinstance(e, TimeoutError):
                self._handle_error(trace_key, metadata, str(e), "EXECUTION_ERROR")
            raise
    
    def _fallback_handler(self, source, target, payload):
        """
        Manejador de fallback cuando el circuito está abierto.
        
        Args:
            source: Módulo origen
            target: Módulo destino
            payload: Datos de la interacción
            
        Returns:
            Valor por defecto apropiado
        """
        self.logger.warning(f"Circuit open for {source}->{target}, using fallback")
        
        # Incrementar contador de fallbacks
        self._update_stats(source, target, "fallbacks")
        
        # Emitir evento de fallback
        self.event_bus.emit(
            "module:circuit_fallback",
            {'source': source, 'target': target}
        )
        
        # Implementar lógica de fallback específica por tipo de módulo
        # Esta implementación es básica, se podría mejorar con estrategias
        # específicas por tipo de módulo o payload
        return None
    
    def _handle_error(self, trace_key, metadata, error_msg, error_type):
        """
        Maneja errores de interacción uniformemente.
        
        Args:
            trace_key: Clave para trazabilidad
            metadata: Metadatos de la interacción
            error_msg: Mensaje de error
            error_type: Tipo de error
        """
        self.logger.error(f"[{error_type}] {error_msg}")
        
        # Actualizar metadatos con error
        metadata.update({
            'status': 'error',
            'error': error_msg,
            'error_type': error_type,
            'error_time': datetime.utcnow().isoformat()
        })
        self.store.set(trace_key, metadata)
        
        # Emitir evento de error
        self.event_bus.emit(
            "module:interaction_error",
            {'trace_key': trace_key, 'error_type': error_type, 'error': error_msg}
        )
    
    def _update_stats(self, source: str, target: str, stat_type: str):
        """
        Actualiza estadísticas de interacciones.
        
        Args:
            source: Módulo origen
            target: Módulo destino
            stat_type: Tipo de estadística a incrementar
        """
        # Inicializar diccionarios si no existen
        if source not in self._stats:
            self._stats[source] = {}
        
        if target not in self._stats[source]:
            self._stats[source][target] = {
                "requests": 0,
                "successes": 0,
                "errors": 0,
                "timeouts": 0,
                "fallbacks": 0,
                "permission_errors": 0,
                "security_errors": 0,
                "latency_sum": 0,
                "latency_count": 0,
                "latency_max": 0
            }
        
        # Incrementar contador
        if stat_type in self._stats[source][target]:
            self._stats[source][target][stat_type] += 1
    
    def _record_latency(self, source: str, target: str, duration_ms: float):
        """
        Registra latencia de una interacción.
        
        Args:
            source: Módulo origen
            target: Módulo destino
            duration_ms: Duración en milisegundos
        """
        # Inicializar diccionarios si no existen
        if source not in self._stats:
            self._stats[source] = {}
        
        if target not in self._stats[source]:
            self._stats[source][target] = {
                "requests": 0,
                "successes": 0,
                "errors": 0,
                "timeouts": 0,
                "fallbacks": 0,
                "permission_errors": 0,
                "security_errors": 0,
                "latency_sum": 0,
                "latency_count": 0,
                "latency_max": 0
            }
        
        # Actualizar estadísticas de latencia
        self._stats[source][target]["latency_sum"] += duration_ms
        self._stats[source][target]["latency_count"] += 1
        
        # Actualizar latencia máxima
        if duration_ms > self._stats[source][target]["latency_max"]:
            self._stats[source][target]["latency_max"] = duration_ms
        
        # Registrar métrica detallada si la telemetría está habilitada
        if self.telemetry_enabled:
            self.event_bus.emit("telemetry:latency", {
                "source": source,
                "target": target,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def get_stats(self, source: Optional[str] = None, target: Optional[str] = None) -> Dict:
        """
        Obtiene estadísticas de interacciones.
        
        Args:
            source: Filtrar por módulo origen (opcional)
            target: Filtrar por módulo destino (opcional)
            
        Returns:
            Diccionario con estadísticas
        """
        # Sin filtros, devolver todas las estadísticas
        if source is None and target is None:
            # Calcular totales
            total_stats = {
                "total_requests": 0,
                "total_successes": 0,
                "total_errors": 0,
                "total_timeouts": 0,
                "total_fallbacks": 0,
                "error_rate": 0.0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "interactions": {}
            }
            
            latency_sum = 0
            latency_count = 0
            max_latency = 0
            
            # Agregar estadísticas de todas las interacciones
            for s, targets in self._stats.items():
                for t, stats in targets.items():
                    # Actualizar totales
                    total_stats["total_requests"] += stats["requests"]
                    total_stats["total_successes"] += stats["successes"]
                    total_stats["total_errors"] += stats["errors"]
                    total_stats["total_timeouts"] += stats["timeouts"]
                    total_stats["total_fallbacks"] += stats["fallbacks"]
                    
                    # Actualizar latencia
                    latency_sum += stats["latency_sum"]
                    latency_count += stats["latency_count"]
                    max_latency = max(max_latency, stats["latency_max"])
                    
                    # Guardar detalle
                    if s not in total_stats["interactions"]:
                        total_stats["interactions"][s] = {}
                    
                    # Calcular latencia promedio para esta interacción
                    avg_latency = 0
                    if stats["latency_count"] > 0:
                        avg_latency = stats["latency_sum"] / stats["latency_count"]
                    
                    total_stats["interactions"][s][t] = {
                        "requests": stats["requests"],
                        "successes": stats["successes"],
                        "errors": stats["errors"],
                        "timeouts": stats["timeouts"],
                        "fallbacks": stats["fallbacks"],
                        "avg_latency_ms": avg_latency,
                        "max_latency_ms": stats["latency_max"]
                    }
            
            # Calcular tasas globales
            if total_stats["total_requests"] > 0:
                total_stats["error_rate"] = total_stats["total_errors"] / total_stats["total_requests"]
                total_stats["success_rate"] = total_stats["total_successes"] / total_stats["total_requests"]
            
            # Calcular latencia promedio global
            if latency_count > 0:
                total_stats["avg_latency_ms"] = latency_sum / latency_count
            
            total_stats["max_latency_ms"] = max_latency
            
            return total_stats
        
        # Filtrar por source
        elif source is not None and target is None:
            if source not in self._stats:
                return {}
            
            # Agregar estadísticas de todas las interacciones del source
            source_stats = {
                "total_requests": 0,
                "total_successes": 0,
                "total_errors": 0,
                "total_timeouts": 0,
                "total_fallbacks": 0,
                "error_rate": 0.0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "targets": {}
            }
            
            latency_sum = 0
            latency_count = 0
            max_latency = 0
            
            for t, stats in self._stats[source].items():
                # Actualizar totales
                source_stats["total_requests"] += stats["requests"]
                source_stats["total_successes"] += stats["successes"]
                source_stats["total_errors"] += stats["errors"]
                source_stats["total_timeouts"] += stats["timeouts"]
                source_stats["total_fallbacks"] += stats["fallbacks"]
                
                # Actualizar latencia
                latency_sum += stats["latency_sum"]
                latency_count += stats["latency_count"]
                max_latency = max(max_latency, stats["latency_max"])
                
                # Calcular latencia promedio para esta interacción
                avg_latency = 0
                if stats["latency_count"] > 0:
                    avg_latency = stats["latency_sum"] / stats["latency_count"]
                
                source_stats["targets"][t] = {
                    "requests": stats["requests"],
                    "successes": stats["successes"],
                    "errors": stats["errors"],
                    "timeouts": stats["timeouts"],
                    "fallbacks": stats["fallbacks"],
                    "avg_latency_ms": avg_latency,
                    "max_latency_ms": stats["latency_max"]
                }
            
            # Calcular tasas
            if source_stats["total_requests"] > 0:
                source_stats["error_rate"] = source_stats["total_errors"] / source_stats["total_requests"]
                source_stats["success_rate"] = source_stats["total_successes"] / source_stats["total_requests"]
            
            # Calcular latencia promedio
            if latency_count > 0:
                source_stats["avg_latency_ms"] = latency_sum / latency_count
            
            source_stats["max_latency_ms"] = max_latency
            
            return source_stats
        
        # Filtrar por source y target
        elif source is not None and target is not None:
            if source not in self._stats or target not in self._stats[source]:
                return {}
            
            stats = self._stats[source][target]
            
            # Calcular latencia promedio
            avg_latency = 0
            if stats["latency_count"] > 0:
                avg_latency = stats["latency_sum"] / stats["latency_count"]
            
            # Calcular tasas
            error_rate = 0.0
            success_rate = 0.0
            if stats["requests"] > 0:
                error_rate = stats["errors"] / stats["requests"]
                success_rate = stats["successes"] / stats["requests"]
            
            return {
                "requests": stats["requests"],
                "successes": stats["successes"],
                "errors": stats["errors"],
                "timeouts": stats["timeouts"],
                "fallbacks": stats["fallbacks"],
                "permission_errors": stats["permission_errors"],
                "security_errors": stats["security_errors"],
                "error_rate": error_rate,
                "success_rate": success_rate,
                "avg_latency_ms": avg_latency,
                "max_latency_ms": stats["latency_max"]
            }
    
    def reset_stats(self, source: Optional[str] = None, target: Optional[str] = None) -> None:
        """
        Reinicia estadísticas de interacciones.
        
        Args:
            source: Filtrar por módulo origen (opcional)
            target: Filtrar por módulo destino (opcional)
        """
        # Reiniciar todas las estadísticas
        if source is None and target is None:
            self._stats = {}
        
        # Reiniciar estadísticas para un source
        elif source is not None and target is None:
            if source in self._stats:
                self._stats[source] = {}
        
        # Reiniciar estadísticas para un par source-target
        elif source is not None and target is not None:
            if source in self._stats and target in self._stats[source]:
                self._stats[source][target] = {
                    "requests": 0,
                    "successes": 0,
                    "errors": 0,
                    "timeouts": 0,
                    "fallbacks": 0,
                    "permission_errors": 0,
                    "security_errors": 0,
                    "latency_sum": 0,
                    "latency_count": 0,
                    "latency_max": 0
                }
    
    def is_interaction_allowed(self, source: str, target: str, 
                              security_context: Optional[SecurityContext] = None) -> bool:
        """
        Verifica si una interacción está permitida.
        
        Args:
            source: Módulo origen
            target: Módulo destino
            security_context: Contexto de seguridad (opcional)
            
        Returns:
            True si la interacción está permitida
        """
        # Verificar registro básico
        if source not in self.registry or target not in self.registry[source]:
            return False
        
        # Verificar nivel de permiso
        if security_context:
            target_permission = self.registry[source][target]
            if target_permission.value > security_context.level.value:
                return False
        
        return True
    
    def get_allowed_targets(self, source: str, 
                           security_context: Optional[SecurityContext] = None) -> List[str]:
        """
        Obtiene la lista de módulos destino permitidos para un origen.
        
        Args:
            source: Módulo origen
            security_context: Contexto de seguridad (opcional)
            
        Returns:
            Lista de módulos destino permitidos
        """
        if source not in self.registry:
            return []
        
        # Sin contexto de seguridad, devolver todos los destinos registrados
        if not security_context:
            return list(self.registry[source].keys())
        
        # Filtrar por nivel de permiso
        allowed = []
        for target, permission_level in self.registry[source].items():
            if permission_level.value <= security_context.level.value:
                allowed.append(target)
        
        return allowed
    
    def get_allowed_sources(self, target: str,
                           security_context: Optional[SecurityContext] = None) -> List[str]:
        """
        Obtiene la lista de módulos origen que pueden acceder a un destino.
        
        Args:
            target: Módulo destino
            security_context: Contexto de seguridad (opcional)
            
        Returns:
            Lista de módulos origen permitidos
        """
        allowed = []
        
        # Buscar en todo el registro
        for source, targets in self.registry.items():
            if target in targets:
                # Verificar nivel de permiso
                if security_context:
                    if targets[target].value <= security_context.level.value:
                        allowed.append(source)
                else:
                    allowed.append(source)
        
        return allowed