"""
Servidor WebRTC para Screen Mirroring

Nombre: Servidor WebRTC para Screen Mirroring
Tipo: Lógica

Entradas:
- config (dict): Configuración para iniciar el stream de mirroring (ej. detalles de la sesión).

Acciones:
- Configura un servidor WebRTC real con aiortc
- Captura la pantalla usando pyautogui/pillow
- Transmite el video en tiempo real
- Maneja la señalización WebRTC

Salidas:
- dict: Un diccionario que contiene la URL del stream de mirroring y datos de conexión.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, asdict
import time

# WebRTC y multimedia
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer, MediaRelay
from av import VideoFrame
import cv2
import numpy as np

# Screen capture
try:
    import pyautogui
    import PIL.Image
    SCREEN_CAPTURE_AVAILABLE = True
except ImportError:
    SCREEN_CAPTURE_AVAILABLE = False

# FastAPI para la API
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StreamConfig:
    """Configuración para el stream de mirroring"""
    session_id: str
    quality: str = "medium"  # low, medium, high
    fps: int = 15
    resolution: tuple = (1280, 720)
    enable_audio: bool = False
    ice_servers: list = None
    
    def __post_init__(self):
        if self.ice_servers is None:
            self.ice_servers = [
                {"urls": "stun:stun.l.google.com:19302"},
                {"urls": "stun:stun1.l.google.com:19302"}
            ]

class ScreenCaptureTrack(VideoStreamTrack):
    """Track personalizado para captura de pantalla"""
    
    def __init__(self, config: StreamConfig):
        super().__init__()
        self.config = config
        self.fps = config.fps
        self.resolution = config.resolution
        
        # Configurar calidad según la configuración
        if config.quality == "low":
            self.resolution = (640, 360)
            self.fps = 10
        elif config.quality == "medium":
            self.resolution = (1280, 720)
            self.fps = 15
        elif config.quality == "high":
            self.resolution = (1920, 1080)
            self.fps = 30
            
        logger.info(f"Screen capture initialized: {self.resolution}@{self.fps}fps")
    
    async def recv(self):
        """Captura y envía frames de la pantalla"""
        pts, time_base = await self.next_timestamp()
        
        try:
            # Capturar pantalla
            screenshot = pyautogui.screenshot()
            
            # Redimensionar si es necesario
            if screenshot.size != self.resolution:
                screenshot = screenshot.resize(self.resolution, PIL.Image.Resampling.LANCZOS)
            
            # Convertir a numpy array para OpenCV
            frame_array = np.array(screenshot)
            frame_array = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            
            # Crear VideoFrame
            frame = VideoFrame.from_ndarray(frame_array, format="bgr24")
            frame.pts = pts
            frame.time_base = time_base
            
            return frame
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            # Crear frame negro en caso de error
            black_frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
            frame = VideoFrame.from_ndarray(black_frame, format="bgr24")
            frame.pts = pts
            frame.time_base = time_base
            return frame

class WebRTCSession:
    """Sesión WebRTC individual"""
    
    def __init__(self, session_id: str, config: StreamConfig):
        self.session_id = session_id
        self.config = config
        self.pc: Optional[RTCPeerConnection] = None
        self.screen_track: Optional[ScreenCaptureTrack] = None
        self.created_at = time.time()
        
    async def create_peer_connection(self) -> RTCPeerConnection:
        """Crea una nueva conexión peer"""
        # Configuración ICE
        ice_servers = [RTCIceServer(urls=server["urls"]) for server in self.config.ice_servers]
        configuration = RTCConfiguration(iceServers=ice_servers)
        
        # Crear peer connection
        self.pc = RTCPeerConnection(configuration)
        
        # Agregar track de video (pantalla)
        self.screen_track = ScreenCaptureTrack(self.config)
        self.pc.addTrack(self.screen_track)
        
        # Event handlers
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Session {self.session_id}: Connection state is {self.pc.connectionState}")
            
        @self.pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"Session {self.session_id}: ICE connection state is {self.pc.iceConnectionState}")
            
        return self.pc
    
    async def handle_offer(self, offer_sdp: str) -> str:
        """Maneja una oferta SDP y retorna la respuesta"""
        if not self.pc:
            await self.create_peer_connection()
            
        # Establecer descripción remota
        await self.pc.setRemoteDescription(RTCSessionDescription(sdp=offer_sdp, type="offer"))
        
        # Crear respuesta
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        
        return answer.sdp
    
    async def add_ice_candidate(self, candidate_data: dict):
        """Agrega un candidato ICE"""
        if self.pc:
            await self.pc.addIceCandidate(candidate_data)
    
    async def close(self):
        """Cierra la sesión"""
        if self.screen_track:
            self.screen_track.stop()
        if self.pc:
            await self.pc.close()
        logger.info(f"Session {self.session_id} closed")

class WebRTCServer:
    """Clase principal para gestionar el servidor WebRTC y el screen mirroring."""
    
    def __init__(self):
        self.sessions: Dict[str, WebRTCSession] = {}
        self.active_connections: Set[WebSocket] = set()
        
    async def start_stream(self, config: dict) -> dict:
        """Inicia un stream de mirroring de pantalla.

        Args:
            config (dict): Configuración para el stream.

        Returns:
            dict: Un diccionario con la URL del stream y datos de sesión.
        """
        
        if not SCREEN_CAPTURE_AVAILABLE:
            raise RuntimeError("Screen capture not available. Install: pip install pyautogui pillow")
        
        # Crear configuración
        session_id = str(uuid.uuid4())
        stream_config = StreamConfig(
            session_id=session_id,
            quality=config.get("quality", "medium"),
            fps=config.get("fps", 15),
            resolution=tuple(config.get("resolution", (1280, 720))),
            enable_audio=config.get("enable_audio", False),
            ice_servers=config.get("ice_servers")
        )
        
        # Crear sesión
        session = WebRTCSession(session_id, stream_config)
        self.sessions[session_id] = session
        
        logger.info(f"Created screen mirroring session: {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "stream_url": f"http://localhost:8000/screen-mirror/{session_id}",
            "websocket_url": f"ws://localhost:8000/ws/{session_id}",
            "config": asdict(stream_config),
            "message": "Screen mirroring session created successfully"
        }
    
    async def get_session(self, session_id: str) -> Optional[WebRTCSession]:
        """Obtiene una sesión por ID"""
        return self.sessions.get(session_id)
    
    async def remove_session(self, session_id: str):
        """Elimina una sesión"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            await session.close()
            del self.sessions[session_id]
            logger.info(f"Removed session: {session_id}")
    
    async def handle_webrtc_offer(self, session_id: str, offer_sdp: str) -> Optional[str]:
        """Maneja una oferta WebRTC"""
        session = await self.get_session(session_id)
        if not session:
            return None
            
        return await session.handle_offer(offer_sdp)
    
    async def handle_ice_candidate(self, session_id: str, candidate_data: dict):
        """Maneja un candidato ICE"""
        session = await self.get_session(session_id)
        if session:
            await session.add_ice_candidate(candidate_data)
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """Obtiene información de una sesión"""
        session = self.sessions.get(session_id)
        if not session:
            return None
            
        return {
            "session_id": session_id,
            "config": asdict(session.config),
            "created_at": session.created_at,
            "connection_state": session.pc.connectionState if session.pc else "not_connected",
            "ice_connection_state": session.pc.iceConnectionState if session.pc else "new"
        }
    
    def list_active_sessions(self) -> list:
        """Lista todas las sesiones activas"""
        return [
            {
                "session_id": session_id,
                "created_at": session.created_at,
                "config": asdict(session.config)
            }
            for session_id, session in self.sessions.items()
        ]

