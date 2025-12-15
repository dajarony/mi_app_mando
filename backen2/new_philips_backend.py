from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import re
import logging
from typing import Optional, Dict, Any
import asyncio
import httpx

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Philips TV Controller", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class CastRequest(BaseModel):
    url: str
    tv_ip: str = "192.168.0.41"

class TVCommand(BaseModel):
    command: str
    tv_ip: str = "192.168.0.41"

class VolumeControl(BaseModel):
    action: str  # "up", "down", "mute"
    tv_ip: str = "192.168.0.41"

class ChannelControl(BaseModel):
    action: str  # "up", "down" o número de canal
    tv_ip: str = "192.168.0.41"

class PhilipsTVController:
    """Controlador para TV Philips básico (Linux, no Android)"""
    
    def __init__(self, tv_ip: str):
        self.tv_ip = tv_ip
        self.base_url = f"http://{tv_ip}:1925/6"
        self.timeout = 10
    
    async def send_key(self, key: str) -> Dict[str, Any]:
        """Envía una tecla específica al TV"""
        try:
            async with httpx.AsyncClient() as client:
                data = {"key": key}
                response = await client.post(
                    f"{self.base_url}/input/key", 
                    json=data, 
                    timeout=self.timeout
                )
                
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "message": f"Tecla '{key}' enviada" if response.status_code == 200 else f"Error enviando tecla: {response.text}",
                    "response": response.text
                }
        except Exception as e:
            logger.error(f"Error sending key {key}: {e}")
            return {
                "success": False,
                "message": f"Error enviando tecla {key}: {str(e)}"
            }
    
    async def get_power_state(self) -> Dict[str, Any]:
        """Obtiene el estado de energía del TV"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/powerstate", timeout=self.timeout)
                
                if response.status_code == 200:
                    power_data = response.json()
                    return {
                        "success": True,
                        "powerstate": power_data.get("powerstate"),
                        "message": f"TV está {power_data.get('powerstate')}"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Error obteniendo estado: {response.text}"
                    }
        except Exception as e:
            logger.error(f"Error getting power state: {e}")
            return {
                "success": False,
                "message": f"Error obteniendo estado: {str(e)}"
            }
    
    async def get_volume_info(self) -> Dict[str, Any]:
        """Obtiene información del volumen"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/audio/volume", timeout=self.timeout)
                
                if response.status_code == 200:
                    volume_data = response.json()
                    return {
                        "success": True,
                        "volume": volume_data,
                        "message": "Información de volumen obtenida"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Error obteniendo volumen: {response.text}"
                    }
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            return {
                "success": False,
                "message": f"Error obteniendo volumen: {str(e)}"
            }
    
    def extract_youtube_id(self, url: str) -> Optional[str]:
        """Extrae el ID del video de YouTube de una URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\\n?#]+)',
            r'youtube\.com/v/([^&\\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def cast_url_to_browser(self, url: str) -> Dict[str, Any]:
        """Envía una URL al navegador del TV"""
        try:
            # Si es YouTube, asegurar formato correcto
            if "youtube.com" in url or "youtu.be" in url:
                video_id = self.extract_youtube_id(url)
                if video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"
            
            async with httpx.AsyncClient() as client:
                browser_data = {"url": url}
                response = await client.post(
                    f"{self.base_url}/activities/browser", 
                    json=browser_data, 
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": f"URL enviada al navegador del TV: {url}",
                        "url": url
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Error enviando URL: {response.text}",
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            logger.error(f"Error casting URL {url}: {e}")
            return {
                "success": False,
                "message": f"Error enviando URL: {str(e)}"
            }
    
    async def turn_on_if_standby(self) -> Dict[str, Any]:
        """Enciende el TV si está en standby"""
        power_state = await self.get_power_state()
        
        if power_state.get("success") and power_state.get("powerstate") == "Standby":
            return await self.send_key("Standby")
        
        return {
            "success": True,
            "message": "TV ya está encendido o estado desconocido"
        }

# Endpoints de la API

@app.get("/")
async def root():
    return {
        "message": "Philips TV Controller API",
        "version": "1.0.0",
        "endpoints": [
            "/tv/status",
            "/tv/cast-url",
            "/tv/volume",
            "/tv/channels",
            "/tv/remote",
            "/tv/power"
        ]
    }

@app.get("/tv/status")
async def get_tv_status(tv_ip: str = "192.168.0.41"):
    """Obtiene el estado completo del TV"""
    controller = PhilipsTVController(tv_ip)
    
    # Obtener información básica
    power_state = await controller.get_power_state()
    volume_info = await controller.get_volume_info()
    
    return {
        "tv_ip": tv_ip,
        "power": power_state,
        "volume": volume_info,
        "timestamp": "2025-07-03T12:37:32Z"
    }

@app.post("/tv/cast-url")
async def cast_url_to_tv(request: CastRequest):
    """Envía una URL al navegador del TV (especialmente YouTube)"""
    controller = PhilipsTVController(request.tv_ip)
    
    # Primero asegurar que el TV esté encendido
    await controller.turn_on_if_standby()
    
    # Pequeña pausa para que el TV responda
    await asyncio.sleep(1)
    
    # Enviar la URL al navegador
    result = await controller.cast_url_to_browser(request.url)
    
    logger.info(f"Cast URL {request.url} to TV {request.tv_ip}: {result}")
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result

@app.post("/tv/volume")
async def control_volume(request: VolumeControl):
    """Controla el volumen del TV"""
    controller = PhilipsTVController(request.tv_ip)
    
    key_map = {
        "up": "VolumeUp",
        "down": "VolumeDown", 
        "mute": "Mute"
    }
    
    if request.action not in key_map:
        raise HTTPException(status_code=400, detail=f"Acción inválida. Use: {list(key_map.keys())}")
    
    result = await controller.send_key(key_map[request.action])
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result

@app.post("/tv/channels")
async def control_channels(request: ChannelControl):
    """Controla los canales del TV"""
    controller = PhilipsTVController(request.tv_ip)
    
    if request.action == "up":
        result = await controller.send_key("ChannelStepUp")
    elif request.action == "down":
        result = await controller.send_key("ChannelStepDown")
    elif request.action.isdigit():
        # Enviar dígitos individuales
        results = []
        for digit in request.action:
            digit_result = await controller.send_key(f"Digit{digit}")
            results.append(digit_result)
            await asyncio.sleep(0.3)  # Pausa entre dígitos
        
        result = {
            "success": all(r.get("success") for r in results),
            "message": f"Canal {request.action} enviado",
            "details": results
        }
    else:
        raise HTTPException(status_code=400, detail="Acción inválida. Use 'up', 'down' o un número de canal")
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result

@app.post("/tv/remote")
async def send_remote_command(request: TVCommand):
    """Envía comandos del control remoto al TV"""
    controller = PhilipsTVController(request.tv_ip)
    
    # Mapeo de comandos disponibles
    available_commands = {
        "power": "Standby",
        "home": "Home",
        "back": "Back",
        "up": "CursorUp",
        "down": "CursorDown",
        "left": "CursorLeft",
        "right": "CursorRight",
        "ok": "Confirm",
        "menu": "Home",
        "source": "Source",
        "info": "Info",
        "guide": "Guide",
        "exit": "Back",
        "red": "RedColour",
        "green": "GreenColour", 
        "yellow": "YellowColour",
        "blue": "BlueColour",
        "play": "Play",
        "pause": "Pause",
        "stop": "Stop",
        "rewind": "Rewind",
        "forward": "FastForward"
    }
    
    if request.command not in available_commands:
        raise HTTPException(
            status_code=400, 
            detail=f"Comando inválido. Comandos disponibles: {list(available_commands.keys())}"
        )
    
    result = await controller.send_key(available_commands[request.command])
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result

@app.post("/tv/power")
async def toggle_power(tv_ip: str = "192.168.0.41"):
    """Alterna el estado de encendido/apagado del TV"""
    controller = PhilipsTVController(tv_ip)
    
    result = await controller.send_key("Standby")
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result

@app.get("/tv/available-commands")
async def get_available_commands():
    """Lista todos los comandos disponibles"""
    return {
        "remote_commands": [
            "power", "home", "back", "up", "down", "left", "right", "ok",
            "menu", "source", "info", "guide", "exit", "red", "green", 
            "yellow", "blue", "play", "pause", "stop", "rewind", "forward"
        ],
        "volume_commands": ["up", "down", "mute"],
        "channel_commands": ["up", "down", "número_de_canal"],
        "special_functions": ["cast-url", "status", "power"]
    }

# Endpoint específico para YouTube (tu caso de uso original)
@app.post("/tv/cast-youtube")
async def cast_youtube(url: str, tv_ip: str = "192.168.0.41"):
    """Endpoint específico para enviar videos de YouTube al TV"""
    
    # Validar que es una URL de YouTube
    if not ("youtube.com" in url or "youtu.be" in url):
        raise HTTPException(status_code=400, detail="URL debe ser de YouTube")
    
    controller = PhilipsTVController(tv_ip)
    
    # Enciender TV si está en standby
    await controller.turn_on_if_standby()
    await asyncio.sleep(1)
    
    # Enviar al navegador
    result = await controller.cast_url_to_browser(url)
    
    logger.info(f"YouTube cast {url} to TV {tv_ip}: {result}")
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return {
        "success": True,
        "message": "Video de YouTube enviado al TV",
        "url": url,
        "tv_ip": tv_ip
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
