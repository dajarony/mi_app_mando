import requests
import json
import re
from urllib.parse import urlparse, parse_qs

class BasicPhilipsTVController:
    def __init__(self, tv_ip):
        self.tv_ip = tv_ip
        self.base_url = f"http://{tv_ip}:1925/6"
    
    def send_key(self, key):
        """Envía una tecla específica al TV"""
        try:
            data = {"key": key}
            response = requests.post(f"{self.base_url}/input/key", json=data, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending key {key}: {e}")
            return False
    
    def get_power_state(self):
        """Obtiene el estado de energía del TV"""
        try:
            response = requests.get(f"{self.base_url}/powerstate", timeout=5)
            if response.status_code == 200:
                return response.json().get("powerstate")
        except Exception as e:
            print(f"Error getting power state: {e}")
        return None
    
    def extract_youtube_id(self, url):
        """Extrae el ID del video de YouTube de una URL"""
        # Patrones comunes de URLs de YouTube
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def cast_youtube_to_browser(self, youtube_url):
        """Intenta abrir YouTube en el navegador del TV"""
        try:
            # Extraer ID del video
            video_id = self.extract_youtube_id(youtube_url)
            if not video_id:
                return False, "URL de YouTube inválida"
            
            # Intentar abrir el navegador con la URL de YouTube
            browser_data = {
                "url": f"https://www.youtube.com/watch?v={video_id}"
            }
            
            response = requests.post(
                f"{self.base_url}/activities/browser", 
                json=browser_data, 
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Video enviado al navegador del TV"
            else:
                return False, f"Error {response.status_code}: {response.text}"
                
        except Exception as e:
            return False, f"Error: {e}"
    
    def open_source_menu(self):
        """Abre el menú de fuentes del TV"""
        return self.send_key("Source")
    
    def turn_on_tv(self):
        """Enciende el TV si está en standby"""
        power_state = self.get_power_state()
        if power_state == "Standby":
            return self.send_key("Standby")
        return True
    
    def volume_up(self):
        """Sube el volumen"""
        return self.send_key("VolumeUp")
    
    def volume_down(self):
        """Baja el volumen"""
        return self.send_key("VolumeDown")
    
    def home(self):
        """Va al menú principal"""
        return self.send_key("Home")

# Ejemplo de uso
def test_youtube_cast():
    tv = BasicPhilipsTVController("192.168.0.41")
    
    print("1. Verificando estado del TV...")
    power_state = tv.get_power_state()
    print(f"Estado: {power_state}")
    
    if power_state == "Standby":
        print("2. Encendiendo TV...")
        tv.turn_on_tv()
    
    print("3. Intentando enviar video de YouTube al navegador...")
    youtube_url = "https://youtube.com/watch?v=wXB8Uczd8j8"
    success, message = tv.cast_youtube_to_browser(youtube_url)
    
    print(f"Resultado: {message}")
    
    if not success:
        print("4. Alternativa: Abriendo menú de fuentes...")
        tv.open_source_menu()
        print("Cambia manualmente a una fuente HDMI con Chromecast/dispositivo de cast")

if __name__ == "__main__":
    test_youtube_cast()