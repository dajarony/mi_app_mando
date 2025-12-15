"""
SUME DOCBLOCK
Nombre: Modelo de Datos para Dispositivos TV
Tipo: Lógica/Modelos

Entradas:
- Datos de dispositivos TV (JSON, diccionarios).

Acciones:
- Define la estructura y valida los datos para representar un dispositivo TV en el sistema.
- Genera automáticamente un `device_id` si no se proporciona.

Salidas:
- Instancias de TVDevice validadas y tipadas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid


class TVDevice(BaseModel):
    """Modelo de datos para dispositivos TV."""
    device_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Identificador único del dispositivo.")
    name: str = Field(description="Nombre amigable del dispositivo.")
    ip: str = Field(description="Dirección IP del dispositivo.")
    type: str = Field(description="Tipo de dispositivo (ej. 'dlna', 'android', 'philips_tv').")
    port: Optional[int] = Field(default=None, description="Puerto de conexión del dispositivo, si aplica.")
    location: Optional[str] = Field(default=None, description="URL de descripción DLNA/UPnP, si aplica.")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="Diccionario para metadatos adicionales del dispositivo.")
