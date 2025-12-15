"""
SUME DOCBLOCK

Nombre: TVController
Tipo: Lógica/Controladores

Entradas:
- Objetos Request de FastAPI (para métodos que reciben JSON directamente del router).
- Diccionarios de datos (para métodos Philips específicos que reciben datos ya parseados).

Acciones:
- Orquesta la interacción con diversos servicios (DLNA, ADB, WebRTC, Philips TV).
- Gestiona el registro, listado y verificación de dispositivos.
- Implementa la lógica para el descubrimiento de dispositivos (DLNA y Android).
- Controla funcionalidades específicas como lanzamiento de apps, casting de URLs y comandos Android/Philips.

Salidas:
- Diccionarios JSON con el resultado de cada operación (éxito/error).
- Excepciones HTTP para errores de cliente o servidor.
"""
import logging
import traceback
from fastapi import Request, HTTPException, status # Request sigue siendo necesario para otros métodos
from fastapi.responses import JSONResponse

from sumetv.entradas.descubrimiento.dlna_discovery import discover_dlna
# Importar el nuevo módulo de descubrimiento Android
from sumetv.entradas.descubrimiento.android_discovery import discover_android_devices
# from sumetv.logica.screenmirroring.webrtc_server import WebRTCServer
from sumetv.logica.lanzadores.mobile_app_launcher import MobileAppLauncher
from sumetv.logica.servicios.protocolos import DLNAService
from sumetv.logica.servicios.ping import ping
from sumetv.logica.servicios.android_control import send_adb_command
from sumetv.logica.Modelos.tv_device import TVDevice
from sumetv.logica.Almacen.almacen_dispositivos import (
    add_device as db_add_device,
    get_device as db_get_device,
    list_devices as db_list_devices,
    remove_device as db_remove_device,
)
# Importar el nuevo controlador de Philips
from sumetv.logica.controladores.philips_controller import PhilipsController

logger = logging.getLogger("tv_controller")

