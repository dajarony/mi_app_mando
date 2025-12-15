"""
SUME DOCBLOCK

Nombre: DLNA Discovery
Tipo: Entrada

Entradas:
- timeout (int): Tiempo máximo de espera para respuestas en segundos
- use_simulation (bool): Si se deben generar dispositivos simulados

Acciones:
- Escanea la LAN via SSDP buscando MediaRenderers
- Filtra y prioriza TVs (MediaRenderers)
- Fallback automático a búsqueda amplia si no hay resultados
- Obtiene nombre amigable desde descriptor XML y filtra por <deviceType>
- Elimina duplicados por device_id

Salidas:
- List[Dict[str, Any]]: Lista de dispositivos encontrados
"""

import asyncio
import socket
import re
import time
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

logger = logging.getLogger("dlna_discovery")

# STDG trace function (puede reemplazarse por implementación real)
def _trace_event(event: str, details: Dict[str, Any] = None) -> None:
    logger.info(f"STDG EVENT: {event} - {details or {}}")


def _get_local_ips() -> List[str]:
    """Obtiene direcciones IPv4 locales excluyendo localhost"""
    local_ips: List[str] = []
    try:
        hostname = socket.gethostname()
        for family, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
            if family == socket.AF_INET:
                ip = sockaddr[0]
                if not ip.startswith("127."):
                    local_ips.append(ip)
        if not local_ips:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                try:
                    s.connect(("8.8.8.8", 1))
                    local_ips.append(s.getsockname()[0])
                except Exception as e:
                    logger.warning(f"No se pudo determinar IP alterna: {e}")
    except Exception as e:
        logger.error(f"Error al detectar IPs locales: {e}")
        raise
    logger.info(f"IPs locales detectadas: {local_ips}")
    _trace_event("get_local_ips", {"ips": local_ips})
    return local_ips


def _fetch_and_parse_descriptor(location: str) -> Dict[str, Any]:
    """Descarga y parsea el descriptor XML, retornando friendlyName, modelName y deviceType"""
    details = {"friendlyName": "", "modelName": "", "deviceType": ""}
    try:
        resp = requests.get(location, timeout=2)
        xml_root = ET.fromstring(resp.content)
        fn = xml_root.find('.//friendlyName')
        mn = xml_root.find('.//modelName')
        dt = xml_root.find('.//deviceType')
        if fn is not None:
            details['friendlyName'] = fn.text or ''
        if mn is not None:
            details['modelName'] = mn.text or ''
        if dt is not None:
            details['deviceType'] = dt.text or ''
    except Exception as e:
        logger.warning(f"Error parseando descriptor {location}: {e}")
    return details


