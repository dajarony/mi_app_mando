"""
SUME DOCBLOCK
Nombre: Servicio de Ping ICMP
Tipo: Lógica/Servicios

Entradas:
- ip_address (str): Dirección IP del dispositivo a verificar.
- timeout (int): Tiempo máximo de espera en segundos.

Acciones:
- Envía un paquete ICMP (ping) a la dirección IP especificada.
- Verifica la respuesta para determinar la disponibilidad del dispositivo.

Salidas:
- bool: True si el dispositivo responde, False en caso contrario.
"""
import asyncio
import os  # ✅ AGREGADO: Importar módulo os
import logging

logger = logging.getLogger("ping_service")

async def ping(ip_address: str, timeout: int = 3) -> bool:
    """
    Verifica si un dispositivo responde en la red mediante ping ICMP.
    
    Args:
        ip_address (str): Dirección IP a verificar.
        timeout (int): Tiempo máximo de espera en segundos.
        
    Returns:
        bool: True si el dispositivo responde, False en caso contrario.
    """
    logger.info(f"Verificando disponibilidad de {ip_address}")
    
    try:
        # Comandos diferentes según sistema operativo
        if os.name == "nt":  # ✅ CORREGIDO: usar os.name en lugar de asyncio.os.name
            cmd = f"ping -n 1 -w {timeout*1000} {ip_address}"
        else:  # Linux/Mac
            cmd = f"ping -c 1 -W {timeout} {ip_address}"
            
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        _, _ = await proc.communicate()
        
        # Si el comando retorna 0, el ping fue exitoso
        return proc.returncode == 0
    except Exception as e:
        logger.error(f"Error al realizar ping a {ip_address}: {e}")
        return False
