"""
SUME DOCBLOCK

Nombre: Core Manager
Tipo: Lógica

Entradas:
- Configuración del sistema
- Eventos del sistema
- Instrucciones de control (inicio, pausa, reinicio, cierre)
- Estado de componentes del sistema

Acciones:
- Inicializar componentes del sistema en orden correcto
- Coordinar la comunicación entre módulos
- Gestionar el ciclo de vida del sistema
- Monitorear salud de componentes
- Aplicar políticas de resiliencia y recuperación
- Gestionar recursos del sistema (CPU, memoria)
- Reiniciar componentes fallidos cuando sea posible
- Manejar señales del sistema operativo

Salidas:
- Estado global del sistema
- Eventos de cambio de estado
- Métricas de rendimiento
- Logs de actividad del sistema
- Respuesta a instrucciones de control
"""
import asyncio
import os
import signal
import sys
import time
import psutil
import logging
from typing import Dict, Any, List, Optional, Set, Callable, Tuple, Union
import threading
from datetime import datetime, timedelta


class SystemState:
    """Estados posibles del sistema."""
    INITIALIZING = "initializing"  # Iniciando componentes
    RUNNING = "running"            # En funcionamiento normal
    DEGRADED = "degraded"          # Funcionando con errores en algunos componentes
    MAINTENANCE = "maintenance"    # En mantenimiento programado
    STOPPING = "stopping"          # En proceso de apagado
    STOPPED = "stopped"            # Detenido completamente
    ERROR = "error"                # Error crítico


