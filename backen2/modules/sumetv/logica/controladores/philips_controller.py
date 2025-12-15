import aiohttp
import asyncio 
import logging
import re
from typing import Dict, Any, Optional, List

logger = logging.getLogger("philips_controller")


class PhilipsController:
    """
    Controlador específico para TVs Philips usando la API JointSpace.
    
    Este controlador encapsula la lógica para interactuar con la API JointSpace
    de televisores Philips, permitiendo enviar comandos, ajustar volumen, lanzar
    aplicaciones y verificar la conexión.
    """
    def __init__(self):
        """Inicializa el PhilipsController."""
        logger.info("Inicializando PhilipsController...")
        
    async def send_command(self, 
                           ip: str, 
                           port: int, 
                           endpoint: str, 
                           method: str = "GET",
                           data: Optional[Dict[str, Any]] = None, 
                           api_version: int = 6,
                           timeout_seconds: int = 5) -> Optional[Dict[str, Any]]:
        """
        Envía un comando HTTP a la API JointSpace de Philips.

        Args:
            ip (str): Dirección IP de la TV.
            port (int): Puerto de la API JointSpace (generalmente 1925 o 1926 para HTTPS).
            endpoint (str): El endpoint específico de la API (ej: "system", "input/key", "audio/volume").
            method (str): Método HTTP ("GET" o "POST").
            data (Optional[Dict[str, Any]]): Diccionario con los datos a enviar en el cuerpo de la solicitud POST.
            api_version (int): Versión de la API JointSpace a utilizar.
            timeout_seconds (int): Tiempo máximo de espera para la respuesta.

        Returns:
            Optional[Dict[str, Any]]: Un diccionario con la respuesta JSON de la API si es exitosa y JSON,
            o un diccionario de éxito para ciertos comandos POST (como input/key, audio/volume, activities/launch) 
            que responden 200 OK con non-JSON,
            o None si ocurre un error o la respuesta 200 OK non-JSON no es de un endpoint especial.
        """
        url = f"http://{ip}:{port}/{api_version}/{endpoint}"
        
        logger.info(f"=== Enviando comando a Philips TV: {method.upper()} {url} ===")
        if data:
            logger.info(f"Datos: {data}")

        request_timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        try:
            async with aiohttp.ClientSession(timeout=request_timeout) as session:
                response_data: Optional[Dict[str, Any]] = None

                if method.upper() == "GET":
                    async with session.get(url) as response:
                        logger.info(f"Respuesta GET - Status: {response.status} - Content-Type: {response.content_type}")
                        if response.status == 200:
                            if response.content_type == 'application/json':
                                response_data = await response.json()
                                logger.info(f"Resultado GET JSON: {response_data}")
                            else: 
                                logger.info(f"Respuesta GET exitosa (200) pero no es JSON (Content-Type: {response.content_type}). Devuelve None para GET.")
                                response_data = None 
                        else: 
                            error_body = await response.text()
                            logger.error(f"Error en GET - Status: {response.status}, Body: {error_body}")
                            return None 
                
                elif method.upper() == "POST":
                    async with session.post(url, json=data) as response:
                        logger.info(f"Respuesta POST - Status: {response.status} - Content-Type: {response.content_type}")
                        if response.status == 200:
                            if response.content_type == 'application/json':
                                response_data = await response.json()
                                logger.info(f"Resultado POST JSON: {response_data}")
                            elif endpoint in ["input/key", "audio/volume", "activities/launch", "activities/browser"]:
                                logger.info(f"Comando POST para '{endpoint}' exitoso (200 OK) con Content-Type: {response.content_type}. Considerando éxito.")
                                response_data = {"status": "success", "message": f"{endpoint} command accepted by TV (non-JSON response)"}
                            else: 
                                logger.info(f"Respuesta POST exitosa (200) pero no es JSON (Content-Type: {response.content_type}) y no es un endpoint con manejo especial. Devuelve None.")
                                response_data = None
                        else: 
                            error_body = await response.text()
                            logger.error(f"Error en POST - Status: {response.status}, Body: {error_body}")
                            return None # Devuelve None si el status no es 200
                else:
                    logger.error(f"Método HTTP no soportado: {method}")
                    return None

                return response_data

        except aiohttp.ClientConnectorError as e:
            logger.error(f"Error de conexión (aiohttp.ClientConnectorError) para {url}: {e}.")
            return None
        except asyncio.TimeoutError as e:  #  CORREGIDO: aiohttp.ClientTimeout → asyncio.TimeoutError
            logger.error(f"Timeout en la solicitud (asyncio.TimeoutError) para {url}: {e}")
            return None
        except aiohttp.ClientError as e: 
            logger.error(f"Error de cliente aiohttp (aiohttp.ClientError) para {url}: {e}")
            return None
        except Exception as e: 
            logger.error(f"Error inesperado al enviar comando a Philips TV ({url}): {e}", exc_info=True)
            return None

    async def check_connection(self, ip: str, port: int = 1925) -> bool:
        """Verifica si la TV está conectada y responde.

        Args:
            ip (str): Dirección IP de la TV.
            port (int): Puerto de la TV.

        Returns:
            bool: True si la TV está conectada y responde, False en caso contrario.
        """
        logger.info(f"Verificando conexión con TV en {ip}:{port}...")
        try:
            result = await self.send_command(ip, port, "system")
            connected = result is not None 
            logger.info(f"Resultado de verificación de conexión para {ip}:{port}: {'Conectado' if connected else 'No conectado o error'}")
            return connected
        except Exception as e:
            logger.error(f"Excepción al verificar conexión con Philips TV ({ip}:{port}): {e}", exc_info=True)
            return False
    
    async def send_key(self, ip: str, port: int, key: str) -> bool:
        """Envía una tecla virtual a la TV.

        Args:
            ip (str): Dirección IP de la TV.
            port (int): Puerto de la TV.
            key (str): La tecla a enviar (ej. "Home", "VolumeUp").

        Returns:
            bool: True si la tecla fue enviada con éxito, False en caso contrario.
        """
        logger.info(f"Enviando tecla '{key}' a Philips TV ({ip}:{port})")
        try:
            result = await self.send_command(
                ip=ip, 
                port=port, 
                endpoint="input/key", 
                method="POST", 
                data={"key": key}
            )
            success = result is not None and result.get("status") == "success"
            logger.info(f"Resultado de enviar tecla '{key}': {result}. Éxito: {success}")
            return success
        except Exception as e:
            logger.error(f"Excepción al enviar tecla '{key}' a Philips TV ({ip}:{port}): {e}", exc_info=True)
            return False
    
    async def set_volume(self, ip: str, port: int, level: int) -> bool:
        """Ajusta el volumen de la TV respetando los límites min/max reportados por la TV.

        Args:
            ip (str): Dirección IP de la TV.
            port (int): Puerto de la TV.
            level (int): El nivel de volumen deseado.

        Returns:
            bool: True si el volumen fue ajustado con éxito, False en caso contrario.
        """
        logger.info(f"Intentando ajustar volumen a {level} en TV {ip}:{port}...")
        try:
            current_audio_state = await self.send_command(ip, port, "audio/volume", method="GET")
            
            if not current_audio_state:
                logger.error(f"No se pudo obtener el estado actual del audio para {ip}:{port}. No se ajustará el volumen.")
                return False

            muted_state = current_audio_state.get("muted", False)
            min_volume = current_audio_state.get("min", 0) 
            max_volume = current_audio_state.get("max", 60) 
            
            logger.info(f"Límites de volumen de la TV: Min={min_volume}, Max={max_volume}. Muted actual: {muted_state}")

            adjusted_level = max(min_volume, min(level, max_volume))
            if adjusted_level != level:
                logger.info(f"Nivel de volumen solicitado ({level}) ajustado a {adjusted_level} para respetar los límites de la TV.")
            
            payload = {"current": adjusted_level, "muted": muted_state} 
            logger.info(f"Payload para volumen: {payload}")

            result = await self.send_command(
                ip=ip, 
                port=port, 
                endpoint="audio/volume", 
                method="POST", 
                data=payload
            )
            success = result is not None and result.get("status") == "success"
            if success:
                logger.info(f"Volumen ajustado a {adjusted_level} con éxito.")
            else:
                logger.warning(f"Fallo al ajustar volumen. Respuesta: {result}")
            return success
        except Exception as e:
            logger.error(f"Excepción al ajustar volumen en Philips TV ({ip}:{port}): {e}", exc_info=True)
            return False
    
    async def launch_app(self, ip: str, port: int, app_id: str, class_name: Optional[str] = None, app_name_for_log: Optional[str] = None) -> bool:
        """
        Lanza una aplicación en la TV usando su ID de paquete y opcionalmente el nombre de la clase.
        
        Args:
            ip (str): Dirección IP de la TV.
            port (int): Puerto de la TV.
            app_id (str): El identificador del paquete de la aplicación (ej: "com.netflix.ninja").
            class_name (Optional[str]): El nombre de la clase de la actividad principal (ej: "com.netflix.ninja.MainActivity").
            app_name_for_log (Optional[str]): Nombre amigable de la aplicación para logs.

        Returns:
            bool: True si la aplicación fue lanzada con éxito, False en caso contrario.
        """
        log_app_name = app_name_for_log or app_id
        logger.info(f"Intentando lanzar aplicación '{log_app_name}' (ID: {app_id}, Clase: {class_name or 'N/A'}) en TV {ip}:{port}...")
        try:
            component_data = {
                "packageName": app_id,
                "className": class_name or "" 
            }
            payload = {
                "intent": {
                    "action": "android.intent.action.MAIN", 
                    "component": component_data
                }
            }
            
            result = await self.send_command(
                ip=ip, 
                port=port, 
                endpoint="activities/launch", 
                method="POST", 
                data=payload
            )
            # La lógica de éxito ahora dependerá de si send_command devuelve un diccionario de éxito
            # para el endpoint "activities/launch" (lo cual hará si devuelve 200 OK non-JSON).
            # O si devuelve None porque la TV respondió con un error (ej. 405).
            success = result is not None and result.get("status") == "success"
            logger.info(f"Resultado de lanzar app '{log_app_name}': {result}. Éxito: {success}")
            return success
        except Exception as e: # Esta excepción es por si algo falla ANTES de la llamada o con el resultado
            logger.error(f"Excepción en la lógica de launch_app para '{log_app_name}' en Philips TV ({ip}:{port}): {e}", exc_info=True)
            return False # Asegura que se retorna False en caso de excepción aquí.
            
    async def get_apps(self, ip: str, port: int) -> List[Dict[str, Any]]:
        """Obtiene la lista de aplicaciones instaladas en la TV.

        Args:
            ip (str): Dirección IP de la TV.
            port (int): Puerto de la TV.

        Returns:
            List[Dict[str, Any]]: Una lista de diccionarios, cada uno representando una aplicación.
        """
        logger.info(f"Obteniendo lista de aplicaciones de TV {ip}:{port}...")
        try:
            result = await self.send_command(ip, port, "applications", method="GET")
            if result and "applications" in result and isinstance(result["applications"], list):
                apps_list = result["applications"]
                logger.info(f"Se encontraron {len(apps_list)} aplicaciones.")
                return apps_list
            else:
                logger.warning(f"No se pudo obtener la lista de aplicaciones o el formato es incorrecto. Resultado: {result}")
                return []
        except Exception as e:
            logger.error(f"Excepción al obtener aplicaciones de Philips TV ({ip}:{port}): {e}", exc_info=True)
            return []

    async def open_url_in_browser(self, ip: str, port: int, url: str) -> dict:
        """
        Envía una URL al navegador del TV Philips usando el endpoint /activities/browser
        
        Esta función funciona específicamente para TVs Philips básicos (Linux, no Android)
        que soportan el endpoint /activities/browser.
        
        Args:
            ip (str): Dirección IP de la TV.
            port (int): Puerto de la TV.
            url (str): URL a abrir en el navegador del TV
            
        Returns:
            dict: Resultado de la operación con formato estándar
            {
                "success": bool,
                "message": str,
                "url": str,
                "status_code": int (opcional)
            }
        """
        try:
            # Validar que la URL sea válida
            if not url or not isinstance(url, str):
                return {
                    "success": False,
                    "message": "URL inválida o vacía",
                    "url": url
                }
            
            # Si es YouTube, asegurar formato correcto
            if "youtube.com" in url or "youtu.be" in url:
                video_id = self._extract_youtube_id(url)
                if video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"Enviando URL al navegador del TV {ip}:{port}: {url}")
            
            # Usar el método send_command existente para mantener consistencia
            result = await self.send_command(
                ip=ip,
                port=port,
                endpoint="activities/browser",
                method="POST",
                data={"url": url},
                timeout_seconds=10
            )
            
            if result is not None and result.get("status") == "success":
                logger.info(f"URL enviada exitosamente al TV: {url}")
                return {
                    "success": True,
                    "message": f"URL enviada al navegador del TV: {url}",
                    "url": url,
                    "status_code": 200
                }
            else:
                error_msg = f"Error enviando URL al TV. Respuesta: {result}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "url": url
                }
                    
        except Exception as e:
            error_msg = f"Error inesperado enviando URL al TV {ip}:{port}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "message": error_msg,
                "url": url
            }

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """
        Extrae el ID del video de YouTube de una URL
        
        Args:
            url (str): URL de YouTube
            
        Returns:
            Optional[str]: ID del video o None si no se encuentra
        """
        try:
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
                r'youtube\.com/v/([^&\n?#]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            logger.error(f"Error extrayendo ID de YouTube de URL {url}: {e}")
            return None

    

