"""
SUME DOCBLOCK

Nombre: AndroidControl
Tipo: Lógica/Servicios

Entradas:
- device (TVDevice): Objeto con información del dispositivo Android TV
- command (str): Comando ADB a ejecutar

Acciones:
- Conecta vía ADB al dispositivo y ejecuta el comando especificado

Salidas:
- dict: Resultado de la operación ADB
"""
import logging
import subprocess
import platform
from typing import Dict, Any
import asyncio
import concurrent.futures

from sumetv.logica.Modelos.tv_device import TVDevice

logger = logging.getLogger("android_control")

# Mapeo de comandos simples a comandos ADB keyevent
KEY_MAPPING = {
    "up": "input keyevent 19",
    "down": "input keyevent 20",
    "left": "input keyevent 21",
    "right": "input keyevent 22",
    "ok": "input keyevent 23",
    "back": "input keyevent 4",
    "home": "input keyevent 3",
    "menu": "input keyevent 82",
    "power": "input keyevent 26",
    "volup": "input keyevent 24",
    "voldown": "input keyevent 25",
    # Puedes añadir más mapeos según sea necesario
}

def run_command(cmd_list):
    """Ejecuta un comando en un subproceso y devuelve la salida"""
    try:
        # Para Windows, usar subprocess.CREATE_NO_WINDOW para evitar ventanas cmd
        extra_args = {}
        if platform.system() == 'Windows':
            extra_args['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        
        process = subprocess.run(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **extra_args
        )
        return {
            'returncode': process.returncode,
            'stdout': process.stdout.strip() if process.stdout else "",
            'stderr': process.stderr.strip() if process.stderr else ""
        }
    except Exception as e:
        return {
            'returncode': -1,
            'stdout': "",
            'stderr': str(e)
        }

async def run_command_async(cmd_list):
    """Ejecuta un comando en un hilo separado para no bloquear el loop de eventos"""
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, run_command, cmd_list)

async def send_adb_command(device: TVDevice, command: str) -> Dict[str, Any]:
    """
    Envía un comando ADB a un dispositivo Android
    
    Args:
        device: Objeto TVDevice con información del dispositivo
        command: Comando a ejecutar (se traducirá si es un comando simple)
        
    Returns:
        Diccionario con el resultado de la operación
    """
    logger.info(f"STDG EVENT: adb_command_start - {{'device_id': '{device.device_id}', 'command': '{command}'}}")
    
    # Traducir el comando simple a comando ADB si existe en el mapeo
    adb_command = KEY_MAPPING.get(command, command)
    logger.info(f"Enviando comando ADB a {device.name} ({device.ip}): {command}")
    
    # Conectar al dispositivo
    device_address = f"{device.ip}:{device.port}"
    logger.info(f"Conectando a dispositivo: {device_address}")
    
    try:
        # Primero conectar al dispositivo (si no está ya conectado)
        connect_result = await run_command_async(['adb', 'connect', device_address])
        connect_output = connect_result['stdout']
        connect_error = connect_result['stderr']
        
        if connect_result['returncode'] != 0 or "unable to connect" in connect_output.lower() or "cannot connect" in connect_output.lower() or connect_error:
            error_msg = connect_error if connect_error else connect_output
            logger.error(f"No se pudo conectar a {device.name} ({device_address}): {error_msg}")
            return {
                "status": "error",
                "device_id": device.device_id,
                "message": f"Error de conexión a {device.name}: {error_msg}"
            }
            
        logger.info(f"Resultado de conexión ADB: {connect_output}")
        
        # Ejecutar el comando
        cmd_result = await run_command_async(['adb', '-s', device_address, 'shell', adb_command])
        output = cmd_result['stdout']
        error = cmd_result['stderr']
        
        if cmd_result['returncode'] != 0 or error:
            error_msg = error if error else output
            logger.error(f"Error al ejecutar comando ADB en {device.name}: {error_msg}")
            return {
                "status": "error",
                "device_id": device.device_id,
                "message": f"Error al ejecutar comando en {device.name}: {error_msg}"
            }
        
        logger.info(f"Comando ADB ejecutado exitosamente en {device.name}")
        return {
            "status": "success",
            "device_id": device.device_id,
            "message": f"Comando ejecutado exitosamente en {device.name}",
            "output": output
        }
        
    except Exception as e:
        logger.error(f"Error al ejecutar operación ADB en {device.name} ({device_address})")
        logger.exception(e)
        return {
            "status": "error",
            "device_id": device.device_id,
            "message": f"Error de operación ADB en {device.name}: {str(e)}"
        }