class CoreManager:
    """
    Gestor central del sistema Core Dajarony.
    
    Coordina la inicialización, operación y apagado de todos los componentes
    del sistema, además de proporcionar monitoreo y control centralizado.
    """
    
    def __init__(self, container):
        """
        Inicializa el Core Manager.
        
        Args:
            container: Contenedor con los servicios del sistema
        """
        self.container = container
        self.logger = container.get("logger")
        self.event_bus = container.get("event_bus")
        self.store = container.get("store")
        self.config = container.get("config")
        
        # Estado actual del sistema
        self._state = SystemState.STOPPED
        
        # Hora de inicio y última actualización
        self._start_time = None
        self._last_update = None
        
        # Control de ciclos de monitoreo
        self._monitoring = False
        self._monitoring_interval = 5  # segundos
        
        # Tareas asíncronas
        self._tasks = []
        
        # Componentes registrados con sus estados
        self._components = {}
        
        # Bloqueo para operaciones concurrentes
        self._lock = threading.RLock()
        
        # Configurar manejadores de señales
        self._setup_signal_handlers()
        
        self.logger.info("Core Manager inicializado")
    
    def _setup_signal_handlers(self):
        """Configura manejadores para señales del sistema operativo."""
        # SIGINT (Ctrl+C)
        try:
            signal.signal(signal.SIGINT, self._handle_sigint)
            signal.signal(signal.SIGTERM, self._handle_sigterm)
            self.logger.debug("Manejadores de señales configurados")
        except Exception as e:
            self.logger.warning(f"No se pudieron configurar manejadores de señales: {str(e)}")
    
    def _handle_sigint(self, signum, frame):
        """Manejador para señal SIGINT (Ctrl+C)."""
        self.logger.info("Señal SIGINT recibida, iniciando apagado ordenado...")
        asyncio.create_task(self.stop())
    
    def _handle_sigterm(self, signum, frame):
        """Manejador para señal SIGTERM."""
        self.logger.info("Señal SIGTERM recibida, iniciando apagado ordenado...")
        asyncio.create_task(self.stop())
    
    async def start(self):
        """
        Inicia el sistema completo.
        
        Returns:
            True si el inicio fue exitoso
        """
        with self._lock:
            if self._state not in (SystemState.STOPPED, SystemState.ERROR):
                self.logger.warning(f"No se puede iniciar: el sistema ya está en estado {self._state}")
                return False
            
            # Actualizar estado
            self._state = SystemState.INITIALIZING
            self._start_time = datetime.now()
            self._last_update = self._start_time
            
            # Emitir evento de inicio
            if self.event_bus:
                self.event_bus.emit("system:state_changed", {
                    "old_state": SystemState.STOPPED,
                    "new_state": SystemState.INITIALIZING,
                    "timestamp": self._start_time.isoformat()
                })
            
            self.logger.info("Iniciando Core Dajarony...")
            
            try:
                # Inicializar componentes del sistema en orden
                await self._initialize_components()
                
                # Iniciar monitoreo
                self._start_monitoring()
                
                # Actualizar estado
                self._state = SystemState.RUNNING
                self._last_update = datetime.now()
                
                # Emitir evento de sistema funcionando
                if self.event_bus:
                    self.event_bus.emit("system:state_changed", {
                        "old_state": SystemState.INITIALIZING,
                        "new_state": SystemState.RUNNING,
                        "timestamp": self._last_update.isoformat()
                    })
                
                self.logger.info("Sistema iniciado y en funcionamiento")
                return True
                
            except Exception as e:
                self.logger.error(f"Error al iniciar el sistema: {str(e)}", exc_info=True)
                self._state = SystemState.ERROR
                
                # Emitir evento de error
                if self.event_bus:
                    self.event_bus.emit("system:state_changed", {
                        "old_state": SystemState.INITIALIZING,
                        "new_state": SystemState.ERROR,
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e)
                    })
                
                return False
    
    async def stop(self):
        """
        Detiene el sistema completo de forma ordenada.
        
        Returns:
            True si la detención fue exitosa
        """
        with self._lock:
            if self._state == SystemState.STOPPED:
                self.logger.warning("El sistema ya está detenido")
                return True
            
            old_state = self._state
            self._state = SystemState.STOPPING
            
            # Emitir evento de apagado
            if self.event_bus:
                self.event_bus.emit("system:state_changed", {
                    "old_state": old_state,
                    "new_state": SystemState.STOPPING,
                    "timestamp": datetime.now().isoformat()
                })
            
            self.logger.info("Deteniendo el sistema...")
            
            try:
                # Detener monitoreo
                self._stop_monitoring()
                
                # Detener tareas en ejecución
                for task in self._tasks:
                    if not task.done():
                        task.cancel()
                
                # Detener componentes en orden inverso
                await self._shutdown_components()
                
                # Actualizar estado
                self._state = SystemState.STOPPED
                self._last_update = datetime.now()
                
                # Emitir evento de sistema detenido
                if self.event_bus:
                    self.event_bus.emit("system:state_changed", {
                        "old_state": SystemState.STOPPING,
                        "new_state": SystemState.STOPPED,
                        "timestamp": self._last_update.isoformat()
                    })
                
                self.logger.info("Sistema detenido correctamente")
                return True
                
            except Exception as e:
                self.logger.error(f"Error al detener el sistema: {str(e)}", exc_info=True)
                self._state = SystemState.ERROR
                
                # Emitir evento de error
                if self.event_bus:
                    self.event_bus.emit("system:state_changed", {
                        "old_state": SystemState.STOPPING,
                        "new_state": SystemState.ERROR,
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e)
                    })
                
                return False
    
    async def restart(self):
        """
        Reinicia el sistema completo.
        
        Returns:
            True si el reinicio fue exitoso
        """
        self.logger.info("Reiniciando el sistema...")
        
        # Detener el sistema
        stop_success = await self.stop()
        if not stop_success:
            self.logger.error("Error al detener el sistema durante reinicio")
            return False
        
        # Esperar un momento para asegurar que todo se detuvo
        await asyncio.sleep(1)
        
        # Iniciar el sistema
        start_success = await self.start()
        if not start_success:
            self.logger.error("Error al iniciar el sistema durante reinicio")
            return False
        
        self.logger.info("Sistema reiniciado correctamente")
        return True
    
    async def _initialize_components(self):
        """
        Inicializa todos los componentes del sistema en orden.
        
        Raises:
            Exception: Si hay un error crítico en la inicialización
        """
        self.logger.info("Inicializando componentes del sistema...")
        
        # Orden de inicialización (de dependencias básicas a servicios de alto nivel)
        # Esto se podría obtener de configuración o definir dinámicamente
        initialization_order = [
            "telemetry_collector",
            "circuit_breaker",
            "interaction_manager",
            # Otros módulos se inicializarían aquí
        ]
        
        # Inicializar componentes en orden
        for component_name in initialization_order:
            try:
                if self.container.has(component_name):
                    component = self.container.get(component_name)
                    
                    # Si el componente tiene método start o initialize, llamarlo
                    if hasattr(component, 'start') and callable(component.start):
                        if asyncio.iscoroutinefunction(component.start):
                            await component.start()
                        else:
                            component.start()
                    elif hasattr(component, 'initialize') and callable(component.initialize):
                        if asyncio.iscoroutinefunction(component.initialize):
                            await component.initialize()
                        else:
                            component.initialize()
                    
                    # Registrar componente como iniciado
                    self._components[component_name] = {
                        "status": "running",
                        "initialized_at": datetime.now().isoformat(),
                        "errors": []
                    }
                    
                    self.logger.info(f"Componente {component_name} inicializado")
                else:
                    self.logger.warning(f"Componente {component_name} no encontrado en el container")
            
            except Exception as e:
                self.logger.error(f"Error al inicializar componente {component_name}: {str(e)}", exc_info=True)
                
                # Verificar si es un componente crítico
                if component_name in ["event_bus", "store", "config", "logger"]:
                    self.logger.critical(f"Error en componente crítico {component_name}, abortando inicialización")
                    raise
                else:
                    # Registrar error pero continuar
                    self._components[component_name] = {
                        "status": "error",
                        "error": str(e),
                        "initialized_at": datetime.now().isoformat(),
                        "errors": [{"timestamp": datetime.now().isoformat(), "error": str(e)}]
                    }
        
        self.logger.info("Todos los componentes inicializados")
    
    async def _shutdown_components(self):
        """
        Detiene todos los componentes del sistema en orden inverso.
        """
        self.logger.info("Deteniendo componentes del sistema...")
        
        # Usar el orden inverso al de inicialización
        shutdown_order = [
            # Servicios de alto nivel primero
            "interaction_manager",
            "circuit_breaker",
            "telemetry_collector",
            # Dependencias básicas al final
        ]
        
        # Detener componentes en orden
        for component_name in shutdown_order:
            try:
                if component_name in self._components and self.container.has(component_name):
                    component = self.container.get(component_name)
                    
                    # Si el componente tiene método stop o shutdown, llamarlo
                    if hasattr(component, 'stop') and callable(component.stop):
                        if asyncio.iscoroutinefunction(component.stop):
                            await component.stop()
                        else:
                            component.stop()
                    elif hasattr(component, 'shutdown') and callable(component.shutdown):
                        if asyncio.iscoroutinefunction(component.shutdown):
                            await component.shutdown()
                        else:
                            component.shutdown()
                    
                    # Actualizar estado del componente
                    self._components[component_name]["status"] = "stopped"
                    self._components[component_name]["stopped_at"] = datetime.now().isoformat()
                    
                    self.logger.info(f"Componente {component_name} detenido")
            
            except Exception as e:
                self.logger.error(f"Error al detener componente {component_name}: {str(e)}", exc_info=True)
                
                # Registrar error pero continuar
                if component_name in self._components:
                    self._components[component_name]["status"] = "error"
                    self._components[component_name]["error"] = str(e)
                    self._components[component_name]["errors"].append({
                        "timestamp": datetime.now().isoformat(),
                        "error": f"Error al detener: {str(e)}"
                    })
        
        self.logger.info("Todos los componentes detenidos")
    
    def _start_monitoring(self):
        """Inicia el monitoreo periódico del sistema."""
        if self._monitoring:
            return
        
        self._monitoring = True
        
        # Crear tarea de monitoreo
        monitor_task = asyncio.create_task(self._monitor_loop())
        self._tasks.append(monitor_task)
        
        self.logger.debug("Monitoreo del sistema iniciado")
    
    def _stop_monitoring(self):
        """Detiene el monitoreo periódico del sistema."""
        self._monitoring = False
        self.logger.debug("Monitoreo del sistema detenido")
    
    async def _monitor_loop(self):
        """Bucle de monitoreo del sistema."""
        try:
            while self._monitoring:
                # Ejecutar monitoreo
                await self._check_system_health()
                
                # Registrar métricas
                self._collect_system_metrics()
                
                # Esperar hasta el próximo ciclo
                await asyncio.sleep(self._monitoring_interval)
        except asyncio.CancelledError:
            self.logger.debug("Tarea de monitoreo cancelada")
        except Exception as e:
            self.logger.error(f"Error en bucle de monitoreo: {str(e)}", exc_info=True)
            # Reintentar después de un tiempo
            if self._monitoring:
                await asyncio.sleep(self._monitoring_interval * 2)
                asyncio.create_task(self._monitor_loop())
    
    async def _check_system_health(self):
        """
        Verifica la salud de todos los componentes del sistema.
        """
        # Verificar componentes con problemas
        error_components = []
        for name, info in self._components.items():
            if info["status"] == "error":
                error_components.append(name)
        
        # Verificar si el sistema está degradado
        old_state = self._state
        if error_components and self._state == SystemState.RUNNING:
            self._state = SystemState.DEGRADED
            self.logger.warning(f"Sistema en estado degradado. Componentes con error: {', '.join(error_components)}")
            
            # Emitir evento de cambio de estado
            if self.event_bus:
                self.event_bus.emit("system:state_changed", {
                    "old_state": old_state,
                    "new_state": self._state,
                    "timestamp": datetime.now().isoformat(),
                    "error_components": error_components
                })
            
            # Intentar recuperar componentes con error
            for component_name in error_components:
                await self._try_recover_component(component_name)
        
        # Verificar si el sistema se ha recuperado
        elif not error_components and self._state == SystemState.DEGRADED:
            self._state = SystemState.RUNNING
            self.logger.info("Sistema recuperado, volviendo a estado normal")
            
            # Emitir evento de cambio de estado
            if self.event_bus:
                self.event_bus.emit("system:state_changed", {
                    "old_state": old_state,
                    "new_state": self._state,
                    "timestamp": datetime.now().isoformat()
                })
    
    async def _try_recover_component(self, component_name: str) -> bool:
        """
        Intenta recuperar un componente con error.
        
        Args:
            component_name: Nombre del componente a recuperar
            
        Returns:
            True si la recuperación fue exitosa
        """
        self.logger.info(f"Intentando recuperar componente: {component_name}")
        
        try:
            # Verificar política de reintentos
            component_info = self._components[component_name]
            error_count = len(component_info.get("errors", []))
            
            # Si hay demasiados errores, no reintentar
            max_retries = self.config.get("system.recovery.max_retries", 3)
            if error_count > max_retries:
                self.logger.warning(
                    f"Componente {component_name} ha superado el máximo de reintentos ({max_retries}), "
                    f"no se intentará recuperar automáticamente"
                )
                return False
            
            # Obtener instancia del componente
            if not self.container.has(component_name):
                self.logger.error(f"No se puede recuperar {component_name}, no está en el container")
                return False
            
            component = self.container.get(component_name)
            
            # Intentar reiniciar el componente
            if hasattr(component, 'restart') and callable(component.restart):
                if asyncio.iscoroutinefunction(component.restart):
                    success = await component.restart()
                else:
                    success = component.restart()
                
                if success:
                    # Actualizar estado
                    self._components[component_name]["status"] = "running"
                    self._components[component_name]["recovered_at"] = datetime.now().isoformat()
                    self.logger.info(f"Componente {component_name} recuperado exitosamente")
                    return True
            
            # Si no tiene método restart, intentar stop + start
            elif (hasattr(component, 'stop') and callable(component.stop) and
                  hasattr(component, 'start') and callable(component.start)):
                
                # Detener componente
                if asyncio.iscoroutinefunction(component.stop):
                    await component.stop()
                else:
                    component.stop()
                
                # Pequeña pausa
                await asyncio.sleep(0.5)
                
                # Iniciar componente
                if asyncio.iscoroutinefunction(component.start):
                    await component.start()
                else:
                    component.start()
                
                # Actualizar estado
                self._components[component_name]["status"] = "running"
                self._components[component_name]["recovered_at"] = datetime.now().isoformat()
                self.logger.info(f"Componente {component_name} reiniciado exitosamente")
                return True
            
            else:
                self.logger.warning(
                    f"No se puede recuperar {component_name}, no tiene métodos restart o start/stop"
                )
                return False
            
        except Exception as e:
            self.logger.error(f"Error al recuperar componente {component_name}: {str(e)}", exc_info=True)
            
            # Registrar error
            self._components[component_name]["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "error": f"Error al recuperar: {str(e)}"
            })
            
            return False
    
    def _collect_system_metrics(self):
        """
        Recopila métricas del sistema y las emite.
        """
        try:
            # Obtener métricas del proceso
            process = psutil.Process(os.getpid())
            
            # CPU
            cpu_percent = process.cpu_percent(interval=0.1)
            
            # Memoria
            memory_info = process.memory_info()
            memory_used_mb = memory_info.rss / (1024 * 1024)  # Convertir a MB
            
            # Tiempo de ejecución
            if self._start_time:
                uptime_seconds = (datetime.now() - self._start_time).total_seconds()
            else:
                uptime_seconds = 0
            
            # Crear diccionario de métricas
            metrics = {
                "cpu_percent": cpu_percent,
                "memory_used_mb": memory_used_mb,
                "uptime_seconds": uptime_seconds,
                "component_count": len(self._components),
                "error_components": sum(1 for c in self._components.values() if c["status"] == "error"),
                "system_state": self._state,
                "timestamp": datetime.now().isoformat()
            }
            
            # Guardar métricas en el store
            current_time = int(time.time())
            self.store.set(f"system.metrics.{current_time}", metrics)
            
            # Emitir eventos con métricas
            if self.event_bus:
                # Evento de uso de CPU
                self.event_bus.emit("system:cpu_usage", {
                    "cpu_percent": cpu_percent,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Evento de uso de memoria
                self.event_bus.emit("system:memory_usage", {
                    "memory_used_mb": memory_used_mb,
                    "memory_total_mb": psutil.virtual_memory().total / (1024 * 1024),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Evento de métricas completas cada minuto
                if current_time % 60 == 0:
                    self.event_bus.emit("system:metrics", metrics)
            
        except Exception as e:
            self.logger.error(f"Error al recopilar métricas del sistema: {str(e)}")
    
    def get_system_state(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del sistema.
        
        Returns:
            Diccionario con información detallada del estado
        """
        # Métricas actuales
        try:
            process = psutil.Process(os.getpid())
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_used_mb = memory_info.rss / (1024 * 1024)
        except Exception:
            cpu_percent = 0
            memory_used_mb = 0
        
        # Calcular tiempo de ejecución
        if self._start_time:
            uptime_seconds = (datetime.now() - self._start_time).total_seconds()
            uptime_str = str(timedelta(seconds=int(uptime_seconds)))
        else:
            uptime_seconds = 0
            uptime_str = "00:00:00"
        
        # Estado general
        state = {
            "state": self._state,
            "uptime_seconds": uptime_seconds,
            "uptime": uptime_str,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "cpu_percent": cpu_percent,
            "memory_used_mb": memory_used_mb,
            "component_count": len(self._components),
            "components": {name: info.copy() for name, info in self._components.items()},
            "timestamp": datetime.now().isoformat()
        }
        
        return state
    
    def register_component(self, name: str, component: Any) -> bool:
        """
        Registra un componente en el sistema.
        
        Args:
            name: Nombre único del componente
            component: Instancia del componente
            
        Returns:
            True si se registró correctamente
        """
        with self._lock:
            # Registrar en el container
            self.container.register(name, component)
            
            # Inicializar estado
            self._components[name] = {
                "status": "registered",
                "registered_at": datetime.now().isoformat(),
                "errors": []
            }
            
            self.logger.debug(f"Componente {name} registrado en el sistema")
            return True
    
    def get_component_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información sobre un componente.
        
        Args:
            name: Nombre del componente
            
        Returns:
            Diccionario con información o None si no existe
        """
        return self._components.get(name)
    
    def get_component_names(self) -> List[str]:
        """
        Obtiene la lista de nombres de componentes registrados.
        
        Returns:
            Lista de nombres de componentes
        """
        return list(self._components.keys())