# --- Ejemplo de uso (requiere una TV Philips accesible en la red) ---
async def main_example():
    """Ejemplo de uso del PhilipsController para probar funcionalidades con una TV Philips real."""
    # ¡CAMBIA ESTO A LA IP DE TU TV Y PUERTO CORRECTO!
    tv_ip = "192.168.0.41"  # Usando la IP de tus logs
    tv_port = 1925           # Puerto estándar para JointSpace HTTP

    controller = PhilipsController()
    logger.info(f"\n--- Iniciando pruebas con TV en {tv_ip}:{tv_port} ---")

    is_connected = await controller.check_connection(tv_ip, tv_port)
    if not is_connected:
        logger.error(f"No se pudo conectar a la TV en {tv_ip}:{tv_port}. Abortando más pruebas.")
        return

    system_info = await controller.send_command(tv_ip, tv_port, "system")
    if system_info:
        logger.info(f"Información del sistema: Nombre: {system_info.get('name', 'N/A')}, Modelo: {system_info.get('model', 'N/A')}")

    # NUEVA PRUEBA: Test de la función open_url_in_browser
    logger.info("\n--- Probando nueva función open_url_in_browser ---")
    test_url = "https://youtube.com/watch?v=wXB8Uczd8j8"
    result = await controller.open_url_in_browser(tv_ip, tv_port, test_url)
    if result["success"]:
        logger.info(f"✅ URL enviada exitosamente: {result['message']}")
    else:
        logger.error(f"❌ Error enviando URL: {result['message']}")

    apps = await controller.get_apps(tv_ip, tv_port)
    if apps:
        logger.info(f"Primeras aplicaciones encontradas (hasta 3 de {len(apps)}):")
        for app_info in apps[:3]: 
            logger.info(f"  - Label: {app_info.get('label', 'N/A')}, ID: {app_info.get('id', app_info.get('packageName', 'N/A'))}")
        netflix_app_id = next((app_info.get('id', app_info.get('packageName')) for app_info in apps if 'netflix' in app_info.get('label', '').lower() or 'netflix' in app_info.get('id', '').lower()), None)
        youtube_app_id = next((app_info.get('id', app_info.get('packageName')) for app_info in apps if 'youtube' in app_info.get('label', '').lower() or 'youtube' in app_info.get('id', '').lower()), "com.google.android.youtube.tv")
    else:
        netflix_app_id = "com.netflix.ninja" 
        youtube_app_id = "com.google.android.youtube.tv"


    logger.info("\n--- Probando envío de tecla 'Home' ---")
    if await controller.send_key(tv_ip, tv_port, "Home"): 
        logger.info("Tecla 'Home' enviada con éxito.")
        await asyncio.sleep(3) 
    else:
        logger.warning("Fallo al enviar tecla 'Home'.")

    logger.info("\n--- Probando ajuste de volumen (con límites de TV) ---")
    test_volumes = [10, -5, 70] 
    for vol_test in test_volumes:
        logger.info(f"Intentando ajustar volumen a: {vol_test}")
        if await controller.set_volume(tv_ip, tv_port, vol_test): 
            logger.info(f"Comando de ajuste de volumen a {vol_test} enviado con éxito.")
        else:
            logger.warning(f"Fallo al ajustar volumen a {vol_test}.")
        await asyncio.sleep(2) 
    
    await asyncio.sleep(1)

    if netflix_app_id:
        logger.info(f"\n--- Intentando lanzar Netflix (ID: {netflix_app_id}) ---")
        # El resultado de launch_app ahora dependerá de si la TV devuelve 200 OK (JSON o non-JSON)
        # o un error como 405. Si es 405, result será None, y success será False.
        if await controller.launch_app(tv_ip, tv_port, netflix_app_id, "Netflix"):
            logger.info("Comando para lanzar Netflix enviado con éxito (TV aceptó el comando).")
        else:
            logger.warning("Fallo al enviar comando para lanzar Netflix (TV pudo haber rechazado el método POST en /activities/launch o hubo otro error).")
        await asyncio.sleep(5) 
    else:
        logger.info("\n--- No se encontró ID de Netflix para probar el lanzamiento. ---")

    if youtube_app_id:
        logger.info(f"\n--- Intentando lanzar YouTube (ID: {youtube_app_id}) ---")
        if await controller.launch_app(tv_ip, tv_port, youtube_app_id, "YouTube"):
            logger.info("Comando para lanzar YouTube enviado con éxito (TV aceptó el comando).")
        else:
            logger.warning("Fallo al enviar comando para lanzar YouTube (TV pudo haber rechazado el método POST en /activities/launch o hubo otro error).")
    else:
        logger.info("\n--- No se encontró ID de YouTube para probar el lanzamiento. ---")


    logger.info("\n--- Pruebas finalizadas ---")

if __name__ == "__main__":
    asyncio.run(main_example())