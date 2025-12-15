"""
SUME DOCBLOCK

Nombre: Circuit Breaker
Tipo: Lógica

Entradas:
- Solicitud de ejecución: función, argumentos
- Configuración: max_fallos, tiempo_reset, fallback
- Identificadores de circuitos (source:target)
- Eventos de éxito y fallo de operaciones

Acciones:
- Monitorear éxitos/fallos de llamadas
- Abrir el circuito al alcanzar umbral de fallos
- Permitir intentos ocasionales en estado semi-abierto
- Cerrar el circuito tras éxitos consecutivos
- Ejecutar función fallback cuando circuito abierto
- Emitir eventos de cambio de estado
- Mantener métricas de rendimiento por circuito
- Proteger contra fallos en cascada

Salidas:
- Resultado de la función si circuito cerrado y ejecución exitosa
- Resultado de fallback si circuito abierto
- Eventos de cambio de estado del circuito
- Métricas de éxito/fallo por circuito
"""
import asyncio
import time
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union, List, Tuple


class CircuitState(Enum):
    """Estados posibles de un circuito."""
    CLOSED = "closed"      # Operación normal
    OPEN = "open"          # Bloqueo de llamadas
    HALF_OPEN = "half_open"  # Permitir prueba de recuperación


class CircuitBreaker:
    """
    Implementación del patrón Circuit Breaker para evitar fallos en cascada.
    
    Monitorea llamadas a funciones y "abre el circuito" si ocurren demasiados
    fallos consecutivos, permitiendo al sistema recuperarse y evitando
    sobrecargar componentes con problemas.
    """
    
    def __init__(self, event_bus, store, logger=None, 
                 default_max_failures=3, default_reset_timeout=30,
                 default_half_open_max_calls=1, default_success_threshold=2):
        """
        Inicializa un Circuit Breaker.
        
        Args:
            event_bus: EventBus para emitir eventos
            store: Store para almacenar estado y métricas
            logger: Logger para registro de actividad (opcional)
            default_max_failures: Número máximo de fallos antes de abrir
            default_reset_timeout: Tiempo en segundos antes de pasar a half-open
            default_half_open_max_calls: Número máximo de llamadas permitidas en half-open
            default_success_threshold: Éxitos consecutivos para cerrar el circuito
        """
        self.event_bus = event_bus
        self.store = store
        self.logger = logger or logging.getLogger(__name__)
        
        self.default_max_failures = default_max_failures
        self.default_reset_timeout = default_reset_timeout
        self.default_half_open_max_calls = default_half_open_max_calls
        self.default_success_threshold = default_success_threshold
        
        # Registro de circuitos: {circuit_id: circuit_data}
        self.circuits: Dict[str, Dict[str, Any]] = {}
        
        # Cargar configuración desde el store si existe
        self._load_circuits()
        
        self.logger.debug("CircuitBreaker inicializado")
    
    def _load_circuits(self):
        """Carga el estado de los circuitos desde el store."""
        if not self.store:
            return
        
        # Buscar circuitos existentes
        keys = self.store.keys("circuit.*.state")
        for key in keys:
            try:
                # Extraer circuit_id del patrón "circuit.<id>.state"
                parts = key.split(".")
                if len(parts) >= 3:
                    circuit_id = parts[1]
                    circuit_data = self.store.get(f"circuit.{circuit_id}")
                    if circuit_data:
                        # Convertir string de estado a enum
                        if "state" in circuit_data and isinstance(circuit_data["state"], str):
                            try:
                                circuit_data["state"] = CircuitState(circuit_data["state"])
                            except ValueError:
                                circuit_data["state"] = CircuitState.CLOSED
                        
                        self.circuits[circuit_id] = circuit_data
            except Exception as e:
                self.logger.error(f"Error al cargar circuito desde store: {str(e)}")
        
        self.logger.debug(f"Cargados {len(self.circuits)} circuitos desde el store")
    
    def register_circuit(self, source: str, target: str, 
                        max_failures: Optional[int] = None,
                        reset_timeout: Optional[int] = None,
                        half_open_max_calls: Optional[int] = None,
                        success_threshold: Optional[int] = None) -> None:
        """
        Registra un circuito entre source y target.
        
        Args:
            source: Identificador del origen
            target: Identificador del destino
            max_failures: Fallos máximos antes de abrir (None = default)
            reset_timeout: Tiempo en segundos para reset (None = default)
            half_open_max_calls: Llamadas máximas en half-open (None = default)
            success_threshold: Éxitos para cerrar circuito (None = default)
        """
        # Crear ID único del circuito
        circuit_id = f"{source}:{target}"
        
        # Si ya existe, solo actualizar configuración
        if circuit_id in self.circuits:
            circuit = self.circuits[circuit_id]
            
            # Actualizar configuración si se proporciona
            if max_failures is not None:
                circuit["max_failures"] = max_failures
            if reset_timeout is not None:
                circuit["reset_timeout"] = reset_timeout
            if half_open_max_calls is not None:
                circuit["half_open_max_calls"] = half_open_max_calls
            if success_threshold is not None:
                circuit["success_threshold"] = success_threshold
                
            self.logger.debug(f"Actualizada configuración del circuito: {circuit_id}")
            return
        
        # Crear nuevo circuito
        circuit = {
            "state": CircuitState.CLOSED,
            "failure_count": 0,
            "success_count": 0,
            "last_failure_time": 0,
            "last_success_time": 0,
            "last_state_change": time.time(),
            "total_failures": 0,
            "total_successes": 0,
            "total_timeouts": 0,
            "open_count": 0,  # Número de veces que se ha abierto
            "source": source,
            "target": target,
            "max_failures": max_failures or self.default_max_failures,
            "reset_timeout": reset_timeout or self.default_reset_timeout,
            "half_open_max_calls": half_open_max_calls or self.default_half_open_max_calls,
            "success_threshold": success_threshold or self.default_success_threshold,
            "half_open_calls": 0  # Contador de llamadas en estado half-open
        }
        
        # Registrar circuito
        self.circuits[circuit_id] = circuit
        
        # Persistir en el store
        if self.store:
            self.store.set(f"circuit.{circuit_id}", circuit)
        
        self.logger.debug(f"Registrado circuito: {circuit_id}")
    
    async def execute(self, circuit_id: str, func: Callable, *args, 
                    fallback: Optional[Callable] = None, timeout: Optional[float] = None,
                    **kwargs) -> Any:
        """
        Ejecuta una función con protección de circuit breaker.
        
        Args:
            circuit_id: Identificador del circuito
            func: Función a ejecutar
            *args: Argumentos para la función
            fallback: Función a ejecutar si el circuito está abierto
            timeout: Timeout en segundos (None = sin timeout)
            **kwargs: Argumentos de palabra clave para la función
            
        Returns:
            Resultado de func o fallback
            
        Raises:
            Exception: Si no hay fallback y el circuito está abierto o si func falla
        """
        # Verificar si el circuito existe
        if circuit_id not in self.circuits:
            parts = circuit_id.split(":")
            if len(parts) == 2:
                source, target = parts
                self.register_circuit(source, target)
            else:
                self.logger.warning(f"Formato de circuit_id incorrecto: {circuit_id}, usando default")
                self.register_circuit("default", circuit_id)
        
        # Obtener circuito
        circuit = self.circuits[circuit_id]
        
        # Verificar estado del circuito
        current_state = circuit["state"]
        current_time = time.time()
        
        # Si está abierto, verificar si podemos pasar a half-open
        if current_state == CircuitState.OPEN:
            if current_time - circuit["last_failure_time"] > circuit["reset_timeout"]:
                # Transición a half-open
                self._change_state(circuit_id, CircuitState.HALF_OPEN)
                circuit["half_open_calls"] = 0
            else:
                # Si existe fallback, usarlo
                if fallback:
                    self.logger.debug(f"Circuito {circuit_id} abierto, usando fallback")
                    return fallback(*args, **kwargs)
                else:
                    raise RuntimeError(f"Circuito {circuit_id} abierto")
        
        # Si está en half-open, limitar número de llamadas
        if current_state == CircuitState.HALF_OPEN:
            circuit["half_open_calls"] += 1
            if circuit["half_open_calls"] > circuit["half_open_max_calls"]:
                # Si existe fallback, usarlo
                if fallback:
                    self.logger.debug(f"Circuito {circuit_id} en half-open con máximo de llamadas alcanzado, usando fallback")
                    return fallback(*args, **kwargs)
                else:
                    raise RuntimeError(f"Circuito {circuit_id} en half-open con máximo de llamadas alcanzado")
        
        # Ejecutar función con timeout si se especifica
        try:
            start_time = time.perf_counter()
            
            if timeout is not None:
                # Ejecutar con timeout
                result = await asyncio.wait_for(
                    self._call_function(func, *args, **kwargs),
                    timeout=timeout
                )
            else:
                # Ejecutar sin timeout
                result = await self._call_function(func, *args, **kwargs)
            
            # Calcular duración
            duration = time.perf_counter() - start_time
            
            # Registrar éxito
            self._record_success(circuit_id, duration)
            
            return result
            
        except asyncio.TimeoutError:
            # Registrar timeout como fallo
            self._record_timeout(circuit_id)
            
            # Si existe fallback, usarlo
            if fallback:
                return fallback(*args, **kwargs)
            else:
                raise
            
        except Exception as e:
            # Registrar fallo
            self._record_failure(circuit_id, str(e))
            
            # Si existe fallback, usarlo
            if fallback:
                return fallback(*args, **kwargs)
            else:
                raise
    
    async def _call_function(self, func: Callable, *args, **kwargs) -> Any:
        """
        Llama a una función, soportando tanto síncronas como asíncronas.
        
        Args:
            func: Función a llamar
            *args: Argumentos
            **kwargs: Argumentos de palabra clave
            
        Returns:
            Resultado de la función
        """
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def _record_success(self, circuit_id: str, duration: float) -> None:
        """
        Registra un éxito en un circuito.
        
        Args:
            circuit_id: Identificador del circuito
            duration: Duración de la operación en segundos
        """
        if circuit_id not in self.circuits:
            return
        
        circuit = self.circuits[circuit_id]
        current_state = circuit["state"]
        current_time = time.time()
        
        # Incrementar contadores
        circuit["success_count"] += 1
        circuit["total_successes"] += 1
        circuit["last_success_time"] = current_time
        
        # Resetear contador de fallos
        circuit["failure_count"] = 0
        
        # Guardar duración
        duration_ms = duration * 1000
        if self.store:
            self.store.set(f"circuit.{circuit_id}.latency.{int(current_time)}", duration_ms)
        
        # Emitir evento de métrica
        if self.event_bus:
            self.event_bus.emit("metrics:circuit_latency", {
                "circuit_id": circuit_id,
                "duration_ms": duration_ms,
                "timestamp": current_time
            })
        
        # Si está en half-open y alcanzamos umbral de éxitos, cerrar circuito
        if current_state == CircuitState.HALF_OPEN and circuit["success_count"] >= circuit["success_threshold"]:
            self._change_state(circuit_id, CircuitState.CLOSED)
        
        # Actualizar en store
        if self.store:
            self.store.set(f"circuit.{circuit_id}", circuit)
    
    def _record_failure(self, circuit_id: str, error: str) -> None:
        """
        Registra un fallo en un circuito.
        
        Args:
            circuit_id: Identificador del circuito
            error: Mensaje de error
        """
        if circuit_id not in self.circuits:
            return
        
        circuit = self.circuits[circuit_id]
        current_state = circuit["state"]
        current_time = time.time()
        
        # Incrementar contadores
        circuit["failure_count"] += 1
        circuit["total_failures"] += 1
        circuit["last_failure_time"] = current_time
        
        # Resetear contador de éxitos
        circuit["success_count"] = 0
        
        # Registrar error
        if self.store:
            self.store.set(f"circuit.{circuit_id}.error.{int(current_time)}", {
                "error": error,
                "timestamp": current_time
            })
        
        # Si alcanzamos máximo de fallos, abrir circuito
        if (current_state in (CircuitState.CLOSED, CircuitState.HALF_OPEN) and 
            circuit["failure_count"] >= circuit["max_failures"]):
            self._change_state(circuit_id, CircuitState.OPEN)
            circuit["open_count"] += 1
        
        # Actualizar en store
        if self.store:
            self.store.set(f"circuit.{circuit_id}", circuit)
    
    def _record_timeout(self, circuit_id: str) -> None:
        """
        Registra un timeout en un circuito.
        
        Args:
            circuit_id: Identificador del circuito
        """
        if circuit_id not in self.circuits:
            return
        
        circuit = self.circuits[circuit_id]
        circuit["total_timeouts"] += 1
        
        # Tratar timeout como fallo
        self._record_failure(circuit_id, "Timeout")
    
    def _change_state(self, circuit_id: str, new_state: CircuitState) -> None:
        """
        Cambia el estado de un circuito.
        
        Args:
            circuit_id: Identificador del circuito
            new_state: Nuevo estado
        """
        if circuit_id not in self.circuits:
            return
        
        circuit = self.circuits[circuit_id]
        old_state = circuit["state"]
        
        # Si no hay cambio real, salir
        if old_state == new_state:
            return
        
        # Cambiar estado
        circuit["state"] = new_state
        circuit["last_state_change"] = time.time()
        
        # Resetear contadores según el nuevo estado
        if new_state == CircuitState.CLOSED:
            circuit["failure_count"] = 0
            circuit["success_count"] = 0
        elif new_state == CircuitState.OPEN:
            circuit["success_count"] = 0
        elif new_state == CircuitState.HALF_OPEN:
            circuit["half_open_calls"] = 0
            circuit["success_count"] = 0
        
        # Log
        self.logger.info(f"Circuito {circuit_id} cambió de {old_state.value} a {new_state.value}")
        
        # Persistir cambio
        if self.store:
            self.store.set(f"circuit.{circuit_id}", circuit)
            self.store.set(f"circuit.{circuit_id}.state_change.{int(time.time())}", {
                "from": old_state.value,
                "to": new_state.value,
                "timestamp": time.time()
            })
        
        # Emitir evento
        if self.event_bus:
            self.event_bus.emit("circuit:state_change", {
                "circuit_id": circuit_id,
                "old_state": old_state.value,
                "new_state": new_state.value,
                "timestamp": datetime.utcnow().isoformat(),
                "source": circuit.get("source", "unknown"),
                "target": circuit.get("target", "unknown")
            })
    
    def reset(self, circuit_id: str) -> bool:
        """
        Resetea un circuito a estado cerrado manualmente.
        
        Args:
            circuit_id: Identificador del circuito
            
        Returns:
            True si se reseteó correctamente
        """
        if circuit_id not in self.circuits:
            return False
        
        self._change_state(circuit_id, CircuitState.CLOSED)
        self.logger.info(f"Circuito {circuit_id} reseteado manualmente")
        return True
    
    def get_state(self, circuit_id: str) -> Optional[CircuitState]:
        """
        Obtiene el estado actual de un circuito.
        
        Args:
            circuit_id: Identificador del circuito
            
        Returns:
            Estado del circuito o None si no existe
        """
        if circuit_id not in self.circuits:
            return None
        
        return self.circuits[circuit_id]["state"]
    
    def get_circuit_info(self, circuit_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información completa de un circuito.
        
        Args:
            circuit_id: Identificador del circuito
            
        Returns:
            Información del circuito o None si no existe
        """
        if circuit_id not in self.circuits:
            return None
        
        # Devolver copia para evitar modificaciones
        circuit = self.circuits[circuit_id].copy()
        
        # Convertir CircuitState a string para serialización
        if "state" in circuit and isinstance(circuit["state"], CircuitState):
            circuit["state"] = circuit["state"].value
        
        return circuit
    
    def list_circuits(self) -> List[str]:
        """
        Lista todos los circuitos registrados.
        
        Returns:
            Lista de identificadores de circuito
        """
        return list(self.circuits.keys())
    
    def get_all_circuits_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene información de todos los circuitos.
        
        Returns:
            Diccionario {circuit_id: circuit_info}
        """
        result = {}
        
        for circuit_id, circuit in self.circuits.items():
            # Crear copia y convertir enums a strings
            circuit_copy = circuit.copy()
            if "state" in circuit_copy and isinstance(circuit_copy["state"], CircuitState):
                circuit_copy["state"] = circuit_copy["state"].value
                
            result[circuit_id] = circuit_copy
        
        return result
    
    def update_configuration(self, circuit_id: str, config: Dict[str, Any]) -> bool:
        """
        Actualiza la configuración de un circuito.
        
        Args:
            circuit_id: Identificador del circuito
            config: Diccionario con parámetros a actualizar
            
        Returns:
            True si se actualizó correctamente
        """
        if circuit_id not in self.circuits:
            return False
        
        circuit = self.circuits[circuit_id]
        
        # Actualizar parámetros permitidos
        allowed_params = ["max_failures", "reset_timeout", "half_open_max_calls", "success_threshold"]
        updated = False
        
        for param in allowed_params:
            if param in config:
                circuit[param] = config[param]
                updated = True
        
        # Persistir si hubo cambios
        if updated and self.store:
            self.store.set(f"circuit.{circuit_id}", circuit)
            
        return updated
    
    def get_metrics(self, circuit_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene métricas de uno o todos los circuitos.
        
        Args:
            circuit_id: Identificador del circuito o None para todos
            
        Returns:
            Diccionario con métricas
        """
        if circuit_id:
            # Métricas de un circuito específico
            if circuit_id not in self.circuits:
                return {}
                
            circuit = self.circuits[circuit_id]
            return {
                "circuit_id": circuit_id,
                "state": circuit["state"].value if isinstance(circuit["state"], CircuitState) else circuit["state"],
                "total_successes": circuit["total_successes"],
                "total_failures": circuit["total_failures"],
                "total_timeouts": circuit["total_timeouts"],
                "open_count": circuit["open_count"],
                "success_rate": self._calculate_success_rate(circuit),
                "last_failure": circuit["last_failure_time"],
                "last_success": circuit["last_success_time"],
                "last_state_change": circuit["last_state_change"]
            }
        else:
            # Métricas agregadas de todos los circuitos
            total_circuits = len(self.circuits)
            open_circuits = sum(1 for c in self.circuits.values() 
                              if c["state"] == CircuitState.OPEN)
            half_open_circuits = sum(1 for c in self.circuits.values() 
                                   if c["state"] == CircuitState.HALF_OPEN)
            closed_circuits = total_circuits - open_circuits - half_open_circuits
            
            total_successes = sum(c["total_successes"] for c in self.circuits.values())
            total_failures = sum(c["total_failures"] for c in self.circuits.values())
            total_timeouts = sum(c["total_timeouts"] for c in self.circuits.values())
            
            # Calcular tasa de éxito global
            success_rate = 0
            if total_successes + total_failures > 0:
                success_rate = total_successes / (total_successes + total_failures)
            
            return {
                "total_circuits": total_circuits,
                "open_circuits": open_circuits,
                "half_open_circuits": half_open_circuits,
                "closed_circuits": closed_circuits,
                "total_successes": total_successes,
                "total_failures": total_failures,
                "total_timeouts": total_timeouts,
                "global_success_rate": success_rate,
                "circuits": {cid: self.get_state(cid).value if self.get_state(cid) else "unknown" 
                           for cid in self.circuits}
            }
    
    def _calculate_success_rate(self, circuit: Dict[str, Any]) -> float:
        """
        Calcula la tasa de éxito para un circuito.
        
        Args:
            circuit: Datos del circuito
            
        Returns:
            Tasa de éxito (0-1)
        """
        total_calls = circuit["total_successes"] + circuit["total_failures"]
        if total_calls == 0:
            return 1.0  # Sin llamadas, asumir 100% éxito
            
        return circuit["total_successes"] / total_calls