"""
SUME DOCBLOCK

Nombre: AndroidDiscovery
Tipo: Entradas/Descubrimiento

Entradas:
- Timeout para búsqueda
- IPs para escanear (opcional)

Acciones:
- Busca dispositivos Android en la red mediante escaneo de puertos y ADB
- Conexión automática a dispositivos encontrados

Salidas:
- Lista de dispositivos Android encontrados con metadatos
"""
import asyncio
import logging
import os
import socket
import subprocess
import ipaddress
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger("android_discovery")

# Ruta a ADB - ajusta según tu instalación
ADB_PATH = "C:\\Users\\gatak\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"
if not os.path.exists(ADB_PATH):
    # Buscar en otras ubicaciones comunes
    potential_paths = [
        "adb.exe",  # Si está en PATH
        "C:\\Android\\platform-tools\\adb.exe",
        "C:\\Program Files\\Android\\platform-tools\\adb.exe",
        "C:\\Program Files (x86)\\Android\\platform-tools\\adb.exe",
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            ADB_PATH = path
            break

# Puerto ADB estándar
ADB_PORT = 5555

async def get_local_ips() -> List[str]:
    """Obtiene las IPs locales de todas las interfaces activas."""
    ips = []
    try:
        hostname = socket.gethostname()
        for ip in socket.getaddrinfo(hostname, None):
            if ip[0] == socket.AF_INET:  # Solo IPv4
                local_ip = ip[4][0]
                if not local_ip.startswith('127.'):  # Ignorar loopback
                    ips.append(local_ip)
    except Exception as e:
        logger.error(f"Error obteniendo IPs locales: {e}")
    
    # Reportar IPs encontradas
    logger.info(f"IPs locales detectadas: {ips}")
    logger.info(f"STDG EVENT: get_local_ips - {{'ips': {ips}}}")
    
    return ips

async def scan_network_for_adb(base_ips: Optional[List[str]] = None, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Escanea la red para encontrar dispositivos con el puerto ADB abierto.
    
    Args:
        base_ips: Lista de IPs base para escanear. Si es None, se detectan automáticamente.
        timeout: Tiempo máximo en segundos para completar el escaneo.
        
    Returns:
        Lista de dispositivos encontrados con sus metadatos.
    """
    logger.info(f"STDG EVENT: android_discovery_start - {{'timeout': {timeout}}}")
    
    if not os.path.exists(ADB_PATH):
        logger.error(f"ADB no encontrado en {ADB_PATH}")
        return []
    
    # Obtener IPs locales si no se proporcionan
    if not base_ips:
        base_ips = await get_local_ips()
    
    if not base_ips:
        logger.warning("No se pudieron determinar IPs locales para escaneo")
        return []
    
    # Generar rangos de IP para escanear
    ip_ranges = []
    for base_ip in base_ips:
        # Obtener los primeros 3 octetos de la IP
        base_prefix = '.'.join(base_ip.split('.')[:3])
        ip_ranges.append(base_prefix)
    
    # Conjunto para evitar duplicados
    found_devices = set()
    
    # Primero, verificar dispositivos ya conectados a ADB
    try:
        result = subprocess.run(
            [ADB_PATH, "devices"], 
            capture_output=True, 
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:  # Primera línea es "List of devices attached"
            for line in lines[1:]:
                if not line.strip():
                    continue
                    
                parts = line.split('\t')
                if len(parts) >= 2:
                    device_id = parts[0].strip()
                    status = parts[1].strip()
                    
                    if status == "device" and ":" in device_id:
                        # Esto es un dispositivo conectado por red
                        ip, port = device_id.split(':')
                        found_devices.add(ip)
                        logger.info(f"Dispositivo ADB ya conectado: {ip}:{port}")
    except Exception as e:
        logger.error(f"Error detectando dispositivos ADB existentes: {e}")
    
    # Lista para tareas de escaneo asíncronas
    scan_tasks = []
    
    # Escanear cada rango de IP
    for ip_range in ip_ranges:
        logger.info(f"Escaneando rango de IP: {ip_range}.0/24")
        
        for i in range(1, 255):
            ip = f"{ip_range}.{i}"
            scan_tasks.append(scan_ip_for_adb(ip, found_devices))
    
    # Ejecutar escaneos con timeout
    try:
        await asyncio.wait_for(asyncio.gather(*scan_tasks), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Timeout alcanzado después de {timeout}s, parando escaneo")
    
    # Conectar a dispositivos encontrados y obtener información
    devices = []
    for ip in found_devices:
        try:
            # Intentar conectar vía ADB
            connect_result = subprocess.run(
                [ADB_PATH, "connect", f"{ip}:{ADB_PORT}"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if "connected" in connect_result.stdout.lower():
                # Obtener información del dispositivo
                info_result = subprocess.run(
                    [ADB_PATH, "-s", f"{ip}:{ADB_PORT}", "shell", "getprop | grep -e model -e product -e manufacturer"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Extraer información útil
                info = info_result.stdout
                model = extract_prop(info, "ro.product.model")
                manufacturer = extract_prop(info, "ro.product.manufacturer")
                
                name = f"{manufacturer} {model}" if manufacturer and model else f"Dispositivo Android ({ip})"
                
                devices.append({
                    "ip": ip,
                    "port": ADB_PORT,
                    "name": name,
                    "device_type": "android",
                    "device_id": f"android-{ip.replace('.', '-')}",
                    "manufacturer": manufacturer,
                    "model": model,
                    "connect_method": "adb"
                })
                
                logger.info(f"Dispositivo Android encontrado y conectado: {name} ({ip}:{ADB_PORT})")
        except Exception as e:
            logger.error(f"Error conectando o extrayendo información de {ip}: {e}")
    
    logger.info(f"STDG EVENT: android_discovery_end - {{'found': {len(devices)}}}")
    logger.info(f"Descubrimiento Android completado: {len(devices)} dispositivos encontrados.")
    
    return devices

async def scan_ip_for_adb(ip: str, found_devices: Set[str]) -> None:
    """Escanea una IP específica para verificar si el puerto ADB está abierto."""
    try:
        # Crear socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)  # Timeout breve para cada intento
        
        # Intentar conectar
        result = await asyncio.to_thread(try_connect, sock, ip, ADB_PORT)
        
        if result:
            logger.info(f"Puerto ADB abierto detectado en: {ip}:{ADB_PORT}")
            found_devices.add(ip)
    except Exception:
        pass  # Ignorar errores en escaneo individual

def try_connect(sock: socket.socket, ip: str, port: int) -> bool:
    """Intenta conectar a una IP:puerto y devuelve True si tiene éxito."""
    try:
        sock.connect((ip, port))
        sock.close()
        return True
    except:
        sock.close()
        return False

def extract_prop(props_text: str, prop_name: str) -> Optional[str]:
    """Extrae un valor de propiedad del resultado de getprop."""
    for line in props_text.split('\n'):
        if prop_name in line:
            # Formato típico: [prop.name]: [value]
            value = line.split('[')[-1].split(']')[0]
            return value.strip()
    return None

async def discover_android_devices(timeout: int = 15) -> List[Dict[str, Any]]:
    """
    Función principal para descubrir dispositivos Android en la red.
    
    Args:
        timeout: Tiempo máximo en segundos para la búsqueda.
        
    Returns:
        Lista de dispositivos Android encontrados.
    """
    return await scan_network_for_adb(timeout=timeout)