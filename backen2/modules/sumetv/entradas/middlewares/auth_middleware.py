"""
SUME DOCBLOCK
Nombre: Middleware de Autenticación y Control de Acceso
Tipo: Entrada

Entradas:
- Headers HTTP: Authorization Bearer <token> o X-API-KEY
- Variables de entorno: AUTH_TOKEN

Acciones:
- Extrae token de encabezados de autorización.
- Valida el token contra el AUTH_TOKEN configurado.
- Exime rutas públicas y solicitudes preflight CORS (OPTIONS) de autenticación.
- Implementa un rate limiting básico por IP para prevenir abusos.

Salidas:
- Permite la petición si la autenticación es válida o la ruta es pública.
- Respuesta JSON con status 401 Unauthorized si no se proporciona o valida el token.
- Respuesta JSON con status 429 Too Many Requests si se excede el rate limit.
"""
import logging
import os
import time
from collections import defaultdict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logger = logging.getLogger("auth_middleware")

# Obtener token seguro desde variables de entorno
API_KEY = os.getenv("AUTH_TOKEN")

if not API_KEY:
    logger.error("❌ AUTH_TOKEN no encontrado en variables de entorno!")
    raise ValueError("AUTH_TOKEN debe estar definido en el archivo .env")

if len(API_KEY) < 32:
    logger.warning("⚠️  AUTH_TOKEN parece muy corto. Usa al menos 32 caracteres.")

# Rate limiting simple por IP
request_tracker = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 60

def validate_token(token: str) -> bool:
    """
    Valida el token Bearer o API key contra la variable de entorno AUTH_TOKEN.
    
    Args:
        token (str): El token a validar.
        
    Returns:
        bool: True si el token es válido, False en caso contrario.
    """
    if not token or not API_KEY:
        return False
    
    # Mask token para logs (mostrar solo últimos 4 caracteres)
    masked = ("*" * (len(token) - 4) + token[-4:]) if len(token) > 4 else "****"
    logger.info(f"Validando token: {masked}. Comparando con API_KEY: {API_KEY[:10]}...")
    return token == API_KEY

def check_rate_limit(ip: str) -> bool:
    """
    Implementa un rate limiting básico: máximo MAX_REQUESTS_PER_MINUTE por IP por minuto.
    
    Args:
        ip (str): La dirección IP del cliente.
        
    Returns:
        bool: True si la solicitud está dentro del límite, False si se excede.
    """
    now = time.time()
    minute_ago = now - 60
    
    # Limpiar requests antiguos
    request_tracker[ip] = [req_time for req_time in request_tracker[ip] if req_time > minute_ago]
    
    # Agregar request actual
    request_tracker[ip].append(now)
    
    # Verificar límite
    if len(request_tracker[ip]) > MAX_REQUESTS_PER_MINUTE:
        logger.warning(f"Rate limit excedido para IP: {ip}")
        return False
    
    return True

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware de autenticación para proteger los endpoints de la API."""
    # Rutas públicas que no requieren autenticación
    public_paths = [
        "/health", "/live", "/ready", "/metrics",
        "/docs", "/redoc", "/openapi.json", 
        "/api/v1/openapi.json",
        "/docs/oauth2-redirect",
        "/reload-config", # Ahora es pública aquí
        "/tv/list_devices", # Añadido aquí
        "/tv/discover", # Añadido aquí
        "/tv/philips-key", # Añadido aquí
        "/tv/open-app", # Añadido aquí
        "/tv/philips-volume",
        "/tv/cast-url",
        "/tv/mirror",
        "/tv/register", # Añadido aquí para permitir el registro sin autenticación
        # Añadir aquí cualquier otra ruta que deba ser pública
    ]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Procesa la solicitud HTTP para aplicar autenticación y rate limiting."""
        path = request.url.path
        method = request.method.upper()
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(f"AuthMiddleware: procesando ruta {method} {path} desde IP {client_ip}")

        # 1) Preflight CORS: siempre permitir
        if method == "OPTIONS":
            logger.info("Preflight CORS detectado, omitiendo autenticación")
            return await call_next(request)

        # 2) Rutas públicas
        is_public_path = any(path.startswith(p) for p in self.public_paths)
        logger.info(f"AuthMiddleware: Path {path} is_public_path: {is_public_path}")
        if is_public_path:
            logger.info(f"Ruta pública {path}: omitiendo autenticación")
            return await call_next(request)

        # 3) Rate limiting
        if not check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "status": "error", 
                    "message": f"Rate limit excedido. Máximo {MAX_REQUESTS_PER_MINUTE} requests por minuto."
                }
            )

        # 4) Extraer token de headers
        auth_header = request.headers.get("Authorization", "")
        api_key_hdr = request.headers.get("X-API-KEY", "")
        
        # No mostrar tokens completos en logs
        auth_display = auth_header[:10] + "..." if len(auth_header) > 10 else auth_header
        api_display = api_key_hdr[:10] + "..." if len(api_key_hdr) > 10 else api_key_hdr
        logger.info(f"Headers parciales: Authorization='{auth_display}', X-API-KEY='{api_display}'")

        token = None
        if auth_header:
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]
                logger.info("Token extraído de header Authorization con prefijo Bearer")
            else:
                token = auth_header
                logger.info("Token extraído de header Authorization sin prefijo Bearer")
        elif api_key_hdr:
            token = api_key_hdr
            logger.info("Token extraído de header X-API-KEY")

        if not token:
            logger.warning(f"No se proporcionó token de autenticación desde IP {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "error", "message": "Unauthorized: No se proporcionó token"}
            )

        # 5) Validar token
        if not validate_token(token):
            logger.warning(f"Token de autenticación inválido desde IP {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "error", "message": "Unauthorized: Token inválido"}
            )

        # 6) Si todo ok, continuar
        logger.info("Autenticación exitosa, procesando request")
        return await call_next(request)