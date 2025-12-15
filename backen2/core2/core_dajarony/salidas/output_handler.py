# -*- coding: utf-8 -*-
"""
SUME DOCBLOCK

Nombre: Manejador de Salidas (Output Handler)
Tipo: Salida

Entradas:
- Datos a enviar (`data`: Any)
- Configuración de salida (opcional):
    - `output_id`: str | None
    - `format`: OutputFormat | None
    - `destination`: OutputDestination | None
    - `path`: str | None (ruta archivo/dirección red)
    - `verbosity`: str | None ('minimal', 'normal', 'detailed')
    - `transform`: str | None (nombre de transformador registrado)
    - `append`: bool (para destino FILE)
    - `metadata`: Dict | None
- Dependencias (opcional en constructor):
    - `event_bus`: Any
    - `logger`: logging.Logger
    - `config`: Dict
- Transformadores (registrados vía `register_transformer`)

Acciones:
- Recibe datos y parámetros de configuración para una operación de salida.
- Aplica transformaciones registradas a los datos si se solicita.
- Formatea los datos según el formato especificado (TEXT, JSON, YAML, CSV, XML, HTML, MARKDOWN, BINARY).
- Enruta y envía los datos formateados al destino especificado (CONSOLE, FILE, NETWORK, MEMORY, EVENT, NULL).
- Gestiona el buffer de memoria para el destino MEMORY.
- Aplica colores a la salida de consola si está configurado y soportado.
- Registra la actividad y los errores utilizando el logger proporcionado o uno por defecto.
- Emite eventos 'output:sent' y 'output:error' a través del event_bus si está disponible.
- Mantiene estadísticas básicas de las operaciones de salida.
- Gestiona la limpieza de recursos (implícita con context managers para archivos/red).

Salidas:
- Resultado booleano del método `output()` indicando éxito (True) o fallo (False).
- Efecto secundario: Datos enviados al destino configurado (consola, archivo, red).
- Efecto secundario: Datos almacenados en el buffer de memoria (si destino es MEMORY).
- Efecto secundario: Eventos emitidos al event_bus (`output:sent`, `output:error`).
- Efecto secundario: Mensajes registrados en el logger.
- Datos recuperables desde memoria (`get_memory_output`).
- Estadísticas recuperables (`get_stats`).
"""

import os
import sys
import json
import yaml
import logging
import socket
from datetime import datetime
from enum import Enum
import csv
import io
from typing import Dict, List, Any, Optional, Union, TextIO, BinaryIO, Callable, Tuple
from pathlib import Path

# Configuración básica del logger si no se proporciona uno externo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class OutputFormat(Enum):
    """Formatos soportados para salidas."""
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"
    XML = "xml"  # Requiere implementación o librería externa robusta
    HTML = "html" # Requiere implementación o librería externa robusta
    MARKDOWN = "markdown" # Requiere implementación o librería externa robusta
    BINARY = "binary"

class OutputDestination(Enum):
    """Destinos soportados para salidas."""
    CONSOLE = "console"
    FILE = "file"
    NETWORK = "network" # Implementación básica TCP
    MEMORY = "memory"
    EVENT = "event"
    NULL = "null"  # Descartar salida (útil para pruebas)

