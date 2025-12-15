"""
SUME DOCBLOCK

Nombre: Telemetry Collector
Tipo: Lógica

Entradas:
- Eventos del sistema
- Métricas de rendimiento
- Registros de interacción
- Datos de latencia y throughput
- Umbrales de alertas configurables
- Patrones de detección de anomalías

Acciones:
- Recopilar métricas en tiempo real
- Agregar datos por dimensiones (módulo, tiempo)
- Calcular estadísticas (percentiles, promedios)
- Detectar anomalías y tendencias
- Emitir alertas basadas en umbrales
- Persistir datos históricos para análisis
- Filtrar y procesar eventos para observabilidad
- Facilitar diagnóstico de problemas

Salidas:
- Métricas agregadas en Store
- Eventos de alerta
- Datos para dashboard de observabilidad
- Exportación a sistemas externos
- Informes periódicos de salud del sistema
"""
import time
import statistics
import math
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set, Union, Callable
from enum import Enum


class AlertSeverity(Enum):
    """Niveles de severidad para alertas."""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Tipos de alertas que puede generar el sistema."""
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    HIGH_LATENCY = "high_latency"
    ERROR_RATE = "error_rate"
    CIRCUIT_OPEN = "circuit_open"
    COMPONENT_ERROR = "component_error"
    SYSTEM_DEGRADED = "system_degraded"
    ANOMALY_DETECTED = "anomaly_detected"
    TIMEOUT_SPIKE = "timeout_spike"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SECURITY_VIOLATION = "security_violation"


class TelemetryCollector:
    """
    Recopilador y procesador de telemetría del sistema.
    
    Proporciona una visión completa del funcionamiento interno del sistema,
    permitiendo detectar problemas, anomalías y cuellos de botella.
    """
    
    def __init__(self, event_bus, store, logger=None, config=None):
        """
        Inicializa el colector de telemetría.
        
        Args:
            event_bus: EventBus para recibir y emitir eventos
            store: Store para almacenar métricas
            logger: Logger para registro de actividad (opcional)
            config: Configuración del sistema (opcional)
        """
        self.event_bus = event_bus
        self.store = store
        self.logger = logger or logging.getLogger(__name__)
        self.config = config or {}
        
        # Buffers para métricas en tiempo real
        self.metrics_buffer: Dict[str, List[float]] = {}
        
        # Contadores acumulativos
        self.counters: Dict[str, int] = {}
        
        # Último valor de cada métrica
        self.last_values: Dict[str, Any] = {}
        
        # Umbrales para alertas
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        
        # Estado de alertas para evitar duplicados
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        
        # Registro de anomalías detectadas
        self.anomalies: List[Dict[str, Any]] = []
        
        # Intervalos de agregación (segundos)
        self.aggregation_intervals = {
            "realtime": 10,     # 10 segundos
            "minute": 60,       # 1 minuto
            "hour": 3600,       # 1 hora
            "day": 86400        # 1 día
        }
        
        # Última ejecución de cada agregación
        self.last_aggregation: Dict[str, float] = {
            interval: 0 for interval in self.aggregation_intervals
        }
        
        # Modelos de detección de anomalías
        self.anomaly_models: Dict[str, Dict[str, Any]] = {}
        
        # Tareas de procesamiento
        self.tasks = []
        
        # Indicador de si está en ejecución
        self.running = False
        
        # Cargar configuración
        self._load_config()
        
        self.logger.debug("TelemetryCollector inicializado")
    
    def _load_config(self):
        """Carga configuración inicial y umbrales."""
        # Valores por defecto
        default_thresholds = {
            "cpu.percent": {"warning": 70, "critical": 90},
            "memory.percent": {"warning": 80, "critical":
            95},
            "latency.interaction": {"warning": 1000, "critical": 5000},  # ms
            "error.rate": {"warning": 0.05, "critical": 0.2},  # 5% y 20%
        }
        
        # Cargar de configuración si existe
        if self.config:
            thresholds_config = self.config.get("telemetry", {}).get("thresholds", {})
            for metric, values in thresholds_config.items():
                self.alert_thresholds[metric] = values
        
        # Aplicar valores por defecto para métricas no configuradas
        for metric, values in default_thresholds.items():
            if metric not in self.alert_thresholds:
                self.alert_thresholds[metric] = values
        
        self.logger.debug(f"Umbrales de alerta cargados: {len(self.alert_thresholds)} métricas configuradas")
    
    async def start(self):
        """
        Inicia el colector de telemetría.
        
        Returns:
            True si se inició correctamente
        """
        if self.running:
            self.logger.warning("TelemetryCollector ya está en ejecución")
            return False
        
        self.logger.info("Iniciando TelemetryCollector...")
        
        try:
            # Registrar manejadores de eventos
            self._register_event_handlers()
            
            # Iniciar tareas de procesamiento
            self._start_processing_tasks()
            
            # Marcar como en ejecución
            self.running = True
            
            self.logger.info("TelemetryCollector iniciado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al iniciar TelemetryCollector: {str(e)}", exc_info=True)
            return False
    
    async def stop(self):
        """
        Detiene el colector de telemetría.
        
        Returns:
            True si se detuvo correctamente
        """
        if not self.running:
            return True
        
        self.logger.info("Deteniendo TelemetryCollector...")
        
        try:
            # Marcar como no en ejecución
            self.running = False
            
            # Cancelar tareas de procesamiento
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Esperar a que terminen las tareas
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Limpiar lista de tareas
            self.tasks = []
            
            self.logger.info("TelemetryCollector detenido correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al detener TelemetryCollector: {str(e)}", exc_info=True)
            return False
    
    def _register_event_handlers(self):
        """Registra manejadores para eventos del sistema."""
        # Eventos generales del sistema
        self.event_bus.on("system:state_changed", self._handle_system_state)
        self.event_bus.on("system:metrics", self._handle_system_metrics)
        self.event_bus.on("system:cpu_usage", self._handle_cpu_usage)
        self.event_bus.on("system:memory_usage", self._handle_memory_usage)
        
        # Eventos de componentes
        self.event_bus.on("module:interaction_error", self._handle_interaction_error)
        self.event_bus.on("circuit:state_change", self._handle_circuit_state)
        
        # Eventos de telemetría específicos
        self.event_bus.on("telemetry:interaction", self._handle_interaction_telemetry)
        self.event_bus.on("telemetry:latency", self._handle_latency)
        
        # Comodín para capturar todos los eventos relevantes para métricas
        self.event_bus.on("metrics:*", self._handle_generic_metric)
        
        self.logger.debug("Manejadores de eventos registrados para telemetría")
    
    def _start_processing_tasks(self):
        """Inicia tareas asíncronas de procesamiento."""
        # Tarea de agregación de métricas
        aggregation_task = asyncio.create_task(self._aggregation_loop())
        self.tasks.append(aggregation_task)
        
        # Tarea de detección de anomalías
        anomaly_task = asyncio.create_task(self._anomaly_detection_loop())
        self.tasks.append(anomaly_task)
        
        # Tarea de mantenimiento (limpieza de datos antiguos)
        maintenance_task = asyncio.create_task(self._maintenance_loop())
        self.tasks.append(maintenance_task)
        
        self.logger.debug(f"Iniciadas {len(self.tasks)} tareas de procesamiento de telemetría")
    
    async def _aggregation_loop(self):
        """Bucle de agregación de métricas."""
        try:
            while self.running:
                # Obtener tiempo actual
                current_time = time.time()
                
                # Verificar cada intervalo de agregación
                for interval_name, interval_seconds in self.aggregation_intervals.items():
                    # Si pasó suficiente tiempo desde la última agregación
                    if current_time - self.last_aggregation[interval_name] >= interval_seconds:
                        # Realizar agregación
                        await self._aggregate_metrics(interval_name, interval_seconds)
                        
                        # Actualizar timestamp de última agregación
                        self.last_aggregation[interval_name] = current_time
                
                # Esperar antes del siguiente ciclo (cada 1 segundo)
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            self.logger.debug("Tarea de agregación de métricas cancelada")
        except Exception as e:
            self.logger.error(f"Error en bucle de agregación: {str(e)}", exc_info=True)
    
    async def _anomaly_detection_loop(self):
        """Bucle de detección de anomalías."""
        try:
            # Esperar 30 segundos iniciales para recopilar suficientes datos
            await asyncio.sleep(30)
            
            while self.running:
                # Analizar métricas en busca de anomalías
                await self._detect_anomalies()
                
                # Esperar antes del siguiente ciclo (cada 10 segundos)
                await asyncio.sleep(10)
                
        except asyncio.CancelledError:
            self.logger.debug("Tarea de detección de anomalías cancelada")
        except Exception as e:
            self.logger.error(f"Error en bucle de detección de anomalías: {str(e)}", exc_info=True)
    
    async def _maintenance_loop(self):
        """Bucle de mantenimiento para limpieza de datos antiguos."""
        try:
            # Ejecutar una vez al día
            while self.running:
                # Limpiar datos antiguos
                await self._clean_old_data()
                
                # Esperar 24 horas
                await asyncio.sleep(86400)  # 24 horas
                
        except asyncio.CancelledError:
            self.logger.debug("Tarea de mantenimiento cancelada")
        except Exception as e:
            self.logger.error(f"Error en bucle de mantenimiento: {str(e)}", exc_info=True)
    
    async def _aggregate_metrics(self, interval_name: str, interval_seconds: int):
        """
        Agrega métricas para un intervalo específico.
        
        Args:
            interval_name: Nombre del intervalo (realtime, minute, hour, day)
            interval_seconds: Duración del intervalo en segundos
        """
        try:
            # Fecha/hora actual
            current_time = time.time()
            timestamp = datetime.utcnow().isoformat()
            
            # Punto de inicio del intervalo
            start_time = current_time - interval_seconds
            
            # Procesar cada grupo de métricas
            for metric_name, values in self.metrics_buffer.items():
                # Filtrar valores para este intervalo
                # (Para simplificar, usamos todos los valores disponibles)
                if not values:
                    continue
                
                # Calcular estadísticas
                stats = self._calculate_statistics(values)
                
                # Guardar en el store
                store_key = f"metrics.{interval_name}.{metric_name}.{int(current_time)}"
                self.store.set(store_key, {
                    "timestamp": timestamp,
                    "interval": interval_name,
                    "metric": metric_name,
                    "stats": stats
                })
                
                # Para intervalos mayores a realtime, limpiar el buffer
                if interval_name != "realtime":
                    self.metrics_buffer[metric_name] = []
                
                # Verificar umbrales para alertas
                self._check_thresholds(metric_name, stats)
            
        except Exception as e:
            self.logger.error(f"Error al agregar métricas para intervalo {interval_name}: {str(e)}")
    
    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """
        Calcula estadísticas para un conjunto de valores.
        
        Args:
            values: Lista de valores numéricos
            
        Returns:
            Diccionario con estadísticas calculadas
        """
        if not values:
            return {"count": 0}
        
        # Ordenar valores para percentiles
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        # Estadísticas básicas
        stats = {
            "count": count,
            "min": min(sorted_values),
            "max": max(sorted_values),
            "sum": sum(sorted_values),
            "mean": statistics.mean(sorted_values)
        }
        
        # Estadísticas adicionales si hay suficientes datos
        if count > 1:
            stats["stddev"] = statistics.stdev(sorted_values)
            stats["variance"] = statistics.variance(sorted_values)
        
        # Percentiles
        if count >= 4:
            stats["median"] = statistics.median(sorted_values)
            stats["p25"] = sorted_values[int(count * 0.25)]
            stats["p75"] = sorted_values[int(count * 0.75)]
            stats["p90"] = sorted_values[int(count * 0.9)]
        
        if count >= 10:
            stats["p95"] = sorted_values[int(count * 0.95)]
            stats["p99"] = sorted_values[int(count * 0.99)]
        
        return stats
    
    def _check_thresholds(self, metric_name: str, stats: Dict[str, float]):
        """
        Verifica si las estadísticas superan umbrales configurados.
        
        Args:
            metric_name: Nombre de la métrica
            stats: Estadísticas calculadas
        """
        # Verificar si hay umbrales para esta métrica
        for threshold_pattern, thresholds in self.alert_thresholds.items():
            # Comprobar si el patrón coincide con la métrica
            if self._match_metric_pattern(metric_name, threshold_pattern):
                # Determinar qué valor usar para comparación
                check_value = None
                
                # Por defecto usamos la media
                if "mean" in stats:
                    check_value = stats["mean"]
                # Para percentiles altos, si están disponibles
                elif "p95" in stats and threshold_pattern.startswith("latency."):
                    check_value = stats["p95"]
                # Para máximos
                elif "max" in stats and threshold_pattern.endswith(".max"):
                    check_value = stats["max"]
                
                if check_value is not None:
                    # Verificar umbral crítico
                    if "critical" in thresholds and check_value >= thresholds["critical"]:
                        self._emit_alert(
                            metric_name, 
                            check_value,
                            thresholds["critical"],
                            AlertSeverity.CRITICAL,
                            stats
                        )
                    # Verificar umbral de advertencia
                    elif "warning" in thresholds and check_value >= thresholds["warning"]:
                        self._emit_alert(
                            metric_name,
                            check_value,
                            thresholds["warning"],
                            AlertSeverity.WARNING,
                            stats
                        )
    
    def _match_metric_pattern(self, metric_name: str, pattern: str) -> bool:
        """
        Verifica si un nombre de métrica coincide con un patrón.
        
        Args:
            metric_name: Nombre de la métrica
            pattern: Patrón de coincidencia (puede incluir *)
            
        Returns:
            True si hay coincidencia
        """
        # Coincidencia exacta
        if pattern == metric_name:
            return True
        
        # Patrón con comodín al final
        if pattern.endswith("*") and metric_name.startswith(pattern[:-1]):
            return True
        
        # Patrón con comodín al inicio
        if pattern.startswith("*") and metric_name.endswith(pattern[1:]):
            return True
        
        # Patrón con comodín en medio
        if "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2 and metric_name.startswith(parts[0]) and metric_name.endswith(parts[1]):
                return True
        
        return False
    
    def _emit_alert(self, metric_name: str, value: float, threshold: float, 
                   severity: AlertSeverity, stats: Dict[str, float] = None):
        """
        Emite una alerta si es necesario.
        
        Args:
            metric_name: Nombre de la métrica
            value: Valor actual
            threshold: Umbral superado
            severity: Severidad de la alerta
            stats: Estadísticas adicionales (opcional)
        """
        # Determinar tipo de alerta
        alert_type = None
        if metric_name.startswith("cpu"):
            alert_type = AlertType.HIGH_CPU
        elif metric_name.startswith("memory"):
            alert_type = AlertType.HIGH_MEMORY
        elif metric_name.startswith("latency"):
            alert_type = AlertType.HIGH_LATENCY
        elif metric_name.startswith("error"):
            alert_type = AlertType.ERROR_RATE
        else:
            alert_type = AlertType.ANOMALY_DETECTED
        
        # Clave única para evitar duplicados
        alert_key = f"{alert_type.value}:{metric_name}"
        
        # Verificar si ya existe una alerta activa de este tipo
        if alert_key in self.active_alerts:
            # Si existe, verificar si podemos emitir de nuevo
            last_alert = self.active_alerts[alert_key]
            
            # No emitir la misma alerta más de una vez cada 5 minutos
            # excepto si aumenta de severidad
            time_since_last = time.time() - last_alert["timestamp"]
            if (time_since_last < 300 and  # 5 minutos
                last_alert["severity"] == severity.value):
                return
            
            # Si es la misma severidad pero ha empeorado significativamente (50% más)
            # también emitir alerta
            if (last_alert["severity"] == severity.value and
                time_since_last < 300 and
                value < last_alert["value"] * 1.5):
                return
        
        # Preparar datos de la alerta
        current_time = time.time()
        timestamp = datetime.utcnow().isoformat()
        
        alert_data = {
            "type": alert_type.value,
            "severity": severity.value,
            "metric": metric_name,
            "value": value,
            "threshold": threshold,
            "message": self._format_alert_message(alert_type, metric_name, value, threshold, severity),
            "timestamp": current_time,
            "datetime": timestamp
        }
        
        # Añadir estadísticas si están disponibles
        if stats:
            alert_data["stats"] = stats
        
        # Guardar como alerta activa
        self.active_alerts[alert_key] = alert_data
        
        # Guardar en el store para historial
        alert_id = f"{int(current_time)}-{alert_key}"
        self.store.set(f"alerts.{alert_id}", alert_data)
        
        # Emitir evento de alerta
        self.event_bus.emit("system:alert", alert_data)
        
        # Log según severidad
        if severity == AlertSeverity.CRITICAL:
            self.logger.critical(alert_data["message"])
        elif severity == AlertSeverity.ERROR:
            self.logger.error(alert_data["message"])
        elif severity == AlertSeverity.WARNING:
            self.logger.warning(alert_data["message"])
        else:
            self.logger.info(alert_data["message"])
    
    def _format_alert_message(self, alert_type: AlertType, metric_name: str, 
                             value: float, threshold: float, severity: AlertSeverity) -> str:
        """
        Formatea un mensaje de alerta legible.
        
        Args:
            alert_type: Tipo de alerta
            metric_name: Nombre de la métrica
            value: Valor actual
            threshold: Umbral superado
            severity: Severidad de la alerta
            
        Returns:
            Mensaje formateado
        """
        # Determinar nivel en texto
        level_text = severity.value.upper()
        
        # Formatear valores según el tipo de métrica
        if metric_name.startswith("latency"):
            value_text = f"{value:.2f}ms"
            threshold_text = f"{threshold:.2f}ms"
        elif metric_name.endswith("percent"):
            value_text = f"{value:.1f}%"
            threshold_text = f"{threshold:.1f}%"
        elif metric_name.startswith("error.rate"):
            value_text = f"{value*100:.2f}%"
            threshold_text = f"{threshold*100:.2f}%"
        else:
            value_text = f"{value:.2f}"
            threshold_text = f"{threshold:.2f}"
        
        # Mensajes específicos por tipo de alerta
        if alert_type == AlertType.HIGH_CPU:
            return f"{level_text}: Alto uso de CPU - {value_text} (umbral: {threshold_text})"
        elif alert_type == AlertType.HIGH_MEMORY:
            return f"{level_text}: Alto uso de memoria - {value_text} (umbral: {threshold_text})"
        elif alert_type == AlertType.HIGH_LATENCY:
            return f"{level_text}: Latencia elevada en {metric_name} - {value_text} (umbral: {threshold_text})"
        elif alert_type == AlertType.ERROR_RATE:
            return f"{level_text}: Tasa de errores elevada - {value_text} (umbral: {threshold_text})"
        elif alert_type == AlertType.ANOMALY_DETECTED:
            return f"{level_text}: Anomalía detectada en {metric_name} - {value_text} (umbral: {threshold_text})"
        else:
            return f"{level_text}: Alerta en {metric_name} - {value_text} (umbral: {threshold_text})"
    
    async def _detect_anomalies(self):
        """Detecta anomalías en las métricas recopiladas."""
        try:
            # Para cada métrica con suficientes datos
            for metric_name, values in self.metrics_buffer.items():
                if len(values) < 30:  # Necesitamos suficientes datos
                    continue
                
                # Inicializar o actualizar modelo para la métrica
                if metric_name not in self.anomaly_models:
                    self.anomaly_models[metric_name] = self._initialize_anomaly_model(values)
                else:
                    # Actualizar modelo con nuevos datos cada 10 minutos
                    model = self.anomaly_models[metric_name]
                    if time.time() - model["last_update"] > 600:  # 10 minutos
                        model = self._update_anomaly_model(model, values)
                        self.anomaly_models[metric_name] = model
                
                # Obtener modelo actual
                model = self.anomaly_models[metric_name]
                
                # Detectar anomalías en los datos recientes
                recent_values = values[-10:]  # Últimos 10 valores
                for value in recent_values:
                    is_anomaly, score = self._check_anomaly(value, model)
                    if is_anomaly:
                        # Registrar anomalía
                        anomaly = {
                            "metric": metric_name,
                            "value": value,
                            "score": score,
                            "timestamp": time.time(),
                            "threshold": model["threshold"],
                            "model_stats": {
                                "mean": model["mean"],
                                "stddev": model["stddev"]
                            }
                        }
                        self.anomalies.append(anomaly)
                        
                        # Guardar en el store
                        anomaly_id = f"anomaly.{metric_name}.{int(time.time())}"
                        self.store.set(anomaly_id, anomaly)
                        
                        # Emitir evento de anomalía
                        self.event_bus.emit("telemetry:anomaly_detected", anomaly)
                        
                        # Emitir alerta si es una anomalía significativa
                        if score > model["threshold"] * 2:  # Anomalía severa
                            self._emit_alert(
                                metric_name,
                                value,
                                model["threshold"],
                                AlertSeverity.ERROR,
                                {"anomaly_score": score}
                            )
                        else:
                            self._emit_alert(
                                metric_name,
                                value,
                                model["threshold"],
                                AlertSeverity.WARNING,
                                {"anomaly_score": score}
                            )
        
        except Exception as e:
            self.logger.error(f"Error en detección de anomalías: {str(e)}", exc_info=True)
    
    def _initialize_anomaly_model(self, values: List[float]) -> Dict[str, Any]:
        """
        Inicializa un modelo simple para detección de anomalías.
        
        Args:
            values: Lista de valores históricos
            
        Returns:
            Diccionario con el modelo
        """
        # Para este ejemplo, usamos un modelo simple basado en media y desviación estándar
        # En un sistema real, podría ser un modelo más sofisticado
        
        mean = statistics.mean(values)
        stddev = statistics.stdev(values) if len(values) > 1 else 0.1 * mean
        
        # El umbral es típicamente un múltiplo de la desviación estándar
        threshold = 3.0 * stddev
        
        return {
            "mean": mean,
            "stddev": stddev,
            "threshold": threshold,
            "last_update": time.time()
        }
    
    def _update_anomaly_model(self, model: Dict[str, Any], new_values: List[float]) -> Dict[str, Any]:
        """
        Actualiza un modelo de anomalías con nuevos datos.
        
        Args:
            model: Modelo existente
            new_values: Nuevos valores
            
        Returns:
            Modelo actualizado
        """
        # Actualización simple con ponderación entre modelo anterior y nuevos datos
        weight_old = 0.7  # 70% peso para datos históricos
        weight_new = 0.3  # 30% peso para nuevos datos
        
        new_mean = statistics.mean(new_values)
        new_stddev = statistics.stdev(new_values) if len(new_values) > 1 else 0.1 * new_mean
        
        updated_mean = (model["mean"] * weight_old) + (new_mean * weight_new)
        updated_stddev = (model["stddev"] * weight_old) + (new_stddev * weight_new)
        updated_threshold = 3.0 * updated_stddev
        
        return {
            "mean": updated_mean,
            "stddev": updated_stddev,
            "threshold": updated_threshold,
            "last_update": time.time()
        }
    
    def _check_anomaly(self, value: float, model: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Verifica si un valor es una anomalía según el modelo.
        
        Args:
            value: Valor a verificar
            model: Modelo de anomalías
            
        Returns:
            Tupla (es_anomalía, puntuación)
        """
        # Calcular Z-score: cuántas desviaciones estándar del valor a la media
        if model["stddev"] == 0:
            z_score = 0
        else:
            z_score = abs(value - model["mean"]) / model["stddev"]
        
        # Determinar si es anomalía
        is_anomaly = z_score > 3.0  # Típicamente 3 sigmas
        
        return is_anomaly, z_score
    
    async def _clean_old_data(self):
        """Limpia datos antiguos para evitar crecimiento indefinido."""
        try:
            # Limpiar buffer de métricas
            # Mantener solo hasta cierta cantidad por métrica
            max_buffer_size = 1000  # Máximo 1000 valores por métrica
            for metric_name in self.metrics_buffer:
                if len(self.metrics_buffer[metric_name]) > max_buffer_size:
                    # Mantener solo los más recientes
                    self.metrics_buffer[metric_name] = self.metrics_buffer[metric_name][-max_buffer_size:]
            
            # Limpiar historial de anomalías
            # Mantener solo las últimas 100
            if len(self.anomalies) > 100:
                self.anomalies = self.anomalies[-100:]
            
            # Limpiar alertas activas antiguas
            current_time = time.time()
            keys_to_remove = []
            for key, alert in self.active_alerts.items():
                # Limpiar alertas con más de 24 horas
                if current_time - alert["timestamp"] > 86400:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.active_alerts[key]
            
            self.logger.debug("Limpieza de datos antiguos completada")
        
        except Exception as e:
            self.logger.error(f"Error en limpieza de datos antiguos: {str(e)}")
    
    # Manejadores de eventos
    def _handle_system_state(self, data: Dict[str, Any], event_name: str):
        """Maneja eventos de cambio de estado del sistema."""
        new_state = data.get("new_state")
        old_state = data.get("old_state")
        
        # Registrar cambio de estado
        self.store.set(f"system.state.{int(time.time())}", data)
        
        # Verificar transición a estado degradado
        if new_state == "degraded" and old_state in ("running", "initializing"):
            # Emitir alerta
            alert_data = {
                "type": AlertType.SYSTEM_DEGRADED.value,
                "severity": AlertSeverity.ERROR.value,
                "message": f"Sistema en estado degradado",
                "details": data.get("error_components", []),
                "timestamp": time.time(),
                "datetime": datetime.utcnow().isoformat()
            }
            
            # Emitir evento de alerta
            self.event_bus.emit("system:alert", alert_data)
            
            # Log
            self.logger.error(f"Sistema en estado degradado. Componentes afectados: {data.get('error_components')}")
    
    def _handle_system_metrics(self, data: Dict[str, Any], event_name: str):
        """Maneja eventos con métricas completas del sistema."""
        # Procesar cada métrica en el evento
        if "cpu_percent" in data:
            self._record_metric("cpu.percent", data["cpu_percent"])
        
        if "memory_used_mb" in data:
            self._record_metric("memory.used_mb", data["memory_used_mb"])
        
        if "uptime_seconds" in data:
            self._record_metric("system.uptime", data["uptime_seconds"])
        
        # Guardar métricas completas en el store
        self.store.set(f"system.metrics.{int(time.time())}", data)
    
    def _handle_cpu_usage(self, data: Dict[str, Any], event_name: str):
        """Maneja eventos específicos de uso de CPU."""
        if "cpu_percent" in data:
            self._record_metric("cpu.percent", data["cpu_percent"])
    
    def _handle_memory_usage(self, data: Dict[str, Any], event_name: str):
        """Maneja eventos específicos de uso de memoria."""
        if "memory_used_mb" in data:
            self._record_metric("memory.used_mb", data["memory_used_mb"])
        
        if "memory_total_mb" in data and data["memory_total_mb"] > 0:
            memory_percent = (data["memory_used_mb"] / data["memory_total_mb"]) * 100
            self._record_metric("memory.percent", memory_percent)
    
    def _handle_interaction_error(self, data: Dict[str, Any], event_name: str):
        """Maneja eventos de errores en interacciones entre módulos."""
        source = data.get("source", "unknown")
        target = data.get("target", "unknown")
        error_type = data.get("error_type", "unknown")
        
        # Incrementar contador de errores
        error_counter = f"error.{source}.{target}.{error_type}"
        self._increment_counter(error_counter)
        
        # Incrementar contador general
        self._increment_counter("error.total")
        
        # Calcular tasa de errores si hay datos suficientes
        source_target = f"{source}.{target}"
        
        # Contadores para rate
        success_key = f"success.{source_target}"
        error_key = f"error.{source_target}"
        
        success_count = self.counters.get(success_key, 0)
        error_count = self.counters.get(error_key, 0)
        total = success_count + error_count
        
        if total > 0:
            error_rate = error_count / total
            self._record_metric(f"error.rate.{source_target}", error_rate)
            
            # Verificar umbral de alerta
            if error_rate > 0.5 and total > 10:  # Más del 50% de errores con al menos 10 interacciones
                alert_data = {
                    "type": AlertType.ERROR_RATE.value,
                    "severity": AlertSeverity.ERROR.value,
                    "message": f"Alta tasa de errores entre {source} y {target}: {error_rate*100:.1f}%",
                    "error_rate": error_rate,
                    "error_type": error_type,
                    "source": source,
                    "target": target,
                    "timestamp": time.time(),
                    "datetime": datetime.utcnow().isoformat()
                }
                
                # Emitir evento de alerta
                self.event_bus.emit("system:alert", alert_data)
    
    def _handle_circuit_state(self, data: Dict[str, Any], event_name: str):
        """Maneja eventos de cambio de estado de circuit breakers."""
        circuit_id = data.get("circuit_id", "unknown")
        new_state = data.get("new_state", "unknown")
        
        # Guardar cambio de estado en el store
        self.store.set(f"circuit.state.{circuit_id}.{int(time.time())}", data)
        
        # Si cambia a estado abierto, emitir alerta
        if new_state == "open":
            # Extraer source/target del circuit_id
            parts = circuit_id.split(":")
            source = parts[0] if len(parts) > 0 else "unknown"
            target = parts[1] if len(parts) > 1 else "unknown"
            
            alert_data = {
                "type": AlertType.CIRCUIT_OPEN.value,
                "severity": AlertSeverity.ERROR.value,
                "message": f"Circuit breaker abierto entre {source} y {target}",
                "circuit_id": circuit_id,
                "source": source,
                "target": target,
                "timestamp": time.time(),
                "datetime": datetime.utcnow().isoformat()
            }
            
            # Emitir evento de alerta
            self.event_bus.emit("system:alert", alert_data)
            
            # Log
            self.logger.error(f"Circuit breaker abierto: {circuit_id}")
    
    def _handle_interaction_telemetry(self, data: Dict[str, Any], event_name: str):
        """Maneja telemetría específica de interacciones."""
        source = data.get("source", "unknown")
        target = data.get("target", "unknown")
        success = data.get("success", True)
        
        # Incrementar contadores
        if success:
            self._increment_counter(f"success.{source}.{target}")
            self._increment_counter("success.total")
        else:
            self._increment_counter(f"error.{source}.{target}")
            self._increment_counter("error.total")
        
        # Total de interacciones
        self._increment_counter(f"interaction.{source}.{target}")
        self._increment_counter("interaction.total")
        
        # Guardar en el store para análisis
        self.store.set(f"interaction.{source}.{target}.{int(time.time())}", data)
    
    def _handle_latency(self, data: Dict[str, Any], event_name: str):
        """Maneja telemetría de latencia."""
        source = data.get("source", "unknown")
        target = data.get("target", "unknown")
        duration_ms = data.get("duration_ms", 0)
        
        # Registrar métrica
        self._record_metric(f"latency.{source}.{target}", duration_ms)
        
        # Detectar latencia anómala de forma simple
        # (esto complementa la detección de anomalías más sofisticada)
        if duration_ms > 5000:  # Más de 5 segundos
            alert_data = {
                "type": AlertType.HIGH_LATENCY.value,
                "severity": AlertSeverity.WARNING.value,
                "message": f"Latencia elevada entre {source} y {target}: {duration_ms:.2f}ms",
                "duration_ms": duration_ms,
                "source": source,
                "target": target,
                "timestamp": time.time(),
                "datetime": datetime.utcnow().isoformat()
            }
            
            # Verificar si ya hay una alerta activa para esta interacción
            alert_key = f"high_latency:{source}.{target}"
            if alert_key not in self.active_alerts:
                # Emitir evento de alerta
                self.event_bus.emit("system:alert", alert_data)
                
                # Registrar como alerta activa
                self.active_alerts[alert_key] = alert_data
    
    def _handle_generic_metric(self, data: Dict[str, Any], event_name: str):
        """Maneja eventos genéricos de métricas."""
        # Extraer nombre de la métrica del evento
        metric_name = event_name.split(":")[-1]
        
        # Procesar cada valor numérico en el evento
        for key, value in data.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                # Registrar como métrica
                self._record_metric(f"{metric_name}.{key}", value)
    
    def _record_metric(self, name: str, value: float):
        """
        Registra una métrica para su procesamiento.
        
        Args:
            name: Nombre de la métrica
            value: Valor numérico
        """
        # Inicializar buffer si no existe
        if name not in self.metrics_buffer:
            self.metrics_buffer[name] = []
        
        # Añadir valor al buffer
        self.metrics_buffer[name].append(value)
        
        # Guardar último valor
        self.last_values[name] = value
    
    def _increment_counter(self, name: str, amount: int = 1):
        """
        Incrementa un contador.
        
        Args:
            name: Nombre del contador
            amount: Cantidad a incrementar
        """
        if name not in self.counters:
            self.counters[name] = 0
        
        self.counters[name] += amount
    
    def get_metrics(self, pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene métricas actuales.
        
        Args:
            pattern: Patrón para filtrar métricas (opcional)
            
        Returns:
            Diccionario con métricas
        """
        result = {}
        
        # Filtrar por patrón si se especificó
        if pattern:
            for name, value in self.last_values.items():
                if self._match_metric_pattern(name, pattern):
                    result[name] = value
        else:
            # Devolver todas las métricas
            result = self.last_values.copy()
        
        return result
    
    def get_counters(self, pattern: Optional[str] = None) -> Dict[str, int]:
        """
        Obtiene contadores actuales.
        
        Args:
            pattern: Patrón para filtrar contadores (opcional)
            
        Returns:
            Diccionario con contadores
        """
        result = {}
        
        # Filtrar por patrón si se especificó
        if pattern:
            for name, value in self.counters.items():
                if self._match_metric_pattern(name, pattern):
                    result[name] = value
        else:
            # Devolver todos los contadores
            result = self.counters.copy()
        
        return result
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Obtiene alertas activas.
        
        Returns:
            Lista de alertas activas
        """
        return list(self.active_alerts.values())
    
    def get_anomalies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene anomalías detectadas.
        
        Args:
            limit: Máximo número de anomalías a devolver
            
        Returns:
            Lista de anomalías
        """
        # Devolver las más recientes primero
        return sorted(
            self.anomalies,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
    
    def set_alert_threshold(self, metric_pattern: str, level: str, value: float):
        """
        Establece un umbral de alerta.
        
        Args:
            metric_pattern: Patrón de métrica
            level: Nivel (warning, critical)
            value: Valor umbral
        """
        if metric_pattern not in self.alert_thresholds:
            self.alert_thresholds[metric_pattern] = {}
        
        self.alert_thresholds[metric_pattern][level] = value
        self.logger.info(f"Umbral de alerta establecido: {metric_pattern}.{level} = {value}")
    
    def get_statistics(self, metric_name: str, interval: str = "realtime") -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas para una métrica específica.
        
        Args:
            metric_name: Nombre de la métrica
            interval: Intervalo de agregación (realtime, minute, hour, day)
            
        Returns:
            Diccionario con estadísticas o None si no hay datos
        """
        if metric_name not in self.metrics_buffer:
            return None
        
        # Para intervalo realtime, calcular sobre buffer actual
        if interval == "realtime":
            values = self.metrics_buffer[metric_name]
            if not values:
                return None
            
            stats = self._calculate_statistics(values)
            return {
                "metric": metric_name,
                "interval": interval,
                "timestamp": datetime.utcnow().isoformat(),
                "stats": stats
            }
        
        # Para otros intervalos, buscar en el store
        current_time = int(time.time())
        # Buscar la agregación más reciente
        pattern = f"metrics.{interval}.{metric_name}.*"
        metrics = self.store.get_many(pattern)
        
        if not metrics:
            return None
        
        # Devolver la más reciente
        latest_key = max(metrics.keys())
        return metrics[latest_key]
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Genera un informe completo del estado del sistema.
        
        Returns:
            Diccionario con el informe
        """
        # Métricas actuales
        current_metrics = self.get_metrics()
        
        # Contadores
        counters = self.get_counters()
        
        # Alertas activas
        alerts = self.get_active_alerts()
        
        # Anomalías recientes
        anomalies = self.get_anomalies(10)  # Últimas 10
        
        # Calcular estadísticas generales
        stats = {}
        for name, values in self.metrics_buffer.items():
            if len(values) > 5:  # Solo si hay suficientes datos
                stats[name] = self._calculate_statistics(values)
        
        # Compilar informe
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": current_metrics,
            "counters": counters,
            "stats": stats,
            "active_alerts": alerts,
            "recent_anomalies": anomalies,
            "system_health": self._assess_system_health()
        }
        
        # Guardar en el store
        self.store.set(f"reports.system.{int(time.time())}", report)
        
        return report
    
    def _assess_system_health(self) -> Dict[str, Any]:
        """
        Evalúa la salud general del sistema.
        
        Returns:
            Diccionario con evaluación de salud
        """
        # Nivel de salud (0-100)
        health_score = 100
        
        # Factores que afectan la salud
        factors = []
        
        # Verificar alertas activas
        critical_alerts = sum(1 for a in self.active_alerts.values() 
                           if a["severity"] == AlertSeverity.CRITICAL.value)
        error_alerts = sum(1 for a in self.active_alerts.values() 
                         if a["severity"] == AlertSeverity.ERROR.value)
        warning_alerts = sum(1 for a in self.active_alerts.values() 
                           if a["severity"] == AlertSeverity.WARNING.value)
        
        # Reducir puntuación según alertas
        if critical_alerts > 0:
            health_score -= min(50, critical_alerts * 20)  # Máximo -50 puntos
            factors.append(f"Alertas críticas: {critical_alerts}")
        
        if error_alerts > 0:
            health_score -= min(30, error_alerts * 10)  # Máximo -30 puntos
            factors.append(f"Alertas de error: {error_alerts}")
        
        if warning_alerts > 0:
            health_score -= min(20, warning_alerts * 5)  # Máximo -20 puntos
            factors.append(f"Alertas de advertencia: {warning_alerts}")
        
        # Verificar circuitos abiertos
        open_circuits = sum(1 for k in self.active_alerts.keys() 
                          if k.startswith("circuit_open:"))
        if open_circuits > 0:
            health_score -= min(40, open_circuits * 15)  # Máximo -40 puntos
            factors.append(f"Circuitos abiertos: {open_circuits}")
        
        # Verificar uso de recursos
        cpu_percent = self.last_values.get("cpu.percent", 0)
        if cpu_percent > 80:
            health_score -= min(30, (cpu_percent - 80) * 1.5)
            factors.append(f"CPU alta: {cpu_percent:.1f}%")
        
        memory_percent = self.last_values.get("memory.percent", 0)
        if memory_percent > 85:
            health_score -= min(30, (memory_percent - 85) * 2)
            factors.append(f"Memoria alta: {memory_percent:.1f}%")
        
        # Verificar tasa de errores
        error_rates = {k: v for k, v in self.last_values.items() if k.startswith("error.rate")}
        high_error_rates = sum(1 for v in error_rates.values() if v > 0.1)  # > 10% error
        if high_error_rates > 0:
            health_score -= min(40, high_error_rates * 10)
            factors.append(f"Tasas de error elevadas: {high_error_rates}")
        
        # Verificar anomalías recientes
        recent_anomalies = sum(1 for a in self.anomalies 
                             if time.time() - a["timestamp"] < 300)  # Últimos 5 minutos
        if recent_anomalies > 0:
            health_score -= min(20, recent_anomalies * 4)
            factors.append(f"Anomalías recientes: {recent_anomalies}")
        
        # Asegurar que no sea negativo
        health_score = max(0, health_score)
        
        # Determinar nivel de salud
        if health_score >= 90:
            health_level = "EXCELLENT"
        elif health_score >= 75:
            health_level = "GOOD"
        elif health_score >= 50:
            health_level = "FAIR"
        elif health_score >= 25:
            health_level = "POOR"
        else:
            health_level = "CRITICAL"
        
        return {
            "score": health_score,
            "level": health_level,
            "factors": factors
        }