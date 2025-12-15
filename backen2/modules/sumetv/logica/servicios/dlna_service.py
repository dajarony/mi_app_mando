

# SUME DOCBLOCK
# Nombre: DLNAService
# Tipo: Lógica
#
# Entradas:
# - device: TVDevice (contiene name, ip, location)
# - url: str (URI del contenido multimedia)
#
# Acciones:
# - Descubrir servicios UPnP/AVTransport y RenderingControl
# - Enviar URI al dispositivo y controlar reproducción (SetAVTransportURI, Play, Pause, Stop)
#
# Salidas:
# - Dict con 'status' ('success'|'error') y 'message'
from urllib.parse import urljoin
import logging
import requests
import xml.etree.ElementTree as ET
from dlna_service import DLNAService
from ..Modelos.tv_device import TVDevice

 # Asegúrate de tener esto también


logger = logging.getLogger(__name__)

AV_TRANSPORT_SERVICE = "urn:schemas-upnp-org:service:AVTransport:1"
RENDER_CONTROL_SERVICE = "urn:schemas-upnp-org:service:RenderingControl:1"
TIMEOUT = 10

class DLNAService:
    def __init__(self):
        logger.info("DLNAService inicializado")

    def _fetch_device_description(self, device: TVDevice) -> ET.Element | None:
        """
        SUME DOCBLOCK
        Nombre: _fetch_device_description
        Tipo: Lógica

        Entradas:
        - device: TVDevice

        Acciones:
        - Realiza GET a device.location y parsea el XML

        Salidas:
        - Elemento raíz XML o None si falla
        """
        if not device.location:
            logger.warning(f"El dispositivo {device.name} no tiene 'location' definida.")
            return None
        try:
            resp = requests.get(device.location, timeout=TIMEOUT)
            resp.raise_for_status()
            return ET.fromstring(resp.content)
        except requests.RequestException as e:
            logger.error(f"Error HTTP al obtener descripción de {device.name}: {e}")
        except ET.ParseError as e:
            logger.error(f"Error al parsear XML de {device.name}: {e}")
        return None

    def _get_control_url(self, root: ET.Element, base: str, service_type: str) -> str | None:
        """
        SUME DOCBLOCK
        Nombre: _get_control_url
        Tipo: Lógica

        Entradas:
        - root: Element (XML descripción)
        - base: str (URL base para urljoin)
        - service_type: str

        Acciones:
        - Localiza serviceList y extrae controlURL para service_type

        Salidas:
        - URL absoluta de control o None
        """
        ns = {'upnp': 'urn:schemas-upnp-org:device-1-0'}
        svc_list = root.find('.//upnp:serviceList', ns)
        if svc_list is None:
            logger.warning("serviceList no encontrado en descripción UPnP.")
            return None
        for svc in svc_list.findall('upnp:service', ns):
            st = svc.find('upnp:serviceType', ns)
            cu = svc.find('upnp:controlURL', ns)
            if st is not None and cu is not None and st.text.strip() == service_type:
                ctrl_path = cu.text.strip()
                full = urljoin(base, ctrl_path)
                logger.info(f"Control URL para {service_type}: {full}")
                return full
        logger.warning(f"Servicio {service_type} no encontrado.")
        return None

    def _discover_control_url(self, device: TVDevice, service_type: str) -> str | None:
        desc = self._fetch_device_description(device)
        if not desc:
            return None
        base = device.location.rsplit('/', 1)[0] + '/'
        return self._get_control_url(desc, base, service_type)

    def _soap_request(self, url: str, service: str, action: str, body: str) -> requests.Response | None:
        """
        SUME DOCBLOCK
        Nombre: _soap_request
        Tipo: Lógica

        Entradas:
        - url: str
        - service: str
        - action: str
        - body: str (contenido XML)

        Acciones:
        - Envía petición POST SOAP

        Salidas:
        - Response o None si falla
        """
        headers = {
            'Content-Type': 'text/xml; charset="utf-8"',
            'SOAPAction': f'"{service}#{action}"'
        }
        try:
            resp = requests.post(url, data=body, headers=headers, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.error(f"Error SOAP {action} a {url}: {e}")
        return None

    def send_content(self, device: TVDevice, url: str) -> dict:
        """
        SUME DOCBLOCK
        Nombre: send_content
        Tipo: Lógica

        Entradas:
        - device: TVDevice
        - url: str (URI multimedia)

        Acciones:
        - SetAVTransportURI y Play

        Salidas:
        - status, message
        """
        logger.info(f"Enviando contenido a {device.name} ({device.ip}): {url}")
        control_url = self._discover_control_url(device, AV_TRANSPORT_SERVICE)
        if not control_url:
            return {"status": "error", "message": "No pude determinar controlURL AVTransport."}
        # SetAVTransportURI
        body_uri = f"""
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
          <s:Body>
            <u:SetAVTransportURI xmlns:u="{AV_TRANSPORT_SERVICE}">
              <InstanceID>0</InstanceID>
              <CurrentURI>{url}</CurrentURI>
              <CurrentURIMetaData></CurrentURIMetaData>
            </u:SetAVTransportURI>
          </s:Body>
        </s:Envelope>
        """
        if not self._soap_request(control_url, AV_TRANSPORT_SERVICE, 'SetAVTransportURI', body_uri):
            return {"status": "error", "message": "Fallo al indicar URI al dispositivo."}
        # Play
        body_play = f"""
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
          <s:Body>
            <u:Play xmlns:u="{AV_TRANSPORT_SERVICE}">
              <InstanceID>0</InstanceID>
              <Speed>1</Speed>
            </u:Play>
          </s:Body>
        </s:Envelope>
        """
        if not self._soap_request(control_url, AV_TRANSPORT_SERVICE, 'Play', body_play):
            return {"status": "error", "message": "URI enviada, pero fallo al reproducir."}
        return {"status": "success", "message": "Reproducción iniciada correctamente."}

    # Métodos adicionales: pause, stop
    def pause(self, device: TVDevice) -> dict:
        """
        SUME DOCBLOCK
        Nombre: pause
        Tipo: Lógica

        Acciones:
        - Pause en AVTransport

        Salidas:
        - status, message
        """
        control_url = self._discover_control_url(device, AV_TRANSPORT_SERVICE)
        if not control_url:
            return {"status": "error", "message": "No pude determinar controlURL AVTransport."}
        body = f"""
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
          <s:Body>
            <u:Pause xmlns:u="{AV_TRANSPORT_SERVICE}">
              <InstanceID>0</InstanceID>
            </u:Pause>
          </s:Body>
        </s:Envelope>
        """
        if not self._soap_request(control_url, AV_TRANSPORT_SERVICE, 'Pause', body):
            return {"status": "error", "message": "Fallo al pausar reproducción."}
        return {"status": "success", "message": "Reproducción en pausa."}

    def stop(self, device: TVDevice) -> dict:
        """
        SUME DOCBLOCK
        Nombre: stop
        Tipo: Lógica

        Acciones:
        - Stop en AVTransport

        Salidas:
        - status, message
        """
        control_url = self._discover_control_url(device, AV_TRANSPORT_SERVICE)
        if not control_url:
            return {"status": "error", "message": "No pude determinar controlURL AVTransport."}
        body = f"""
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
          <s:Body>
            <u:Stop xmlns:u="{AV_TRANSPORT_SERVICE}">
              <InstanceID>0</InstanceID>
            </u:Stop>
          </s:Body>
        </s:Envelope>
        """
        if not self._soap_request(control_url, AV_TRANSPORT_SERVICE, 'Stop', body):
            return {"status": "error", "message": "Fallo al detener reproducción."}
        return {"status": "success", "message": "Reproducción detenida."}