class OutputHandler:
    # La descripción detallada ahora está en el SUME DOCBLOCK al inicio del archivo.

    def __init__(self, event_bus: Optional[Any] = None, logger: Optional[logging.Logger] = None, config: Optional[Dict] = None):
        """
        Inicializa el manejador de salidas.

        Args:
            event_bus: Instancia de EventBus para emisión de eventos (opcional).
            logger: Instancia de Logger para registro de actividad (opcional).
            config: Diccionario de configuración del sistema (opcional).
        """
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.config = config if config is not None else {}

        # --- Configuración por defecto ---
        try:
            self.default_verbosity: str = self.config.get("output.verbosity", "normal")
            self.default_destination: OutputDestination = OutputDestination(
                self.config.get("output.destination", "console"))
            self.default_format: OutputFormat = OutputFormat(
                self.config.get("output.format", "text"))
        except ValueError as e:
            self.logger.error(f"Configuración inválida para OutputHandler: {e}. Usando valores por defecto seguros.")
            self.default_verbosity = "normal"
            self.default_destination = OutputDestination.CONSOLE
            self.default_format = OutputFormat.TEXT

        # --- Recursos y Estado Interno ---
        self._memory_buffer: Dict[str, List[Any]] = {}
        self._transformers: Dict[str, Callable[[Any], Any]] = {}
        self._stats: Dict[str, int] = {
            "output_count": 0,
            "bytes_written": 0,
            "errors": 0
        }
        self._setup_console_colors()
        self.logger.info(f"OutputHandler inicializado (Default: {self.default_destination.value}/{self.default_format.value})")

    def _setup_console_colors(self):
        """Configura colores ANSI para salida en consola si está soportado y habilitado."""
        self.colors_enabled = (
            self.config.get("output.colors", True) and
            hasattr(sys.stdout, 'isatty') and
            sys.stdout.isatty()
        )
        _color_map = {
            "reset": "\033[0m", "bold": "\033[1m", "red": "\033[31m",
            "green": "\033[32m", "yellow": "\033[33m", "blue": "\033[34m",
            "magenta": "\033[35m", "cyan": "\033[36m", "white": "\033[37m",
            "bg_red": "\033[41m", "bg_green": "\033[42m", "bg_yellow": "\033[43m",
            "bg_blue": "\033[44m"
        }
        if self.colors_enabled:
            self.colors = _color_map
            self.logger.debug("Colores de consola habilitados.")
        else:
            self.colors = {k: "" for k in _color_map.keys()}
            self.logger.debug("Colores de consola deshabilitados.")

    # ------------------------------------------------- #
    # UAF - OUTPUT - Punto de entrada principal para enviar salidas
    # ------------------------------------------------- #
    def output(self,
               data: Any,
               output_id: Optional[str] = None,
               format: Optional[OutputFormat] = None,
               destination: Optional[OutputDestination] = None,
               path: Optional[str] = None, # Ruta para FILE, Addr:Port para NETWORK
               verbosity: Optional[str] = None,
               transform: Optional[str] = None, # Nombre del transformador a usar
               append: bool = False, # Para destino FILE
               metadata: Optional[Dict[str, Any]] = None # Datos extra para eventos/logs
               ) -> bool:
        """
        Procesa, formatea y envía datos al destino especificado.
        (Ver SUME DOCBLOCK al inicio para detalles completos)
        """
        output_id = output_id or f"output_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        current_format = format or self.default_format
        current_destination = destination or self.default_destination
        current_verbosity = verbosity or self.default_verbosity
        metadata = metadata or {}
        self.logger.debug(f"Procesando salida ID: {output_id}, Dest: {current_destination.value}, Format: {current_format.value}")

        try:
            processed_data = data
            # 1. Aplicar transformación
            if transform:
                if transform in self._transformers:
                    try:
                        processed_data = self._transformers[transform](data)
                        self.logger.debug(f"Transformador '{transform}' aplicado a salida {output_id}")
                    except Exception as e:
                        self.logger.error(f"Error aplicando transformador '{transform}' a salida {output_id}: {e}")
                        self._stats["errors"] += 1
                        return False
                else:
                    self.logger.warning(f"Transformador '{transform}' no encontrado para salida {output_id}. Usando datos originales.")

            # 2. Formatear datos
            formatted_data = self._format_data(processed_data, current_format, current_verbosity)
            if formatted_data is None:
                self.logger.warning(f"Formato {current_format.value} no aplicable o falló para salida {output_id}")
                self._stats["errors"] += 1
                return False

            # 3. Enviar al destino
            send_success = self._send_to_destination(
                formatted_data, current_destination, path, output_id, append
            )

            # 4. Actualizar estadísticas y emitir evento
            if send_success:
                self._stats["output_count"] += 1
                if isinstance(formatted_data, (str, bytes)):
                    self._stats["bytes_written"] += len(formatted_data)
                self._emit_event("output:sent", {
                    "output_id": output_id, "destination": current_destination.value,
                    "format": current_format.value, "success": True,
                    "bytes": len(formatted_data) if isinstance(formatted_data, (str, bytes)) else None,
                    "metadata": metadata
                })
                return True
            else:
                self._stats["errors"] += 1
                self._emit_event("output:error", {
                     "output_id": output_id, "destination": current_destination.value,
                     "format": current_format.value, "error": "Failed to send to destination",
                     "metadata": metadata
                 })
                return False
        except Exception as e:
            self.logger.exception(f"Error inesperado procesando salida {output_id}: {e}")
            self._stats["errors"] += 1
            self._emit_event("output:error", {"output_id": output_id, "error": str(e), "metadata": metadata})
            return False

    # ------------------------------------------------- #
    # UAF - REGISTER_TRANSFORMER - Registra función transformadora
    # ------------------------------------------------- #
    def register_transformer(self, name: str, transformer: Callable[[Any], Any]) -> bool:
        """Registra una función para modificar datos antes de formatear."""
        if not callable(transformer):
            self.logger.error(f"Intento de registrar transformador '{name}' que no es una función.")
            return False
        if name in self._transformers:
            self.logger.warning(f"Sobrescribiendo transformador existente: {name}")
        self._transformers[name] = transformer
        self.logger.info(f"Transformador registrado: {name}")
        return True

    # ------------------------------------------------- #
    # UAF - GET_MEMORY_OUTPUT - Obtiene salida de memoria
    # ------------------------------------------------- #
    def get_memory_output(self, output_id: str) -> Optional[List[Any]]:
        """Obtiene la lista de datos almacenados en memoria para un ID."""
        return self._memory_buffer.get(output_id)

    # ------------------------------------------------- #
    # UAF - CLEAR_MEMORY_OUTPUT - Limpia salida de memoria
    # ------------------------------------------------- #
    def clear_memory_output(self, output_id: Optional[str] = None) -> None:
        """Limpia el buffer de memoria para un ID específico o todos."""
        if output_id:
            if self._memory_buffer.pop(output_id, None): # Usar pop con default None
                self.logger.debug(f"Buffer de memoria limpiado para ID: {output_id}")
            else:
                 self.logger.debug(f"Intento de limpiar buffer de memoria para ID inexistente: {output_id}")
        else:
            self._memory_buffer.clear()
            self.logger.info("Todos los buffers de memoria limpiados.")

    # ------------------------------------------------- #
    # UAF - CLOSE_ALL_RESOURCES - Cierra recursos (si aplica)
    # ------------------------------------------------- #
    def close_all_resources(self) -> None:
        """Cierra recursos abiertos (si los hubiera)."""
        self.logger.info("Cerrando recursos de OutputHandler (si aplica)...")
        # Actualmente no hay recursos persistentes que cerrar aquí
        self.logger.info("Recursos de OutputHandler cerrados.")

    # ------------------------------------------------- #
    # UAF - GET_STATS - Obtiene estadísticas
    # ------------------------------------------------- #
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de las operaciones de salida."""
        return self._stats.copy()

    # --- Métodos Internos de Formateo ---

    def _format_data(self, data: Any, format_type: OutputFormat, verbosity: str) -> Optional[Union[str, bytes]]:
        """Formatea los datos según el tipo especificado."""
        self.logger.debug(f"Formateando datos a: {format_type.value}")
        formatter_method_name = f"_format_as_{format_type.value}"
        formatter_method = getattr(self, formatter_method_name, None)

        if formatter_method and callable(formatter_method):
            try:
                # Pasar verbosidad como argumento nombrado
                return formatter_method(data, verbosity=verbosity)
            except Exception as e:
                self.logger.error(f"Error en formateador '{formatter_method_name}': {e}")
                return None
        elif format_type == OutputFormat.BINARY: # Manejo especial si no hay _format_as_binary
            if isinstance(data, bytes): return data
            try: return bytes(str(data), 'utf-8')
            except Exception as e: self.logger.error(f"No se pudo convertir dato a bytes: {e}"); return None
        else:
            self.logger.warning(f"Formateador no implementado o no encontrado: {formatter_method_name}")
            return None

    def _format_as_text(self, data: Any, verbosity: str) -> str:
        """Formatea los datos como texto plano."""
        if isinstance(data, (str, bytes)):
            return data.decode('utf-8', errors='replace') if isinstance(data, bytes) else data
        if isinstance(data, (dict, list)) and verbosity == "detailed":
            import pprint
            return pprint.pformat(data, indent=2, width=120)
        return str(data)

    def _format_as_json(self, data: Any, verbosity: str) -> Optional[str]:
        """Formatea los datos como JSON string."""
        indent = 2 if verbosity == "detailed" else None
        try:
            return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
        except TypeError as e:
            self.logger.error(f"Error al serializar a JSON: {e}. Tipo no soportado: {type(data)}")
            return None

    def _format_as_yaml(self, data: Any, verbosity: str) -> Optional[str]:
        """Formatea los datos como YAML string."""
        try:
            return yaml.dump(data, default_flow_style=None, allow_unicode=True, sort_keys=False)
        except Exception as e:
            self.logger.error(f"Error al formatear como YAML: {e}")
            return None

    def _format_as_csv(self, data: Any, verbosity: str) -> Optional[str]:
        """Formatea datos (lista de dicts/listas) como CSV string."""
        output = io.StringIO()
        try:
            if isinstance(data, list) and data:
                first_item = data[0]
                if isinstance(first_item, dict):
                    fieldnames = list(first_item.keys())
                    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
                    writer.writeheader()
                    writer.writerows(data)
                elif isinstance(first_item, (list, tuple)):
                    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
                    writer.writerows(data)
                else: # Lista de valores simples
                    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(["Value"])
                    writer.writerows([[item] for item in data]) # Envolver cada item en una lista
            elif isinstance(data, dict):
                writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
                writer.writerow(["Key", "Value"])
                writer.writerows(data.items())
            else:
                self.logger.warning(f"Tipo de dato no soportado para CSV: {type(data)}")
                return None
            return output.getvalue()
        except Exception as e:
            self.logger.error(f"Error al formatear como CSV: {e}")
            return None
        finally:
            output.close()

    def _format_as_xml(self, data: Any, verbosity: str) -> Optional[str]:
        """Formatea datos como XML (básico). Usar lxml para producción."""
        self.logger.warning("Formateo XML es básico.")
        try:
            from xml.etree.ElementTree import Element, SubElement, tostring
            from xml.dom.minidom import parseString
            def _to_xml(val, name="item"):
                safe_name = ''.join(c for c in name if c.isalnum() or c in '_-') or "item"
                if not safe_name[0].isalpha() and safe_name[0] != '_': safe_name = "item"
                elem = Element(safe_name)
                if isinstance(val, dict):
                    for k, v in val.items(): elem.append(_to_xml(v, k))
                elif isinstance(val, list):
                    for i in val: elem.append(_to_xml(i, "item"))
                else: elem.text = str(val)
                return elem
            root = _to_xml(data, "root")
            return parseString(tostring(root, 'utf-8')).toprettyxml(indent="  ")
        except Exception as e: self.logger.error(f"Error al formatear como XML (básico): {e}"); return None

    def _format_as_html(self, data: Any, verbosity: str) -> Optional[str]:
        """Formatea datos como HTML (básico). Usar plantillas para producción."""
        self.logger.warning("Formateo HTML es básico.")
        try:
            from html import escape
            def _render(item):
                if isinstance(item, dict): return f"<table>{''.join(f'<tr><td><strong>{escape(str(k))}</strong></td><td>{_render(v)}</td></tr>' for k, v in item.items())}</table>"
                if isinstance(item, list): return f"<ul>{''.join(f'<li>{_render(i)}</li>' for i in item)}</ul>"
                return escape(str(item))
            styles = "<style>body{font-family:sans-serif;margin:1em}table{border-collapse:collapse;margin-bottom:1em;width:auto}th,td{border:1px solid #ccc;padding:0.4em;text-align:left;vertical-align:top}th{background-color:#f2f2f2;font-weight:bold}ul{margin-top:0;padding-left:1.5em}li{margin-bottom:0.3em}</style>"
            html = [f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Output</title>{styles}</head><body>"]
            if isinstance(data, list) and data and all(isinstance(r, dict) for r in data):
                 headers = list(data[0].keys())
                 html.append("<h2>Tabla</h2><table><thead><tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr></thead><tbody>")
                 for row in data: html.append("<tr>" + "".join(f"<td>{_render(row.get(h,''))}</td>" for h in headers) + "</tr>")
                 html.append("</tbody></table>")
            elif isinstance(data, dict): html.append("<h2>Diccionario</h2><table>" + "".join(f"<tr><th>{escape(str(k))}</th><td>{_render(v)}</td></tr>" for k,v in data.items()) + "</table>")
            elif isinstance(data, list): html.append("<h2>Lista</h2><ul>" + "".join(f"<li>{_render(i)}</li>" for i in data) + "</ul>")
            else: html.append(f"<h2>Datos</h2><p>{escape(str(data))}</p>")
            html.append("</body></html>")
            return "\n".join(html)
        except Exception as e: self.logger.error(f"Error al formatear como HTML (básico): {e}"); return None

    def _format_as_markdown(self, data: Any, verbosity: str) -> Optional[str]:
        """Formatea datos como Markdown (básico). Usar librerías para producción."""
        self.logger.warning("Formateo Markdown es básico.")
        try:
            md = ["# Output\n"]
            if isinstance(data, list) and data and all(isinstance(r, dict) for r in data):
                 headers = list(data[0].keys())
                 md.append("| " + " | ".join(headers) + " |")
                 md.append("| " + " | ".join(["-----"] * len(headers)) + " |")
                 for row in data: md.append("| " + " | ".join(str(row.get(h,'')).replace('|','\\|') for h in headers) + " |")
            elif isinstance(data, (dict, list)): md.append("```json\n" + json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n```")
            else: md.append(str(data))
            return "\n".join(md)
        except Exception as e: self.logger.error(f"Error al formatear como Markdown (básico): {e}"); return None

    # --- Métodos Internos de Envío ---

    def _send_to_destination(self, formatted_data: Union[str, bytes], destination: OutputDestination, path: Optional[str], output_id: str, append: bool) -> bool:
        """Enruta los datos formateados al destino correcto."""
        self.logger.debug(f"Enviando salida {output_id} a {destination.value}...")
        sender_map = {
            OutputDestination.CONSOLE: self._send_to_console,
            OutputDestination.FILE: lambda d: self._send_to_file(d, path=path, append=append),
            OutputDestination.NETWORK: lambda d: self._send_to_network(d, address=path),
            OutputDestination.MEMORY: lambda d: self._store_in_memory(d, key=output_id),
            OutputDestination.EVENT: lambda d: self._emit_event(d, event_id=output_id),
            OutputDestination.NULL: self._send_to_null
        }
        sender_method = sender_map.get(destination)
        if sender_method and callable(sender_method):
            try: return sender_method(formatted_data)
            except Exception as e: self.logger.error(f"Error en sender para {destination.value}: {e}"); return False
        else: self.logger.warning(f"Sender no implementado para destino: {destination.value}"); return False

    def _send_to_console(self, data: Union[str, bytes]) -> bool:
        """Envía datos a sys.stdout."""
        try:
            text_data = data.decode('utf-8', errors='replace') if isinstance(data, bytes) else str(data)
            # Aplicar colores básicos
            color = ""
            if self.colors_enabled:
                if text_data.lstrip().startswith("Error"): color = self.colors['red']
                elif text_data.lstrip().startswith("WARN"): color = self.colors['yellow']
            print(f"{color}{text_data}{self.colors['reset']}")
            sys.stdout.flush()
            return True
        except Exception as e: self.logger.error(f"Error crítico al enviar a consola: {e}"); return False

    def _send_to_file(self, data: Union[str, bytes], path: Optional[str], append: bool) -> bool:
        """Envía datos a un archivo usando 'with open()'."""
        if not path: self.logger.error("Ruta de archivo no especificada."); return False
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            is_binary = isinstance(data, bytes)
            mode = ('ab' if append else 'wb') if is_binary else ('a' if append else 'w')
            encoding = None if is_binary else 'utf-8'
            with open(file_path, mode, encoding=encoding) as f:
                f.write(data)
                if not is_binary and isinstance(data, str) and not data.endswith('\n'): f.write('\n')
            self.logger.debug(f"Datos {'añadidos a' if append else 'escritos en'} archivo: {path}")

            # --- Rotación de archivos ---
            # Si el archivo supera max_file_size bytes, renombrar con timestamp y crear uno nuevo.
            max_file_size = getattr(self, 'max_file_size', 10 * 1024 * 1024)  # 10 MB por defecto
            try:
                if file_path.stat().st_size > max_file_size:
                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    rotated_name = file_path.with_name(f"{file_path.stem}_{timestamp}{file_path.suffix}")
                    file_path.rename(rotated_name)
                    self.logger.info(f"Archivo {file_path} rotado a {rotated_name}.")
            except FileNotFoundError:
                # El archivo puede haber sido movido/borrado por otro proceso; ignorar
                pass
            return True
        except IOError as e: self.logger.error(f"Error I/O al escribir en {path}: {e}"); return False
        except Exception as e: self.logger.error(f"Error inesperado al enviar a {path}: {e}"); return False

    def _send_to_network(self, data: Union[str, bytes], address: Optional[str]) -> bool:
        """Envía datos vía TCP (conexión corta)."""
        if not address or ':' not in address: self.logger.error(f"Dirección red inválida (host:puerto): {address}"); return False
        try:
            host, port_str = address.split(':', 1)
            port = int(port_str)
            with socket.create_connection((host, port), timeout=5) as sock:
                encoded_data = data.encode('utf-8') if isinstance(data, str) else data
                sock.sendall(encoded_data)
                self.logger.debug(f"Datos enviados a {address} ({len(encoded_data)} bytes)")
                return True
        except ValueError: self.logger.error(f"Puerto inválido: {address}"); return False
        except socket.timeout: self.logger.error(f"Timeout en red {address}"); return False
        except socket.error as e: self.logger.error(f"Error socket en red {address}: {e}"); return False
        except Exception as e: self.logger.error(f"Error inesperado en red {address}: {e}"); return False

    def _store_in_memory(self, data: Any, key: str) -> bool:
        """Almacena datos originales en buffer de memoria."""
        try:
            self._memory_buffer.setdefault(key, []).append(data) # Usar setdefault
            self.logger.debug(f"Datos añadidos a buffer memoria (clave: {key})")
            return True
        except Exception as e: self.logger.error(f"Error al almacenar en memoria (clave {key}): {e}"); return False

    def _emit_event(self, event_name: str, data: Dict) -> bool:
        """Emite un evento interno o a través del EventBus."""
        # Asegurar que data tenga timestamp y source si se emite externamente
        payload = {**data, 'timestamp': datetime.now().isoformat()}
        if 'source' not in payload: payload['source'] = 'OutputHandler'

        if self.event_bus and hasattr(self.event_bus, 'emit'):
            try:
                self.event_bus.emit(event_name, payload)
                self.logger.debug(f"Evento emitido: {event_name}")
                return True
            except Exception as e:
                self.logger.error(f"Error al emitir evento {event_name}: {e}")
                return False
        else:
            # Log interno si no hay event bus para ciertos eventos
            if event_name in ["output:sent", "output:error"]:
                 self.logger.debug(f"Evento interno (sin EventBus): {event_name} - {data.get('output_id', '')}")
            return False # No se emitió externamente

    def _send_to_null(self, data: Union[str, bytes]) -> bool:
         """Descarta la salida."""
         self.logger.debug("Salida enviada a NULL (descartada).")
         return True

    # --- Destructor (Llamada opcional a cleanup) ---
    def __del__(self):
        """Llamado (no garantizado) cuando el objeto es destruido."""
        self.close_all_resources()

# --- Ejemplo de Uso (Opcional) ---
if __name__ == "__main__":
    example_logger = logging.getLogger("ExampleOutput")
    example_logger.setLevel(logging.DEBUG)
    if not example_logger.handlers: # Evitar añadir handlers múltiples veces
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        example_logger.addHandler(handler)

    output_handler = OutputHandler(logger=example_logger, config={"output.colors": True})
    my_data_dict = {"nombre": "Dajarony", "valor": 123, "lista": [1, "dos", 3.0], "nested": {"a": True}}
    my_data_list = [{"id": 1, "desc": "Item A"}, {"id": 2, "desc": "Item B"}]
    my_data_text = "Este es un mensaje de texto simple."

    print("\n--- Salida Consola (Texto Detallado) ---")
    output_handler.output(my_data_dict, format=OutputFormat.TEXT, verbosity="detailed")
    print("\n--- Salida Consola (JSON Detallado) ---")
    output_handler.output(my_data_dict, format=OutputFormat.JSON, verbosity="detailed")
    print("\n--- Salida Consola (YAML) ---")
    output_handler.output(my_data_list, format=OutputFormat.YAML)
    print("\n--- Salida Archivo (CSV) ---")
    if output_handler.output(my_data_list, destination=OutputDestination.FILE, format=OutputFormat.CSV, path="./output_example.csv"):
        print("CSV guardado en output_example.csv")
    print("\n--- Salida Consola (HTML Básico) ---")
    output_handler.output(my_data_list, format=OutputFormat.HTML)
    print("\n--- Salida Consola (Markdown Básico) ---")
    output_handler.output(my_data_dict, format=OutputFormat.MARKDOWN, verbosity="detailed")

    output_handler.close_all_resources()