# ===== MODELOS PYDANTIC =====

class StreamStartRequest(BaseModel):
    quality: str = "medium"
    fps: int = 15
    resolution: list = [1280, 720]
    enable_audio: bool = False

class WebRTCOfferRequest(BaseModel):
    session_id: str
    sdp: str
    type: str = "offer"

class ICECandidateRequest(BaseModel):
    session_id: str
    candidate: str
    sdpMLineIndex: int
    sdpMid: str

# ===== INTEGRACIÓN CON FASTAPI =====

# Instancia global del servidor WebRTC
webrtc_server = WebRTCServer()

# Endpoints para integrar con tu aplicación FastAPI existente

async def add_webrtc_routes(app: FastAPI):
    """Agrega las rutas WebRTC a tu aplicación FastAPI existente"""
    
    @app.post("/screen-mirror/start")
    async def start_screen_mirror(request: StreamStartRequest):
        """Inicia una nueva sesión de screen mirroring"""
        try:
            config = {
                "quality": request.quality,
                "fps": request.fps,
                "resolution": tuple(request.resolution),
                "enable_audio": request.enable_audio
            }
            
            result = await webrtc_server.start_stream(config)
            return result
            
        except Exception as e:
            logger.error(f"Error starting screen mirror: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/screen-mirror/{session_id}")
    async def get_screen_mirror_page(session_id: str):
        """Retorna la página HTML para ver el screen mirror"""
        
        session_info = webrtc_server.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # HTML básico para el cliente WebRTC
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Screen Mirror - {session_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
                video {{ width: 100%; max-width: 1000px; background: #000; border-radius: 4px; }}
                .controls {{ margin: 20px 0; }}
                button {{ padding: 10px 20px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
                button:hover {{ background: #0056b3; }}
                .status {{ padding: 10px; margin: 10px 0; border-radius: 4px; }}
                .status.connecting {{ background: #fff3cd; border: 1px solid #ffeaa7; }}
                .status.connected {{ background: #d4edda; border: 1px solid #c3e6cb; }}
                .status.failed {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Screen Mirror</h1>
                <div id="status" class="status connecting">Conectando...</div>
                
                <video id="remoteVideo" autoplay muted controls></video>
                
                <div class="controls">
                    <button onclick="startConnection()">Conectar</button>
                    <button onclick="stopConnection()">Desconectar</button>
                    <button onclick="toggleFullscreen()">Pantalla Completa</button>
                </div>
                
                <div>
                    <h3>Información de la Sesión</h3>
                    <p><strong>Session ID:</strong> {session_id}</p>
                    <p><strong>Calidad:</strong> {session_info['config']['quality']}</p>
                    <p><strong>Resolución:</strong> {session_info['config']['resolution']}</p>
                    <p><strong>FPS:</strong> {session_info['config']['fps']}</p>
                </div>
            </div>

            <script>
                const sessionId = '{session_id}';
                const wsUrl = `ws://localhost:8000/ws/${{sessionId}}`;
                
                let pc = null;
                let ws = null;
                const remoteVideo = document.getElementById('remoteVideo');
                const statusDiv = document.getElementById('status');
                
                function updateStatus(message, className = 'connecting') {{
                    statusDiv.textContent = message;
                    statusDiv.className = `status ${{className}}`;
                }}
                
                async function startConnection() {{
                    try {{
                        updateStatus('Iniciando conexión...', 'connecting');
                        
                        // Crear peer connection
                        pc = new RTCPeerConnection({{
                            iceServers: [
                                {{ urls: 'stun:stun.l.google.com:19302' }},
                                {{ urls: 'stun:stun1.l.google.com:19302' }}
                            ]
                        }});
                        
                        // Manejar stream remoto
                        pc.ontrack = (event) => {{
                            remoteVideo.srcObject = event.streams[0];
                            updateStatus('Conectado - Recibiendo video', 'connected');
                        }};
                        
                        // Manejar cambios de estado
                        pc.onconnectionstatechange = () => {{
                            console.log('Connection state:', pc.connectionState);
                            if (pc.connectionState === 'failed') {{
                                updateStatus('Conexión fallida', 'failed');
                            }}
                        }};
                        
                        // Conectar WebSocket para señalización
                        ws = new WebSocket(wsUrl);
                        
                        ws.onopen = async () => {{
                            console.log('WebSocket connected');
                            
                            // Crear oferta
                            const offer = await pc.createOffer();
                            await pc.setLocalDescription(offer);
                            
                            // Enviar oferta
                            ws.send(JSON.stringify({{
                                type: 'offer',
                                sdp: offer.sdp
                            }}));
                        }};
                        
                        ws.onmessage = async (event) => {{
                            const message = JSON.parse(event.data);
                            
                            if (message.type === 'answer') {{
                                await pc.setRemoteDescription(new RTCSessionDescription({{
                                    type: 'answer',
                                    sdp: message.sdp
                                }}));
                            }} else if (message.type === 'ice-candidate') {{
                                await pc.addIceCandidate(new RTCIceCandidate(message.candidate));
                            }}
                        }};
                        
                        // Manejar candidatos ICE
                        pc.onicecandidate = (event) => {{
                            if (event.candidate && ws.readyState === WebSocket.OPEN) {{
                                ws.send(JSON.stringify({{
                                    type: 'ice-candidate',
                                    candidate: event.candidate
                                }}));
                            }}
                        }};
                        
                    }} catch (error) {{
                        console.error('Error starting connection:', error);
                        updateStatus('Error en la conexión: ' + error.message, 'failed');
                    }}
                }}
                
                function stopConnection() {{
                    if (pc) {{
                        pc.close();
                        pc = null;
                    }}
                    if (ws) {{
                        ws.close();
                        ws = null;
                    }}
                    remoteVideo.srcObject = null;
                    updateStatus('Desconectado', 'connecting');
                }}
                
                function toggleFullscreen() {{
                    if (document.fullscreenElement) {{
                        document.exitFullscreen();
                    }} else {{
                        remoteVideo.requestFullscreen();
                    }}
                }}
                
                // Auto-conectar al cargar la página
                window.addEventListener('load', () => {{
                    setTimeout(startConnection, 1000);
                }});
                
                // Limpiar al cerrar la página
                window.addEventListener('beforeunload', stopConnection);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    
    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        """WebSocket para señalización WebRTC"""
        await websocket.accept()
        webrtc_server.active_connections.add(websocket)
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message["type"] == "offer":
                    # Manejar oferta
                    answer_sdp = await webrtc_server.handle_webrtc_offer(session_id, message["sdp"])
                    if answer_sdp:
                        await websocket.send_text(json.dumps({
                            "type": "answer",
                            "sdp": answer_sdp
                        }))
                
                elif message["type"] == "ice-candidate":
                    # Manejar candidato ICE
                    await webrtc_server.handle_ice_candidate(session_id, message["candidate"])
                    
        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")
        finally:
            webrtc_server.active_connections.discard(websocket)
    
    @app.get("/screen-mirror/{session_id}/info")
    async def get_session_info(session_id: str):
        """Obtiene información de una sesión"""
        info = webrtc_server.get_session_info(session_id)
        if not info:
            raise HTTPException(status_code=404, detail="Session not found")
        return info
    
    @app.delete("/screen-mirror/{session_id}")
    async def stop_session(session_id: str):
        """Detiene una sesión de mirroring"""
        await webrtc_server.remove_session(session_id)
        return {"message": f"Session {session_id} stopped"}
    
    @app.get("/screen-mirror")
    async def list_sessions():
        """Lista todas las sesiones activas"""
        return {
            "active_sessions": webrtc_server.list_active_sessions(),
            "total_sessions": len(webrtc_server.sessions)
        }

# Función helper para agregar las rutas a tu app existente
def setup_webrtc_routes(app: FastAPI):
    """Setup function para agregar a tu aplicación existente"""
    asyncio.create_task(add_webrtc_routes(app))

if __name__ == "__main__":
    # Ejemplo de uso standalone
    import uvicorn
    
    app = FastAPI(title="WebRTC Screen Mirroring Server")
    
    # Agregar las rutas WebRTC
    asyncio.run(add_webrtc_routes(app))
    
    # Ejecutar servidor
    uvicorn.run(app, host="0.0.0.0", port=8000)