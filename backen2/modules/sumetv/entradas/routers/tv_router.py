"""
SUME DOCBLOCK

Nombre: Router de Control de TV
Tipo: Entrada

Entradas:
- Peticiones POST a varios sub-endpoints bajo /tv (ej. /tv/register, /tv/ping, /tv/discover, etc.)

Acciones:
- Recibe y enruta las peticiones relacionadas con el control de dispositivos TV.
- Delega la lógica de negocio a los métodos del TVController.
- Maneja errores HTTP y excepciones generales.

Salidas:
- Respuestas JSON con el resultado de cada operación (éxito/error).
"""
import logging
import traceback # Keep traceback for detailed error logging if needed elsewhere
from fastapi import APIRouter, Request, HTTPException
from starlette.responses import JSONResponse
# Assuming TVController is in the path sumetv.logica.controladores.tv_controller
from sumetv.logica.controladores.tv_controller import TVController

logger = logging.getLogger("tv_router")

logger.info("Inicializando Router TV...")
# Se elimina el prefix="/tv" para evitar la duplicación de rutas
router = APIRouter(tags=["tv"])

@router.post("/register")
async def register(request: Request):
    """Registra o actualiza un dispositivo TV en el sistema."""
    logger.info("Recibida solicitud POST /tv/register")
    try:
        controller = TVController()
        logger.info("TVController inicializado correctamente para register")
        # Controller's register method will handle request.json()
        result = await controller.register(request)
        logger.info(f"Resultado de register: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en register: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/ping")
async def ping(request: Request):
    """Verifica la disponibilidad de un dispositivo TV por su ID."""
    logger.info("Recibida solicitud POST /tv/ping")
    try:
        controller = TVController()
        logger.info("TVController inicializado correctamente para ping")
        # Controller's ping method will handle request.json()
        result = await controller.ping(request)
        logger.info(f"Resultado de ping: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en ping: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/discover")
async def discover(request: Request):
    """Inicia el proceso de descubrimiento de dispositivos TV en la red."""
    logger.info("Recibida solicitud POST /tv/discover")
    try:
        controller = TVController()
        logger.info("TVController inicializado correctamente para discover")
        # Controller's discover method will handle request.json()
        result = await controller.discover(request)
        logger.info(f"Resultado de discover: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en discover: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno en discover: {str(e)}")

@router.post("/mirror")
async def mirror(request: Request):
    """Inicia el mirroring de pantalla a un dispositivo compatible."""
    logger.info("Recibida solicitud POST /tv/mirror")
    try:
        # Controller's mirror method will handle request.json()
        return await TVController().mirror(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en mirror: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/open-app")
async def open_app(request: Request):
    """Lanza una aplicación específica en un dispositivo TV."""
    logger.info("Recibida solicitud POST /tv/open-app")
    try:
        # Controller's open_app method will handle request.json()
        return await TVController().open_app(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en open_app: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/cast-url")
async def cast_url(request: Request):
    """Envía una URL multimedia para ser reproducida en un dispositivo TV."""
    logger.info("Recibida solicitud POST /tv/cast-url")
    try:
        # Controller's cast_url method will handle request.json()
        return await TVController().cast_url(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en cast_url: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/android-control")
async def android_control(request: Request):
    """Envía comandos de control ADB a un dispositivo Android TV."""
    logger.info("Recibida solicitud POST /tv/android-control")
    try:
        controller = TVController()
        logger.info("TVController inicializado correctamente para android-control")
        # Controller's android_control method will handle request.json()
        result = await controller.android_control(request)
        logger.info(f"Resultado de android-control: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en android-control: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/list_devices")
async def list_devices(request: Request): # Assuming this might take a body in the future, though typically list might not.
    """Lista todos los dispositivos TV registrados en el sistema."""
    logger.info("Recibida solicitud POST /tv/list_devices")
    try:
        controller = TVController()
        logger.info("TVController inicializado correctamente para list_devices")
        # Controller's list_devices method will handle request.json() if needed
        result = await controller.list_devices(request)
        logger.info(f"Resultado de list_devices: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en list_devices: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# Nuevos endpoints para el control de Philips TV
@router.post("/philips-key")
async def philips_key(request: Request):
    """Envía un comando de tecla a una TV Philips."""
    logger.info("=== INICIO endpoint /tv/philips-key ===")
    try:
        try:
            # Leer el cuerpo como JSON UNA SOLA VEZ
            request_data = await request.json()
        except Exception as json_exc:
            logger.error(f"Error al parsear JSON del request para philips-key: {json_exc}", exc_info=True)
            # Devolver un error 400 Bad Request si el JSON es inválido o ausente
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Cuerpo de la solicitud JSON inválido o ausente."}
            )
        logger.info(f"Datos JSON recibidos en router para philips-key: {request_data}")
        
        controller = TVController()
        logger.info("TVController creado para philips-key")
        # Pasar el diccionario parseado al método del controlador
        # Asegúrate de que controller.philips_key ahora espera un diccionario
        result = await controller.philips_key(request_data) 
        
        logger.info(f"Resultado del controlador para philips-key: {result}")
        
        if isinstance(result, JSONResponse):
            logger.info("Devolviendo JSONResponse para philips-key")
            logger.info(f"Status code: {result.status_code}")
            return result
        
        logger.info(f"Resultado final (no JSONResponse) para philips-key: {result}")
        logger.info("=== FIN endpoint /tv/philips-key ===")
        # Si result no es JSONResponse, FastAPI lo convertirá a uno (asumiendo que es serializable)
        return result

    except HTTPException: # Re-lanzar HTTPExceptions para que FastAPI las maneje
        raise
    except Exception as e:
        logger.error(f"Error inesperado en endpoint philips-key: {str(e)}", exc_info=True)
        # Usar traceback.format_exc() para un log más detallado si es necesario,
        # pero exc_info=True en logger.error ya lo incluye.
        # logger.error(f"Traceback completo: {traceback.format_exc()}") 
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Error interno en endpoint philips-key: {str(e)}"}
        )

@router.post("/philips-volume")
async def philips_volume(request: Request):
    """Ajusta el volumen de una TV Philips."""
    logger.info("=== INICIO endpoint /tv/philips-volume ===")
    try:
        try:
            # Leer el cuerpo como JSON UNA SOLA VEZ
            request_data = await request.json()
        except Exception as json_exc:
            logger.error(f"Error al parsear JSON del request para philips-volume: {json_exc}", exc_info=True)
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Cuerpo de la solicitud JSON inválido o ausente."}
            )
        logger.info(f"Datos JSON recibidos en router para philips-volume: {request_data}")
        
        controller = TVController()
        logger.info("TVController creado para philips-volume")
        # Pasar el diccionario parseado al método del controlador
        # Asegúrate de que controller.philips_volume ahora espera un diccionario
        result = await controller.philips_volume(request_data)
        
        logger.info(f"Resultado del controlador para philips-volume: {result}")
        
        if isinstance(result, JSONResponse):
            logger.info("Devolviendo JSONResponse para philips-volume")
            logger.info(f"Status code: {result.status_code}")
            return result
        
        logger.info(f"Resultado final (no JSONResponse) para philips-volume: {result}")
        logger.info("=== FIN endpoint /tv/philips-volume ===")
        return result

    except HTTPException: # Re-lanzar HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Error inesperado en endpoint philips-volume: {str(e)}", exc_info=True)
        # logger.error(f"Traceback completo: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Error interno en endpoint philips-volume: {str(e)}"}
        )