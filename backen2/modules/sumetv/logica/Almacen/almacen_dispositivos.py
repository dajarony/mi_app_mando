"""
SUME DOCBLOCK

Nombre: Almacén de Dispositivos TV
Tipo: Lógica / Almacén

Entradas:
- Objetos TVDevice para operaciones CRUD (add, get, list, remove).
- Variables de entorno como FIREBASE_DEVICE_TIMEOUT para configuración.

Acciones:
- Mantiene una caché en memoria de dispositivos TV para acceso rápido.
- Sincroniza la caché con la base de datos en la nube (Firebase Firestore) de forma asíncrona.
- Realiza un precargado de dispositivos críticos al inicio para asegurar su disponibilidad.
- Gestiona la persistencia de los dispositivos (guardar, obtener, listar, eliminar).

Salidas:
- Objetos TVDevice listos para ser consumidos por otras capas de la aplicación (ej. routers).
- Información de estado y errores en los logs.
"""
from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from concurrent.futures import TimeoutError as _FuturesTimeout
from typing import Dict, List, Optional

from sumetv.logica.Modelos.tv_device import TVDevice
from sumetv.salidas.firebase_store import FirebaseStore

logger = logging.getLogger("almacen_dispositivos")

# ============================
# Configuración y constantes
# ============================
# Timeout (en segundos) para lecturas individuales en Firebase; configurable vía env.
FIREBASE_DEVICE_TIMEOUT: int = int(os.getenv("FIREBASE_DEVICE_TIMEOUT", "120"))

# ============================
# Estado interno
# ============================
#   • Caché local de TVDevice por device_id.
#   • FirebaseStore singleton para acceso a la nube.
# ============================
_devices_cache: Dict[str, TVDevice] = {}
_firebase_store = FirebaseStore()

# ============================
# Función de preload crítico
# ============================
def _preload_critical_devices():
    """Asegura que los dispositivos críticos estén siempre en caché.

    Esta función precarga dispositivos como emuladores o móviles de prueba
    para garantizar su disponibilidad inmediata en la caché local.
    """
    logger.info("Precargando dispositivos críticos en caché")
    
    # El emulador es crítico - siempre debe estar disponible
    if "emulator-5554" not in _devices_cache:
        _devices_cache["emulator-5554"] = TVDevice(
            device_id="emulator-5554",
            name="Mi Emulador Android",
            ip="127.0.0.1",
            type="android",
            port=5555
        )
        logger.info("Precargado dispositivo crítico: emulator-5554")
    
    # Dispositivo móvil también importante
    if "mi-movil-android" not in _devices_cache:
        _devices_cache["mi-movil-android"] = TVDevice(
            device_id="mi-movil-android",
            name="Mi Movil Android",
            ip="192.168.1.50",
            type="android",
            port=5555
        )
        logger.info("Precargado dispositivo crítico: mi-movil-android")

# Precargar al iniciar el módulo
_preload_critical_devices()


# ============================
# Funciones auxiliares privadas
# ============================