class TVController:
    """Clase controladora para orquestar las operaciones relacionadas con dispositivos TV."""
    def __init__(self):
        """Inicializa el TVController y sus dependencias."""
        # Inicializar el controlador Philips
        self.philips_controller = PhilipsController()
        logger.debug("Inicializado PhilipsController")
    
    async def register(self, request: Request):
        """Registra o actualiza un dispositivo TV en la base de datos.

        Args:
            request (Request): Objeto Request de FastAPI que contiene los datos del dispositivo.

        Returns:
            dict: Un diccionario con el estado de éxito y los datos del dispositivo registrado.

        Raises:
            HTTPException: Si el formato de los datos es inválido.
        """
        try:
            data = await request.json()
            device = TVDevice(**data)
            stored = db_add_device(device) # db_add_device es síncrono
            return {
                "status": "success",
                "message": f"Dispositivo '{device.name}' registrado correctamente",
                "device": stored.dict(),
            }
        except Exception as e:
            logger.exception("Error al registrar dispositivo")
            raise HTTPException(status_code=400, detail=f"Formato inválido: {e}")

    async def list_devices(self, request: Request): # request no se usa aquí, pero se mantiene por consistencia si se necesitara en el futuro.
        """Lista todos los dispositivos TV registrados en el sistema.

        Args:
            request (Request): Objeto Request de FastAPI (no utilizado directamente).

        Returns:
            dict: Un diccionario con el estado de éxito y una lista de dispositivos.

        Raises:
            HTTPException: Si ocurre un error interno al listar dispositivos.
        """
        try:
            devices = db_list_devices() # db_list_devices es síncrono
            return {
                "status": "success",
                "devices": [d.dict() for d in devices],
            }
        except Exception as e:
            logger.exception("Error al listar dispositivos")
            raise HTTPException(status_code=500, detail="Error interno al listar dispositivos")

    async def ping(self, request: Request):
        """Verifica la disponibilidad de un dispositivo TV por su ID.

        Args:
            request (Request): Objeto Request de FastAPI que contiene el device_id.

        Returns:
            dict: Un diccionario con el estado de éxito y la disponibilidad del dispositivo.

        Raises:
            HTTPException: Si falta el device_id, el dispositivo no se encuentra o hay un error interno.
        """
        try:
            data = await request.json()
            device_id = data.get("device_id")
            if not device_id:
                raise HTTPException(status_code=400, detail="Falta 'device_id'")

            device = db_get_device(device_id) # db_get_device es síncrono
            if not device:
                raise HTTPException(status_code=404, detail=f"No se encontró dispositivo con ID '{device_id}'")

            # Ping específico para TVs Philips
            if device.type.lower() == "philips_tv":
                alive = await self.philips_controller.check_connection(device.ip, device.port or 1925)
                return {
                    "status": "success",
                    "device_id": device_id,
                    "name": device.name,
                    "alive": alive,
                }
            else:
                # Ping genérico para otros dispositivos
                alive = await ping(device.ip)
                return {
                    "status": "success",
                    "device_id": device_id,
                    "name": device.name,
                    "alive": alive,
                }
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error en ping")
            raise HTTPException(status_code=500, detail="Error interno en ping")

    async def android_control(self, request: Request):
        """Envía comandos de control ADB a un dispositivo Android TV.

        Args:
            request (Request): Objeto Request de FastAPI que contiene el device_id y el comando.

        Returns:
            JSONResponse: Una respuesta JSON con el estado de la operación.

        Raises:
            HTTPException: Si faltan parámetros, el dispositivo no se encuentra o no es Android.
        """
        try:
            data = await request.json()
            device_id = data.get("device_id")
            command = data.get("command")

            if not device_id or not command:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": "Se requieren 'device_id' y 'command'"}
                )

            device = db_get_device(device_id) # db_get_device es síncrono
            if not device:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"status": "error", "message": f"No se encontró dispositivo con ID '{device_id}'"}
                )
                
            if device.type.lower() != "android":
                logger.warning(f"Intento de control Android en dispositivo no compatible: {device.name} ({device.type})")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": f"El dispositivo '{device.name}' no es Android"}
                )

            result = await send_adb_command(device, command)
            return result
        except Exception as e:
            logger.exception(f"Error en android_control: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error", "message": f"Error interno en android_control: {str(e)}"}
            )

    async def philips_key(self, request_data: dict):
        """
        Envía un comando de tecla a una TV Philips.
        
        Args:
            request_data (dict): Diccionario con 'device_id' y 'key'.
            
        Returns:
            JSONResponse: Una respuesta JSON con el estado de la operación.
        """
        logger.info("=== INICIO TVController.philips_key ===")
        try:
            logger.info(f"Datos recibidos en TVController.philips_key: {request_data}")
            result = await self.philips_control(request_data)
            logger.info(f"Resultado de philips_control en TVController.philips_key: {result}")
            
            if isinstance(result, JSONResponse):
                logger.info(f"JSONResponse status code: {result.status_code}")
                logger.info(f"JSONResponse body: {result.body}")
            
            logger.info("=== FIN TVController.philips_key ===")
            return result
        except Exception as e:
            logger.error(f"Error en TVController.philips_key: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "error_id": "PHILIPS_KEY_CONTROLLER_ERROR",
                    "message": f"Error interno en TVController.philips_key: {str(e)}"
                }
            )

    async def philips_control(self, request_data: dict):
        """Envía comandos a TV Philips mediante JointSpace API.

        Args:
            request_data (dict): Diccionario con 'device_id' y 'key'.

        Returns:
            JSONResponse: Una respuesta JSON con el estado de la operación.
        """
        logger.info("=== INICIO TVController.philips_control ===")
        try:
            logger.info(f"Datos recibidos en TVController.philips_control: {request_data}")
            
            device_id = request_data.get("device_id")
            key = request_data.get("key")
            logger.info(f"device_id: {device_id}, key: {key}")
            
            if not device_id or not key:
                error_msg = f"Faltan parámetros - device_id: {device_id}, key: {key}"
                logger.error(error_msg)
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": "Se requieren 'device_id' y 'key'"}
                )
                
            device = db_get_device(device_id) # db_get_device es síncrono
            logger.info(f"Dispositivo encontrado: {device.dict() if device else None}")
            
            if not device:
                logger.error(f"Dispositivo no encontrado: {device_id}")
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"status": "error", "message": f"No se encontró dispositivo con ID '{device_id}'"}
                )
                
            logger.info(f"Tipo de dispositivo: '{device.type}' (esperado: 'philips_tv')")
            if device.type.lower() != "philips_tv":
                error_msg = f"Tipo de dispositivo incorrecto: '{device.type}' != 'philips_tv'"
                logger.warning(error_msg)
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": f"El dispositivo '{device.name}' no es Philips TV"}
                )
                
            logger.info(f"Enviando tecla '{key}' a IP: {device.ip}, Puerto: {device.port or 1925}")
            success = await self.philips_controller.send_key(device.ip, device.port or 1925, key)
            logger.info(f"Resultado send_key: {success}")
            
            if success:
                logger.info("Tecla enviada correctamente")
                return JSONResponse(
                    content={"status": "success", "message": f"Tecla '{key}' enviada correctamente", "device_id": device_id}
                )
            else:
                logger.error("Error al enviar tecla")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"status": "error", "message": f"Error al enviar tecla '{key}'", "device_id": device_id}
                )
        except Exception as e:
            logger.error(f"Error en TVController.philips_control: {str(e)}", exc_info=True)
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error", "message": f"Error interno en TVController.philips_control: {str(e)}"}
            )
            
    async def philips_volume(self, request_data: dict):
        """Ajusta el volumen en TV Philips.

        Args:
            request_data (dict): Diccionario con 'device_id' y 'volume'.

        Returns:
            JSONResponse: Una respuesta JSON con el estado de la operación.
        """
        logger.info("=== INICIO TVController.philips_volume ===")
        try:
            logger.info(f"Datos recibidos en TVController.philips_volume: {request_data}")
            device_id = request_data.get("device_id")
            volume = request_data.get("volume")
            
            if not device_id or volume is None:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": "Se requieren 'device_id' y 'volume'"}
                )
                
            device = db_get_device(device_id) # db_get_device es síncrono
            if not device:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"status": "error", "message": f"No se encontró dispositivo con ID '{device_id}'"}
                )
                
            if device.type.lower() != "philips_tv":
                logger.warning(f"Intento de control Philips en dispositivo no compatible: {device.name} ({device.type})")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": f"El dispositivo '{device.name}' no es Philips TV"}
                )
                
            success = await self.philips_controller.set_volume(device.ip, device.port or 1925, int(volume))
            if success:
                return JSONResponse(
                    content={"status": "success", "message": f"Volumen ajustado a {volume}", "device_id": device_id}
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"status": "error", "message": "Error al ajustar volumen", "device_id": device_id}
                )
        except Exception as e:
            logger.exception(f"Error en TVController.philips_volume: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error", "message": f"Error interno en TVController.philips_volume: {str(e)}"}
            )

    async def handle_philips_cast_url(self, device, url: str) -> dict:
        """
        Maneja cast-url específicamente para TVs Philips usando el endpoint /activities/browser
        
        Args:
            device: Objeto del dispositivo TV Philips
            url (str): URL a enviar al TV
            
        Returns:
            dict: Resultado de la operación con formato estándar
        """
        logger.info(f"=== INICIO handle_philips_cast_url ===")
        logger.info(f"Dispositivo: {device.name} ({device.ip}:{device.port or 1925})")
        logger.info(f"URL: {url}")
        
        try:
            # Verificar si el TV está encendido, si no, encenderlo
            logger.info("Verificando estado de energía del TV...")
            # Note: Usando send_command directamente para verificar estado
            power_result = await self.philips_controller.send_command(
                device.ip, device.port or 1925, "powerstate", method="GET"
            )
            
            if power_result and power_result.get("powerstate") == "Standby":
                logger.info("TV en standby, enviando comando para encender...")
                await self.philips_controller.send_key(device.ip, device.port or 1925, "Standby")
                
                # Esperar un momento para que el TV responda
                import asyncio
                await asyncio.sleep(2)
                logger.info("TV encendido, continuando con cast-url...")
            
            # Enviar URL al navegador del TV usando la nueva función
            logger.info("Enviando URL al navegador del TV...")
            result = await self.philips_controller.open_url_in_browser(
                device.ip, device.port or 1925, url
            )
            
            # Log del resultado detallado
            logger.info(f"Resultado de open_url_in_browser: {result}")
            
            if result["success"]:
                logger.info(f"✅ Cast-URL exitoso a TV Philips {device.name}: {url}")
                return {
                    "status": "success",
                    "message": f"URL enviada al navegador del TV: {url}",
                    "device_id": device.device_id,
                    "url": url
                }
            else:
                error_msg = f"❌ Cast-URL falló en TV Philips {device.name}: {result.get('message', 'Error desconocido')}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": result.get("message", "Error desconocido enviando URL al TV"),
                    "device_id": device.device_id,
                    "url": url
                }
                
        except Exception as e:
            error_msg = f"Error inesperado en handle_philips_cast_url para {device.name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg,
                "device_id": device.device_id,
                "url": url
            }
        finally:
            logger.info(f"=== FIN handle_philips_cast_url ===")

    async def discover(self, request: Request):
        """
        Descubre dispositivos en la red y opcionalmente los registra.
        Mejorado para buscar dispositivos DLNA y Android simultáneamente.
        
        Args:
            request (Request): Objeto Request de FastAPI que puede contener 'timeout', 'use_simulation' y 'auto_register'.
            
        Returns:
            dict: Un diccionario con el estado de éxito, la lista de dispositivos encontrados y si se registraron automáticamente.
            
        Raises:
            HTTPException: Si ocurre un error interno durante el descubrimiento.
        """
        try:
            data = await request.json()
            timeout = data.get("timeout", 15)
            use_simulation = data.get("use_simulation", False)
            auto_reg = data.get("auto_register", False)
            
            all_devices = []
            
            dlna_devices = await discover_dlna(timeout=timeout, use_simulation=use_simulation)
            all_devices.extend(dlna_devices)
            
            try:
                android_devices = await discover_android_devices(timeout=timeout)
                all_devices.extend(android_devices)
                logger.info(f"Encontrados {len(android_devices)} dispositivos Android")
            except Exception as e:
                logger.error(f"Error en descubrimiento Android: {e}")
                logger.exception(e)
            
            if auto_reg and all_devices:
                for dev in all_devices:
                    try:
                        if dev.get("device_type") == "MediaRenderer":
                            device_type = "dlna"
                        elif dev.get("device_type") == "android":
                            device_type = "android"
                        else:
                            device_type = "unknown"
                        
                        if "device_id" not in dev:
                            if device_type == "android":
                                dev["device_id"] = f"android-{dev['ip'].replace('.', '-')}"
                            else:
                                dev["device_id"] = f"device-{dev['ip'].replace('.', '-')}"
                        
                        tv = TVDevice(
                            device_id=dev.get("device_id"),
                            name=dev.get("name", f"TV {dev['ip']}"),
                            ip=dev["ip"],
                            type=device_type,
                            port=dev.get("port", 5555) if device_type == "android" else None,
                            location=dev.get("location"),
                            extra=dev,
                        )
                        db_add_device(tv) # db_add_device es síncrono
                        logger.info(f"Dispositivo registrado automáticamente: {tv.name} ({tv.device_id})")
                    except Exception as e:
                        logger.exception(f"Registro automático falló para {dev.get('ip')}: {e}")

            return {"status": "success", "devices": all_devices, "registered": auto_reg}
        except Exception as e:
            logger.exception("Error en discover")
            raise HTTPException(status_code=500, detail=f"Error interno en discover: {e}")

    async def mirror(self, request: Request):
        """Inicia el mirroring de pantalla a un dispositivo compatible.

        Args:
            request (Request): Objeto Request de FastAPI que contiene los datos para iniciar el mirroring.

        Returns:
            dict: Un diccionario con la URL del stream o el estado de la operación.
        """
        # WebRTC temporalmente deshabilitado
        # data = await request.json()
        # return await WebRTCServer().start_stream(data)
        
        raise HTTPException(
            status_code=501, 
            detail="WebRTC no disponible - instalar aiortc"
        )

    async def open_app(self, request: Request):
        """Lanza una aplicación específica en un dispositivo TV.

        Args:
            request (Request): Objeto Request de FastAPI que contiene 'device_id' y 'app_id'.

        Returns:
            dict: Un diccionario con el estado de éxito del lanzamiento de la aplicación.

        Raises:
            HTTPException: Si faltan parámetros, el dispositivo no se encuentra o hay un error interno.
        """
        logger.info("=== INICIO TVController.open_app ===")
        try:
            data = await request.json()
            device_id = data.get("device_id")
            app_id = data.get("app_id")
            
            if not device_id or not app_id:
                logger.error("Faltan device_id o app_id en la solicitud.")
                raise HTTPException(status_code=400, detail="Se requieren 'device_id' y 'app_id'")
                
            device = db_get_device(device_id) # db_get_device es síncrono
            if not device:
                logger.error(f"Dispositivo {device_id} no encontrado.")
                raise HTTPException(status_code=404, detail=f"Dispositivo '{device_id}' no encontrado")
                
            if device.type.lower() == "philips_tv":
                logger.info(f"Dispositivo Philips TV detectado. Buscando className para {app_id}...")
                apps = await self.philips_controller.get_apps(device.ip, device.port or 1925)
                
                target_app_class_name = None
                app_label = None
                for app_info in apps:
                    # Buscar por id o packageName
                    if app_info.get("id") == app_id or (app_info.get("intent") and app_info["intent"].get("component") and app_info["intent"]["component"].get("packageName") == app_id):
                        if app_info.get("intent") and app_info["intent"].get("component"):
                            target_app_class_name = app_info["intent"]["component"].get("className")
                            app_label = app_info.get("label", app_id)
                            logger.info(f"className encontrado para {app_id}: {target_app_class_name}")
                            break
                
                if target_app_class_name is None:
                    logger.warning(f"No se encontró className para {app_id} en la lista de aplicaciones de la TV. Intentando lanzar sin className específico.")
                    # Si no se encuentra, se intentará con className vacío como fallback
                    success = await self.philips_controller.launch_app(device.ip, device.port or 1925, app_id, class_name="", app_name_for_log=app_label)
                else:
                    success = await self.philips_controller.launch_app(device.ip, device.port or 1925, app_id, class_name=target_app_class_name, app_name_for_log=app_label)
                
                logger.info(f"Resultado de lanzamiento de app {app_id}: {success}")
                return {"launched": success}
            else:
                logger.info(f"Dispositivo no Philips TV. Delegando a MobileAppLauncher para {app_id}.")
                return MobileAppLauncher().launch_app(app_id) # Asumo que esto es síncrono o maneja su propia asincronía
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error en open_app: {e}")
            raise HTTPException(status_code=500, detail=f"Error interno en open_app: {e}")

    async def cast_url(self, request: Request):
        """Envía una URL multimedia para ser reproducida en un dispositivo TV.

        Args:
            request (Request): Objeto Request de FastAPI que contiene 'device_id' y 'url'.

        Returns:
            dict: Un diccionario con el estado de éxito del casting de la URL.

        Raises:
            HTTPException: Si faltan parámetros, el dispositivo no se encuentra o el tipo de dispositivo no es soportado.
        """
        try:
            data = await request.json()
            device_id = data.get("device_id")
            url = data.get("url")

            if not device_id or not url:
                raise HTTPException(status_code=400, detail="Se requieren 'device_id' y 'url'")

            device = db_get_device(device_id) # db_get_device es síncrono
            if not device:
                raise HTTPException(status_code=404, detail=f"Dispositivo '{device_id}' no encontrado")

            logger.info(f"Cast a {device.name} ({device.ip}): {url}")

            ct = "video/mp4"
            if url.endswith(".mp3"):
                ct = "audio/mpeg"
            elif url.lower().endswith((".jpg", ".jpeg")):
                ct = "image/jpeg"
            elif url.lower().endswith(".png"):
                ct = "image/png"

            if device.type == "dlna":
                try:
                    svc = DLNAService() # Asumo que DLNAService.send_content es síncrono o maneja su propia asincronía
                    res = svc.send_content(url)
                    logger.info(f"DLNAService response: {res}")
                    return {
                        "status": "success" if "sent" in res else "error",
                        "message": res.get("sent", res.get("error", "Error DLNA")),
                        "device_id": device_id
                    }
                except Exception as ex:
                    logger.exception("Error en DLNAService.send_content")
                    raise HTTPException(status_code=500, detail=f"DLNAService fallo: {ex}")

            elif device.type.lower() == "philips_tv":
                logger.info(f"Dispositivo Philips TV detectado. Usando nueva función open_url_in_browser para URL: {url}")
                
                # Usar la nueva función handle_philips_cast_url que maneja todo el flujo
                result = await self.handle_philips_cast_url(device, url)
                
                # Verificar el resultado y responder apropiadamente
                if result.get("status") == "success":
                    return result
                else:
                    # Si hay error, lanzar HTTPException con el mensaje del error
                    raise HTTPException(
                        status_code=500, 
                        detail=result.get("message", "Error desconocido en cast a Philips TV")
                    )

            elif device.type == "android":
                try:
                    cmd = f'am start -a android.intent.action.VIEW -d "{url}" -t {ct}'
                    logger.info(f"Enviando intent ADB para cast-url: {cmd}")
                    out = await send_adb_command(device, cmd)
                    logger.info(f"ADB intent response: {out}")

                    return {
                        "status": out.get("status", "error"),
                        "message": out.get("message", out.get("output", f"URL enviada a {device.name}")),
                        "device_id": device_id
                    }
                except Exception as ex:
                    logger.exception("Error enviando intent ADB para cast-url")
                    raise HTTPException(status_code=500, detail=f"Android intent fallo: {ex}")

            else:
                raise HTTPException(status_code=400, detail=f"Tipo '{device.type}' no soportado para cast")

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error en cast_url")
            raise HTTPException(status_code=500, detail=f"Error interno en cast_url: {e}")