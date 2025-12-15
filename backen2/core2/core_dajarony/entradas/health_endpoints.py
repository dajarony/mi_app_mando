# core_dajarony/entradas/health_endpoints.py
"""
SUME DOCBLOCK

Nombre: Health Endpoints
Tipo: Entrada

Entradas:
- Instancia del contenedor
- Solicitudes HTTP para checks de salud
- Parámetros de consulta para diferentes niveles de detalle

Acciones:
- Verificar estado de componentes principales
- Recopilar métricas de salud del sistema
- Proporcionar información de versión y entorno
- Evaluar conectividad con servicios externos
- Generar respuestas formateadas de salud

Salidas:
- Respuestas HTTP con estado de salud
- Métricas detalladas del sistema
- Errores o advertencias detectadas
- Información de diagnóstico
"""
import json
import asyncio
from http.server import BaseHTTPRequestHandler
from datetime import datetime
from typing import Dict, Any

class HealthEndpoints:
    """Endpoints de salud para monitoreo del sistema."""
    
    def __init__(self, container):
        self.container = container
        self.logger = container.get("logger")
        self.components = ['event_bus', 'store', 'validator', 'telemetry_collector', 'circuit_breaker']
        
    async def get_health_status(self) -> Dict[str, Any]:
        """Obtiene el estado de salud completo del sistema."""
        status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {},
            "metrics": {},
            "errors": []
        }
        
        # Verificar estado de componentes
        for component_name in self.components:
            try:
                component = self.container.get(component_name)
                if component:
                    status["components"][component_name] = {
                        "status": "up",
                        "version": getattr(component, "__version__", "1.0.0")
                    }
                else:
                    status["components"][component_name] = {
                        "status": "down",
                        "error": f"Component {component_name} not found"
                    }
                    status["errors"].append(f"Component {component_name} is down")
            except Exception as e:
                status["components"][component_name] = {
                    "status": "error",
                    "error": str(e)
                }
                status["errors"].append(f"Error checking {component_name}: {e}")
        
        # Obtener métricas básicas si está disponible el telemetry collector
        try:
            telemetry = self.container.get("telemetry_collector")
            if telemetry:
                status["metrics"] = {
                    "uptime": telemetry.get_uptime(),
                    "request_count": telemetry.get_request_count(),
                    "error_rate": telemetry.get_error_rate()
                }
        except Exception as e:
            self.logger.warning(f"Could not collect metrics: {e}")
        
        # Determinar estado general
        if status["errors"]:
            status["status"] = "unhealthy"
        elif any(comp["status"] != "up" for comp in status["components"].values()):
            status["status"] = "degraded"
        
        return status
    
    async def get_readiness(self) -> Dict[str, Any]:
        """Verifica si el sistema está listo para procesar solicitudes."""
        ready = True
        checks = {}
        
        # Verificar componentes críticos
        for component_name in ['event_bus', 'store', 'validator']:
            try:
                component = self.container.get(component_name)
                checks[component_name] = component is not None
                ready = ready and checks[component_name]
            except:
                checks[component_name] = False
                ready = False
        
        return {
            "ready": ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_liveness(self) -> Dict[str, str]:
        """Simple check de que el servicio está vivo."""
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }

    def start_http_server(self, port: int = 8080):
        """Inicia un servidor HTTP simple para los endpoints de salud."""
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        
        class HealthCheckHandler(SimpleHTTPRequestHandler):
            def __init__(self, health_endpoints, *args, **kwargs):
                self.health_endpoints = health_endpoints
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                if self.path == '/health' or self.path == '/':
                    self.handle_health()
                elif self.path == '/ready':
                    self.handle_readiness()
                elif self.path == '/live':
                    self.handle_liveness()
                else:
                    self.send_error(404, "Endpoint not found")
            
            def handle_health(self):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                status = loop.run_until_complete(self.health_endpoints.get_health_status())
                loop.close()
                
                status_code = 200 if status["status"] == "healthy" else 503
                self.send_response(status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(status).encode())
            
            def handle_readiness(self):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                status = loop.run_until_complete(self.health_endpoints.get_readiness())
                loop.close()
                
                status_code = 200 if status["ready"] else 503
                self.send_response(status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(status).encode())
            
            def handle_liveness(self):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                status = loop.run_until_complete(self.health_endpoints.get_liveness())
                loop.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(status).encode())
        
        def handler_factory(*args, **kwargs):
            return HealthCheckHandler(self, *args, **kwargs)
        
        server_address = ('', port)
        httpd = HTTPServer(server_address, handler_factory)
        self.logger.info(f"Health check server running on port {port}")
        httpd.serve_forever()