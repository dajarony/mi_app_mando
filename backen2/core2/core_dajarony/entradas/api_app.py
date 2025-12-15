"""
SUME DOCBLOCK
Nombre: API Principal de Observabilidad y Control SUMETV
Tipo: Entrada

Entradas:
- Rutas HTTP: /health, /live, /ready, /metrics (GET)
- Rutas HTTP: /reload-config (POST, requiere autenticación)
- Rutas HTTP: /tv/* (POST, requieren autenticación)

Acciones:
- Proporciona endpoints para monitoreo de salud y métricas.
- Permite la recarga de configuración en caliente.
- Integra el middleware de autenticación para proteger rutas.
- Incluye el router de control de TV para la gestión de dispositivos.

Salidas:
- Respuestas JSON con estados y resultados de operaciones.
- Métricas en formato Prometheus.
- Notificaciones a través de logs.
"""
import logging
import os
import sys
from typing import Any, Dict
from types import MethodType
from datetime import datetime # Importar datetime
from contextlib import asynccontextmanager # Importar asynccontextmanager

from dotenv import load_dotenv

# Importar y configurar logging centralizado
from core2.core_dajarony.infraestructura.logging_config import setup_logging
setup_logging()

# Configurar el logger para este módulo después de setup_logging()
logger = logging.getLogger("api_app")

from fastapi import FastAPI, Response, Depends, HTTPException, Security, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter

# Cargar variables de entorno desde archivo .env
load_dotenv()

# --- Gestión de Paths ---
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
modules_dir = os.path.join(base_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

# --- Importaciones de Módulos del Core y SUMETV ---
from core2.core_dajarony.entradas.health_endpoints import HealthEndpoints
from core2.core_dajarony.logica.container import create_container
from core2.core_dajarony.entradas.config_watcher import start_config_watcher
from core2.core_dajarony.entradas.routers.tv_control_router import router as tv_router

logger.info("Inicializando API app...")

# --- Seguridad por API-Key para /reload-config ---
API_KEY_VALUE = os.getenv("RELOAD_CONFIG_API_KEY")
if not API_KEY_VALUE:
    logger.warning("RELOAD_CONFIG_API_KEY no está configurada. El endpoint /reload-config podría ser inseguro o no funcionar.")
    API_KEY_VALUE = "YOUR_DEFAULT_DEVELOPMENT_KEY_CHANGE_ME"

API_KEY_NAME = "X-API-KEY"
api_key_header_auth = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header_auth)) -> str:
    """Valida la API Key para el endpoint de recarga de configuración."""
    logger.info(f"get_api_key: Received API Key: {api_key_header[:10]}... (Expected: {API_KEY_VALUE[:10]}...)")
    if api_key_header != API_KEY_VALUE:
        logger.warning(f"Intento de acceso no autorizado a /reload-config con API Key: {api_key_header[:10]}...")
        raise HTTPException(
            status_code=403, detail="Forbidden: Invalid API Key"
        )
    return api_key_header

# --- Inicialización del Contenedor y Health Checks ---
logger.info("Creando contenedor de dependencias...")
try:
    container = create_container()
    health = HealthEndpoints(container)
except Exception as e:
    logger.error(f"Error inicializando el contenedor o HealthEndpoints: {e}", exc_info=True)
    sys.exit(1)

# --- Watcher de Configuración ---
CONFIG_FILE_PATH = "config.yml"
logger.info(f"Iniciando watcher de configuración para '{CONFIG_FILE_PATH}'...")
try:
    start_config_watcher(CONFIG_FILE_PATH, container)
except Exception as e:
    logger.error(f"Error iniciando el config watcher: {e}", exc_info=True)

# --- Métricas de Peticiones HTTP con Prometheus ---
REQUEST_COUNT = Counter(
    'app_requests_total',
    'Total de peticiones HTTP de la aplicación',
    ['method', 'endpoint', 'http_status']
)

# --- Middleware para contar peticiones ---
async def count_requests_middleware(request: Request, call_next):
    """Middleware para contar las peticiones HTTP y exponerlas como métricas."""
    endpoint = request.url.path
    method = request.method
    response = None
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        logger.error(f"Excepción no manejada procesando {method} {endpoint}: {e}", exc_info=True)
        raise
    finally:
        current_status_code = status_code if response else 500
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=current_status_code).inc()
    return response

