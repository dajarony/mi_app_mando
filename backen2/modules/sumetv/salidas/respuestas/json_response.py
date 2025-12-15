"""
SUME DOCBLOCK

Nombre: JSON Response
Tipo: Salida

Entradas:
- Datos de respuesta
Acciones:
- Formatear con status, mensaje y data
Salidas:
- dict JSON
"""
def json_response(data, status: str = "ok", mensaje: str = ""):
    return {"status": status, "mensaje": mensaje, "data": data}