def _search_ssdp_for_target(local_ip: str, search_target: str, timeout: int, filter_media: bool = True) -> List[Dict[str, Any]]:
    """Realiza búsqueda SSDP M-SEARCH para un target y devuelve dispositivos"""
    devices: List[Dict[str, Any]] = []
    locations: set = set()
    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    SSDP_MX = 3

    search_msg = "\r\n".join([
        "M-SEARCH * HTTP/1.1",
        f"HOST: {SSDP_ADDR}:{SSDP_PORT}",
        'MAN: "ssdp:discover"',
        f"MX: {SSDP_MX}",
        f"ST: {search_target}",
        "", ""
    ]).encode()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
            if local_ip:
                try:
                    sock.bind((local_ip, 0))
                except Exception as e:
                    logger.warning(f"No se pudo enlazar a {local_ip}: {e}")
            sock.settimeout(1)
            logger.info(f"Enviando M-SEARCH ST={search_target} desde {local_ip}")
            sock.sendto(search_msg, (SSDP_ADDR, SSDP_PORT))

            start = time.time()
            sub_timeout = min(timeout / 2, 5)
            while time.time() - start < sub_timeout:
                try:
                    data, addr = sock.recvfrom(4096)
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error en recvfrom: {e}")
                    break

                response = data.decode(errors="ignore")
                location_match = re.search(r"LOCATION:\s*(.*)", response, re.IGNORECASE)
                usn_match = re.search(r"USN:\s*(.*)", response, re.IGNORECASE)
                if not location_match:
                    continue
                location = location_match.group(1).strip()
                if location in locations:
                    continue
                locations.add(location)

                usn = usn_match.group(1).strip() if usn_match else ""

                # Parse descriptor for deviceType
                desc = _fetch_and_parse_descriptor(location)
                dtype = desc.get('deviceType', '')
                is_media = 'MediaRenderer' in dtype
                if filter_media and not is_media:
                    continue

                # Friendly name or fallback
                name = desc.get('friendlyName') or desc.get('modelName') or f"MediaRenderer en {addr[0]}"

                device_id = usn.split(":")[-1] if ":" in usn else f"DEV{len(devices)+1}"

                devices.append({
                    "device_id": device_id,
                    "name": name,
                    "ip": addr[0],
                    "location": location,
                    "server": desc.get('modelName', ''),
                    "device_type": "MediaRenderer" if is_media else "Device"
                })
    except Exception as e:
        logger.error(f"Error durante SSDP search {search_target} en {local_ip}: {e}")
    _trace_event("ssdp_search", {"local_ip": local_ip, "search_target": search_target, "found": len(devices)})
    return devices


async def discover_dlna(timeout: int = 20, use_simulation: bool = False) -> List[Dict[str, Any]]:
    """Implementación de descubrimiento SSDP/DLNA con fallback automático y filtrado por descriptor."""
    _trace_event("discover_dlna_start", {"timeout": timeout, "use_simulation": use_simulation})
    local_ips = _get_local_ips() or [""]
    PRIMARY_TARGETS = ["urn:schemas-upnp-org:device:MediaRenderer:1"]
    FALLBACK_TARGETS = ["ssdp:all", "upnp:rootdevice"]

    loop = asyncio.get_running_loop()
    # Primera fase: TVs
    tasks = [
        loop.run_in_executor(None, _search_ssdp_for_target, ip, tgt, timeout, True)
        for ip in local_ips for tgt in PRIMARY_TARGETS
    ]
    results = await asyncio.gather(*tasks)
    devices = [dev for sub in results for dev in sub]

    # Fallback si no hay TVs reales
    if not devices and not use_simulation:
        logger.info("No se encontraron TVs; iniciando búsqueda amplia (fallback)")
        _trace_event("fallback_start")
        fb_tasks = [
            loop.run_in_executor(None, _search_ssdp_for_target, ip, tgt, timeout, False)
            for ip in local_ips for tgt in FALLBACK_TARGETS
        ]
        fb_results = await asyncio.gather(*fb_tasks)
        devices = [dev for sub in fb_results for dev in sub]
        _trace_event("fallback_end", {"found": len(devices)})

    # Eliminar duplicados por device_id
    unique: Dict[str, Dict[str, Any]] = {}
    for dev in devices:
        if dev["device_id"] not in unique:
            unique[dev["device_id"]] = dev
    devices = list(unique.values())

    # Simulación si sigue vacío y está habilitada
    if not devices and use_simulation:
        logger.info("No se encontraron dispositivos reales; generando simulados")
        devices = [
            {"device_id": "TV1", "name": "Samsung TV Sala (Simulado)", "ip": "192.168.1.100", "model": "Samsung Q60", "device_type": "MediaRenderer"},
            {"device_id": "TV2", "name": "LG TV Dormitorio (Simulado)", "ip": "192.168.1.101", "model": "LG C1", "device_type": "MediaRenderer"}
        ]
        _trace_event("discover_simulation", {"simulated_count": len(devices)})

    _trace_event("discover_dlna_end", {"found": len(devices)})
    logger.info(f"Descubrimiento completado: {len(devices)} dispositivos encontrados.")
    return devices
