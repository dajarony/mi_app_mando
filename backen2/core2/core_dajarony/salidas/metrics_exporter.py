# core_dajarony/salidas/metrics_exporter.py
"""
SUME DOCBLOCK

Nombre: Metrics Exporter
Tipo: Salida

Entradas:
- Métricas internas del sistema
- Configuración de exportación
- Destinos de exportación (Prometheus, StatsD, etc.)
- Intervalos y políticas de exportación

Acciones:
- Recopilar métricas de diferentes componentes
- Transformar métricas a formatos específicos
- Agregar y agrupar métricas según configuración
- Exportar a sistemas externos de monitoreo
- Manejar reintentos y errores de conexión

Salidas:
- Métricas exportadas a sistemas externos
- Confirmación de exportación exitosa
- Registro de errores y advertencias
- Metadatos de exportación
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

class ExportFormat(Enum):
    PROMETHEUS = "prometheus"
    STATSD = "statsd"
    INFLUXDB = "influxdb"
    OPENTELEMETRY = "opentelemetry"
    JSON = "json"

class MetricsExporter:
    """Exportador de métricas a sistemas externos de monitoreo."""
    
    def __init__(self, event_bus, store, logger, config=None):
        self.event_bus = event_bus
        self.store = store
        self.logger = logger
        self.config = config or {}
        self.export_interval = self.config.get('export_interval', 60)  # segundos
        self.batch_size = self.config.get('batch_size', 1000)
        self.exporters = {}
        self.running = False
        self.metrics_buffer = []
        
        # Registrar exportadores disponibles
        self._register_exporters()
        # Registrar listeners
        self._register_event_listeners()
    
    def _register_exporters(self):
        """Registra los exportadores disponibles."""
        self.exporters[ExportFormat.PROMETHEUS] = self._export_prometheus
        self.exporters[ExportFormat.STATSD] = self._export_statsd
        self.exporters[ExportFormat.INFLUXDB] = self._export_influxdb
        self.exporters[ExportFormat.OPENTELEMETRY] = self._export_opentelemetry
        self.exporters[ExportFormat.JSON] = self._export_json
    
    def _register_event_listeners(self):
        """Registra listeners para eventos del sistema."""
        self.event_bus.on("metrics:collect", self._handle_metric_event)
        self.event_bus.on("metrics:export_requested", self._handle_export_request)
    
    async def start(self):
        """Inicia el proceso de exportación periódica."""
        self.running = True
        self.logger.info("Metrics exporter started")
        
        while self.running:
            try:
                await self._periodic_export()
                await asyncio.sleep(self.export_interval)
            except Exception as e:
                self.logger.error(f"Error in periodic export: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def stop(self):
        """Detiene el proceso de exportación."""
        self.running = False
        # Exportar métricas pendientes antes de detener
        if self.metrics_buffer:
            await self._export_batch(self.metrics_buffer)
        self.logger.info("Metrics exporter stopped")
    
    def collect_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, 
                      timestamp: Optional[datetime] = None) -> None:
        """Recopila una métrica individual."""
        metric = {
            'name': name,
            'value': value,
            'tags': tags or {},
            'timestamp': timestamp or datetime.utcnow()
        }
        self.metrics_buffer.append(metric)
        
        # Si el buffer excede el tamaño de lote, exportar
        if len(self.metrics_buffer) >= self.batch_size:
            asyncio.create_task(self._export_batch(self.metrics_buffer))
            self.metrics_buffer = []
    
    async def export_metrics(self, format_type: ExportFormat, metrics: List[Dict], 
                           config: Optional[Dict] = None) -> bool:
        """Exporta métricas en el formato especificado."""
        if format_type not in self.exporters:
            self.logger.error(f"Unsupported export format: {format_type}")
            return False
        
        exporter = self.exporters[format_type]
        try:
            return await exporter(metrics, config or {})
        except Exception as e:
            self.logger.error(f"Error exporting metrics in {format_type} format: {e}")
            return False
    
    # Métodos privados de exportación
    async def _export_prometheus(self, metrics: List[Dict], config: Dict) -> bool:
        """Exporta métricas en formato Prometheus."""
        endpoint = config.get('endpoint', 'http://localhost:9090/metrics')
        
        try:
            # Convertir métricas a formato Prometheus
            prometheus_data = []
            for metric in metrics:
                tags_str = ','.join([f'{k}="{v}"' for k, v in metric['tags'].items()])
                if tags_str:
                    prometheus_data.append(f"{metric['name']}{{{tags_str}}} {metric['value']} {int(metric['timestamp'].timestamp() * 1000)}")
                else:
                    prometheus_data.append(f"{metric['name']} {metric['value']} {int(metric['timestamp'].timestamp() * 1000)}")
            
            # Simular envío a Prometheus (en implementación real sería una llamada HTTP)
            self.logger.debug(f"Exporting to Prometheus: {prometheus_data}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting to Prometheus: {e}")
            return False
    
    async def _export_statsd(self, metrics: List[Dict], config: Dict) -> bool:
        """Exporta métricas en formato StatsD."""
        host = config.get('host', 'localhost')
        port = config.get('port', 8125)
        
        try:
            # Convertir métricas a formato StatsD
            statsd_data = []
            for metric in metrics:
                tags_str = ','.join([f'{k}:{v}' for k, v in metric['tags'].items()])
                if tags_str:
                    statsd_data.append(f"{metric['name']}:{metric['value']}|g|#{tags_str}")
                else:
                    statsd_data.append(f"{metric['name']}:{metric['value']}|g")
            
            # Simular envío a StatsD (en implementación real sería un envío UDP)
            self.logger.debug(f"Exporting to StatsD: {statsd_data}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting to StatsD: {e}")
            return False
    
    async def _export_influxdb(self, metrics: List[Dict], config: Dict) -> bool:
        """Exporta métricas en formato InfluxDB."""
        url = config.get('url', 'http://localhost:8086')
        database = config.get('database', 'core_dajarony')
        
        try:
            # Convertir métricas a formato InfluxDB line protocol
            influx_data = []
            for metric in metrics:
                tags_str = ','.join([f'{k}={v}' for k, v in metric['tags'].items()])
                if tags_str:
                    influx_data.append(f"{metric['name']},{tags_str} value={metric['value']} {int(metric['timestamp'].timestamp() * 1e9)}")
                else:
                    influx_data.append(f"{metric['name']} value={metric['value']} {int(metric['timestamp'].timestamp() * 1e9)}")
            
            # Simular envío a InfluxDB (en implementación real sería una llamada HTTP)
            self.logger.debug(f"Exporting to InfluxDB: {influx_data}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting to InfluxDB: {e}")
            return False
    
    async def _export_opentelemetry(self, metrics: List[Dict], config: Dict) -> bool:
        """Exporta métricas en formato OpenTelemetry."""
        endpoint = config.get('endpoint', 'http://localhost:4317')
        
        try:
            # Convertir métricas a formato OpenTelemetry
            otel_data = {
                'resource_metrics': [{
                    'resource': {
                        'attributes': [
                            {'key': 'service.name', 'value': {'string_value': 'core_dajarony'}}
                        ]
                    },
                    'scope_metrics': [{
                        'scope': {'name': 'core_dajarony.metrics'},
                        'metrics': []
                    }]
                }]
            }
            
            for metric in metrics:
                otel_metric = {
                    'name': metric['name'],
                    'unit': '',
                    'gauge': {
                        'data_points': [{
                            'value': metric['value'],
                            'time_unix_nano': int(metric['timestamp'].timestamp() * 1e9),
                            'attributes': [{'key': k, 'value': {'string_value': str(v)}} for k, v in metric['tags'].items()]
                        }]
                    }
                }
                otel_data['resource_metrics'][0]['scope_metrics'][0]['metrics'].append(otel_metric)
            
            # Simular envío a OpenTelemetry (en implementación real sería un gRPC o HTTP call)
            self.logger.debug(f"Exporting to OpenTelemetry: {otel_data}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting to OpenTelemetry: {e}")
            return False
    
    async def _export_json(self, metrics: List[Dict], config: Dict) -> bool:
        """Exporta métricas en formato JSON."""
        filepath = config.get('filepath', f'metrics_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json')
        
        try:
            # Convertir métricas a JSON
            json_data = []
            for metric in metrics:
                json_data.append({
                    'name': metric['name'],
                    'value': metric['value'],
                    'tags': metric['tags'],
                    'timestamp': metric['timestamp'].isoformat()
                })
            
            # Guardar en archivo JSON
            with open(filepath, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            self.logger.debug(f"Exported metrics to JSON file: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            return False
    
    # Métodos privados auxiliares
    async def _periodic_export(self):
        """Realiza la exportación periódica de métricas."""
        if not self.metrics_buffer:
            return
        
        # Exportar en los formatos configurados
        for format_name, config in self.config.get('export_formats', {}).items():
            if config.get('enabled', False):
                format_type = ExportFormat(format_name.lower())
                await self.export_metrics(format_type, self.metrics_buffer, config)
        
        # Limpiar buffer
        self.metrics_buffer = []
    
    async def _export_batch(self, metrics: List[Dict]) -> None:
        """Exporta un lote de métricas."""
        for format_name, config in self.config.get('export_formats', {}).items():
            if config.get('enabled', False):
                format_type = ExportFormat(format_name.lower())
                await self.export_metrics(format_type, metrics, config)
    
    def _handle_metric_event(self, event_data: Dict[str, Any]) -> None:
        """Maneja eventos de métricas."""
        name = event_data.get('name')
        value = event_data.get('value')
        tags = event_data.get('tags')
        timestamp = event_data.get('timestamp')
        
        if name and value is not None:
            self.collect_metric(name, value, tags, timestamp)
    
    def _handle_export_request(self, event_data: Dict[str, Any]) -> None:
        """Maneja solicitudes explícitas de exportación."""
        format_type = event_data.get('format')
        metrics = event_data.get('metrics', self.metrics_buffer)
        config = event_data.get('config')
        
        if format_type:
            try:
                export_format = ExportFormat(format_type.lower())
                asyncio.create_task(self.export_metrics(export_format, metrics, config))
            except ValueError:
                self.logger.error(f"Invalid export format requested: {format_type}")