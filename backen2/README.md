
# Backend de Control para TV Philips

Este proyecto implementa un servicio de backend para controlar televisores Philips que utilizan la API Jointspace. La aplicación está construida con FastAPI y proporciona una API REST para interactuar con los televisores de forma remota.

## Arquitectura (SUME/STDG)

El proyecto sigue una adaptación de la arquitectura SUME, dividiendo las responsabilidades en las siguientes capas:

- **Entradas (`new_philips_backend.py`)**: La API REST construida con FastAPI define los puntos de entrada al sistema. Recibe peticiones HTTP para controlar el televisor.
- **Lógica (`pylips.py`, `new_philips_backend.py`)**:
    - `pylips.py`: Contiene la lógica de negocio de bajo nivel para la comunicación directa con la API de Philips TV (autenticación, envío de comandos, etc.).
    - `new_philips_backend.py`: Orquesta las llamadas a `pylips.py` basándose en las peticiones recibidas en la capa de entrada.
- **Salidas**: Las respuestas de la API en formato JSON. También utiliza MQTT para publicar eventos o cambios de estado.
- **Infraestructura**:
    - **FastAPI/Uvicorn**: Servidor web asíncrono.
    - **Firebase Admin**: Para la integración con servicios de Google Firebase (posiblemente Firestore para almacenar datos de dispositivos).
    - **Paho-MQTT**: Cliente para la comunicación a través del protocolo MQTT.
    - **python-dotenv**: Para la gestión de variables de entorno.

## Configuración del Entorno

1.  **Clonar el repositorio (si aplica)**
    ```bash
    git clone <url-del-repositorio>
    cd backen2
    ```

2.  **Crear un entorno virtual**
    ```bash
    python -m venv venv
    ```

3.  **Activar el entorno virtual**
    - En Windows:
      ```bash
      .\venv\Scripts\activate
      ```
    - En macOS/Linux:
      ```bash
      source venv/bin/activate
      ```

4.  **Instalar dependencias**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configurar variables de entorno**
    Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido. Deberás obtener estos valores de la configuración de tu TV y de tu proyecto de Firebase.

    ```env
    # Configuración de la TV Philips
    TV_HOST=192.168.1.100 # IP de la TV
    TV_USER=tu_usuario_api
    TV_PASS=tu_contraseña_api

    # Configuración de Firebase
    FIREBASE_CREDENTIALS_PATH=/ruta/a/tu/archivo-de-credenciales.json
    FIREBASE_DB_URL=https://tu-proyecto.firebaseio.com

    # Configuración de MQTT (si es necesario)
    MQTT_BROKER_HOST=192.168.1.200
    MQTT_BROKER_PORT=1883
    ```

## Ejecución

Para iniciar el servidor de desarrollo, utiliza Uvicorn:

```bash
uvicorn new_philips_backend:app --reload
```

El servidor estará disponible en `http://127.0.0.1:8000`.

## Documentación de la API

La API se documenta automáticamente a través de Swagger UI. Una vez que el servidor esté en ejecución, puedes acceder a la documentación interactiva en:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Endpoints Principales (Ejemplos)

- `POST /sendKey`: Envía una tecla de control remoto a la TV.
- `POST /setVolume`: Ajusta el nivel de volumen.
- `GET /status`: Obtiene el estado actual de la TV.

## Propuesta de Documentación Interna (SUME DOCBLOCKS)

Para mejorar la mantenibilidad, se recomienda añadir `SUME DOCBLOCKS` al inicio de los archivos Python clave.

**Ejemplo para `new_philips_backend.py`:**

```python
"""
SUME DOCBLOCK

Nombre: API Backend para Philips TV
Tipo: Entrada

Entradas:
- Peticiones HTTP JSON desde clientes (frontend, apps móviles).
- Vienen a través de FastAPI.

Acciones:
- Valida las peticiones de entrada.
- Orquesta la comunicación con la TV a través del módulo `pylips`.
- Se comunica con Firebase para obtener/guardar configuraciones.
- Publica mensajes en un broker MQTT sobre cambios de estado.

Salidas:
- Respuestas HTTP JSON a los clientes.
- Mensajes MQTT al topic `tv/status`.

Dependencias:
- `pylips.py`: Para el control de la TV.
- `firebase_admin`: Para la conexión con Firebase.
- `paho.mqtt.client`: Para la comunicación MQTT.
"""
```

**Ejemplo para `pylips.py`:**

```python
"""
SUME DOCBLOCK

Nombre: Controlador de Philips TV (Jointspace API)
Tipo: Lógica

Entradas:
- Host (IP de la TV), usuario y contraseña.
- Comandos a ejecutar (ej. "Standby", "VolumeUp").

Acciones:
- Establece una sesión de comunicación con la TV.
- Realiza el proceso de autenticación.
- Envía comandos HTTP a la API Jointspace.
- Parsea las respuestas de la TV.

Salidas:
- El resultado de la ejecución del comando.
- Datos de estado de la TV (canal actual, volumen, etc.).

Dependencias:
- `requests` o `aiohttp`: Para realizar las peticiones HTTP.
"""
```