# --- Lifespan de la aplicación --- 
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja los eventos de inicio y apagado de la aplicación FastAPI."""
    logger.info("La aplicación FastAPI ha iniciado.")
    logger.info("Rutas registradas:")
    url_list = []
    for route in app.routes:
        methods_str = ""
        if hasattr(route, "methods"):  # Para APIRoute
            methods_str = ", ".join(route.methods)
        elif hasattr(route, "routes"):  # Para Router montado
            methods_str = "ROUTER"  # Indica que es un router y los métodos están dentro

        url_list.append(f"  Path: {route.path}, Name: {getattr(route, 'name', 'N/A')}, Methods: [{methods_str}]")
    url_list.sort()  # Ordenar alfabéticamente por path para consistencia
    for line in url_list:
        logger.info(line)
    yield
    logger.info("La aplicación FastAPI se está apagando.")

# --- Instancia FastAPI ---
app = FastAPI(
    title="Core SUME Observabilidad + SUMETV",
    version="1.0.0",
    description="API para health checks, métricas Prometheus, hot-reload de configuración y control de Smart TVs.",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan # Usar la función lifespan
)

# Aplicar el middleware de conteo de peticiones
app.middleware("http")(count_requests_middleware)

# --- Middleware de CORS SEGURO ---
cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")

# Solo permitir orígenes específicos - NUNCA "*" en producción
if cors_origins_env:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    # Fallback seguro para desarrollo local ÚNICAMENTE
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    logger.warning("⚠️ CORS_ALLOWED_ORIGINS no configurado en .env. Usando configuración de desarrollo local.")

# Validar que no hay "*" en la lista (peligroso)
if "*" in CORS_ALLOWED_ORIGINS and len(CORS_ALLOWED_ORIGINS) > 1:
    logger.error("❌ CORS_ALLOWED_ORIGINS contiene '*' junto con otros orígenes específicos - ¡PELIGRO DE SEGURIDAD!")
    logger.error("❌ Configura solo orígenes específicos en el archivo .env o usa solo '*' si es intencional para desarrollo abierto (no recomendado).")
elif CORS_ALLOWED_ORIGINS == ["*"]:
    logger.warning("⚠️ CORS_ALLOWED_ORIGINS está configurado para permitir todos los orígenes ('*'). Esto es riesgoso para producción.")

logger.info(f"🔒 CORS configurado con orígenes: {CORS_ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-API-KEY",
        "Accept",
        "Origin",
        "X-Requested-With"
    ],
    expose_headers=["X-Total-Count"]
)

# --- Integración SUMETV ---

app.include_router(tv_router, prefix="/tv", tags=["SUMETV Control"])

# --- Fin Integración SUMETV ---

# --- Endpoints de Observabilidad ---
@app.get("/health", tags=["Observabilidad"], summary="Chequeo de salud básico")
async def health_check() -> Dict[str, str]:
    """Endpoint para verificar el estado de salud de la aplicación."""
    logger.debug("Health check solicitado.")
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/live", tags=["Observabilidad"], summary="Indica si la aplicación está viva")
async def live_check() -> Dict[str, str]:
    """Endpoint para verificar si la aplicación está viva y respondiendo."""
    logger.debug("Live check solicitado.")
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@app.get("/ready", tags=["Observabilidad"], summary="Indica si la aplicación está lista para recibir tráfico")
async def ready_check() -> Dict[str, str]:
    """Endpoint para verificar si la aplicación está lista para manejar solicitudes."""
    logger.debug("Ready check solicitado.")
    return {"status": "ready", "timestamp": datetime.now().isoformat()}

@app.get("/metrics", tags=["Observabilidad"], summary="Exporta métricas en formato Prometheus")
async def metrics() -> Response:
    """Endpoint para exponer métricas de la aplicación en formato Prometheus."""
    logger.debug("Métricas solicitadas.")
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.post("/reload-config", tags=["Observabilidad"], summary="Recarga la configuración desde config.yml",
          dependencies=[Depends(get_api_key)])
async def reload_config_endpoint() -> Dict[str, str]:
    """Endpoint para recargar la configuración de la aplicación desde config.yml."""
    logger.info(f"Solicitud de recarga de configuración para '{CONFIG_FILE_PATH}' recibida.")
    try:
        start_config_watcher(CONFIG_FILE_PATH, container)
        logger.info(f"Configuración '{CONFIG_FILE_PATH}' recargada exitosamente.")
        return {"status": "reloaded", "message": f"Configuration '{CONFIG_FILE_PATH}' reloaded."}
    except FileNotFoundError:
        logger.error(f"Error al recargar: El archivo de configuración '{CONFIG_FILE_PATH}' no fue encontrado.")
        raise HTTPException(status_code=404, detail=f"Configuration file '{CONFIG_FILE_PATH}' not found.")
    except Exception as e:
        logger.error(f"Error durante la recarga de configuración: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reloading configuration: {e}")

if __name__ == "__main__":
    import uvicorn
    # Usar valores de .env para Uvicorn si están definidos, con defaults razonables
    uvicorn_host = os.getenv("HOST", "127.0.0.1")
    uvicorn_port = int(os.getenv("PORT", "8000"))
    uvicorn_log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    # Convertir string de reload a booleano de forma más robusta
    uvicorn_reload_str = os.getenv("UVICORN_RELOAD", "False")
    uvicorn_reload = uvicorn_reload_str.lower() in ("true", "1", "t", "yes")

    logger.info(f"Iniciando Uvicorn en http://{uvicorn_host}:{uvicorn_port} (Reload: {uvicorn_reload}, Log Level: {uvicorn_log_level})")
    uvicorn.run(
        "core2.core_dajarony.entradas.api_app:app",  # Referencia a la instancia de la app FastAPI en este archivo
        host=uvicorn_host,
        port=uvicorn_port,
        log_level=uvicorn_log_level,
        reload=uvicorn_reload
    )