def _run_coroutine_sync(coro, *, timeout: Optional[int] = None):
    """Ejecuta una corrutina de forma síncrona en el bucle de eventos actual o en uno temporal.

    Args:
        coro: La corrutina a ejecutar.
        timeout (Optional[int]): Tiempo máximo de espera para la corrutina.

    Returns:
        El resultado de la corrutina.

    Raises:
        TimeoutError: Si la corrutina excede el tiempo de espera.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No hay bucle: creamos uno ad‑hoc.
        _temp_loop = asyncio.new_event_loop()
        try:
            return _temp_loop.run_until_complete(asyncio.wait_for(coro, timeout))
        finally:
            _temp_loop.close()
    else:
        # Ya existe un bucle ⇒ ejecutamos desde un hilo seguro.
        future = asyncio.run_coroutine_threadsafe(asyncio.wait_for(coro, timeout), loop)
        return future.result(timeout)


# ============================
# API pública
# ============================

def add_device(device: TVDevice) -> TVDevice:
    """Registra o actualiza un dispositivo tanto en la caché local como en Firebase.

    Args:
        device (TVDevice): El objeto TVDevice a añadir o actualizar.

    Returns:
        TVDevice: El dispositivo TVDevice almacenado.
    """
    # Primero lo guardamos en caché para disponibilidad inmediata
    _devices_cache[device.device_id] = device

    # Guardado asíncrono a Firebase – no bloquea la ejecución.
    async def _save():
        try:
            # TVDevice → dict (ignorando campos None y privados)
            payload = {k: v for k, v in device.dict(exclude_none=True).items() if not k.startswith("_")}
            await _firebase_store.save_device(payload)
            logger.info("Dispositivo %s (%s) guardado en Firebase", device.name, device.device_id)
        except Exception as exc:  # noqa: BLE001 – Queremos loguear cualquier error.
            logger.error("Error guardando %s en Firebase: %s", device.device_id, exc, exc_info=True)

    try:
        asyncio.create_task(_save())
    except RuntimeError:
        # Si no hay bucle en marcha (p.e. script síncrono), lo lanzamos en uno temporal.
        threading.Thread(target=lambda: asyncio.run(_save()), daemon=True).start()

    return device


def get_device(device_id: str) -> Optional[TVDevice]:
    """Devuelve un **TVDevice** por su *device_id*.
    
    Utiliza primero la caché, y si el dispositivo no está en caché, intenta obtenerlo de Firebase.
    Si el dispositivo es crítico, siempre estará en caché.

    Args:
        device_id (str): El ID del dispositivo a buscar.

    Returns:
        Optional[TVDevice]: El dispositivo TVDevice si se encuentra, None en caso contrario.
    """
    # Verificar si necesitamos recargar dispositivos críticos
    if device_id in ["emulator-5554", "mi-movil-android"] and device_id not in _devices_cache:
        _preload_critical_devices()
    
    # 1️⃣ Caché local inmediata.
    if device_id in _devices_cache:
        logger.info(f"Dispositivo {device_id} encontrado en caché local")
        return _devices_cache[device_id]

    # 2️⃣ Consulta a Firebase con timeout configurable.
    try:
        logger.info(f"Buscando dispositivo {device_id} en Firebase (timeout: {FIREBASE_DEVICE_TIMEOUT}s)")
        data = _run_coroutine_sync(
            _firebase_store.get_device(device_id),
            timeout=FIREBASE_DEVICE_TIMEOUT,
        )
    except (_FuturesTimeout, asyncio.TimeoutError):
        logger.warning(
            "Timeout (%ss) al buscar %s en Firebase - intentando usar caché si existe", 
            FIREBASE_DEVICE_TIMEOUT, device_id
        )
        # Si ya está en caché, devuelve el dispositivo de la caché
        if device_id in _devices_cache:
            logger.info(f"Usando valor de caché para {device_id} debido a timeout de Firebase")
            return _devices_cache[device_id]
        logger.error(f"No se pudo obtener {device_id} de Firebase ni caché")
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("Error recuperando %s desde Firebase: %s", device_id, exc, exc_info=True)
        # Si ya está en caché, devuelve el dispositivo de la caché
        if device_id in _devices_cache:
            logger.info(f"Usando valor de caché para {device_id} debido a error de Firebase")
            return _devices_cache[device_id]
        return None

    if data:
        try:
            device = TVDevice(**data)
            _devices_cache[device_id] = device
            return device
        except Exception as exc:  # noqa: BLE001
            logger.error("Datos inválidos para TVDevice %s: %s", device_id, exc, exc_info=True)
            # Si ya está en caché, devuelve el dispositivo de la caché
            if device_id in _devices_cache:
                return _devices_cache[device_id]

    return None


def list_devices() -> List[TVDevice]:
    """Obtiene todos los dispositivos registrados, actualizando la caché local.

    • Ejecuta la consulta a Firebase en un **hilo** con su propio bucle asyncio
      para no bloquear hilos de eventos del servidor.
    • Si la nube no responde tras *timeout* segundos, devuelve el contenido de la
      caché local y deja constancia en los logs.
    • Asegura que los dispositivos críticos siempre estén disponibles

    Returns:
        List[TVDevice]: Una lista de todos los dispositivos TV registrados.
    """
    # Asegurar que los dispositivos críticos estén siempre disponibles
    _preload_critical_devices()
    
    result_container: dict[str, object] = {"data": None, "error": None, "done": False}
    timeout = FIREBASE_DEVICE_TIMEOUT + 3  # Damos un pequeño margen.

    def _fetch():
        try:
            thread_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(thread_loop)
            devices_data = thread_loop.run_until_complete(
                asyncio.wait_for(_firebase_store.list_devices(), timeout)
            )
            result_container["data"] = devices_data
        except Exception as exc:  # noqa: BLE001
            result_container["error"] = exc
            logger.error("Error listando dispositivos en Firebase: %s", exc, exc_info=True)
        finally:
            result_container["done"] = True
            thread_loop.close()

    threading.Thread(target=_fetch, daemon=True).start()

    start = time.time()
    while not result_container["done"] and time.time() - start < timeout:
        time.sleep(0.1)

    if not result_container["done"]:
        logger.warning("Timeout (%ss) listando dispositivos; devolviendo caché", timeout)
        return list(_devices_cache.values())

    if result_container["error"] is not None:
        return list(_devices_cache.values())

    # Procesar datos recuperados y refrescar caché.
    devices_data = result_container["data"] or []
    
    # No limpiamos completamente la caché para mantener dispositivos críticos
    # Simplemente actualizamos con los nuevos datos
    for item in devices_data:
        try:
            if isinstance(item, dict) and "device_id" in item:
                _devices_cache[item["device_id"]] = TVDevice(**item)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error construyendo TVDevice: %s", exc, exc_info=True)

    # Aseguramos que los dispositivos críticos sigan en la caché
    _preload_critical_devices()
    
    logger.info("Sincronizados %s dispositivos desde Firebase", len(_devices_cache))
    return list(_devices_cache.values())


def remove_device(device_id: str) -> bool:
    """Elimina un dispositivo tanto de la caché local como de Firebase.

    Args:
        device_id (str): ID del dispositivo a eliminar.

    Returns:
        bool: True si se eliminó correctamente, False si no existe.
    """
    # No permitir eliminar dispositivos críticos
    if device_id in ["emulator-5554", "mi-movil-android"]:
        logger.warning(f"Intento de eliminar dispositivo crítico: {device_id} - Operación rechazada")
        return False
        
    removed_from_cache = _devices_cache.pop(device_id, None) is not None

    async def _delete():
        try:
            await _firebase_store.delete_device(device_id)
            logger.info("Dispositivo %s eliminado de Firebase", device_id)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error eliminando %s de Firebase: %s", device_id, exc, exc_info=True)

    try:
        asyncio.create_task(_delete())
    except RuntimeError:
        threading.Thread(target=lambda: asyncio.run(_delete()), daemon=True).start()

    return removed_from_cache