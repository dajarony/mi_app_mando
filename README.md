# Smart TV Manager 📺

Una aplicación Flutter completa para controlar Smart TVs de diferentes marcas con interfaz neumórfica moderna.

## 🚀 Características Principales

- **Control remoto universal** para múltiples marcas de TV
- **Escaneo automático** de TVs en la red local
- **Registro manual** de dispositivos
- **Interfaz neumórfica** moderna y profesional
- **Control directo** via HTTP/WebSocket
- **Almacenamiento local** de configuraciones
- **Soporte multi-marca**: Samsung, LG, Sony, Philips, Roku, etc.

## 📱 Pantallas

### 1. HomeScreen (`/`)
- Pantalla principal de gestión de TVs
- Escaneo automático de red
- Lista de TVs registradas
- Formulario de registro manual
- Selección de TV activa

### 2. RemoteControlScreen (`/remote_control`)
- Control remoto funcional con diseño neumórfico
- D-pad de navegación
- Teclado numérico
- Controles de volumen
- Botones de función (Power, Home, Back, Menu)

### 3. SettingsScreen (`/settings`)
- Configuraciones de la aplicación
- Preferencias de usuario

## 🏗️ Arquitectura del Proyecto

```
lib/
├── main.dart                    # Punto de entrada de la aplicación
├── router/
│   └── app_routes.dart         # Configuración de rutas y navegación
├── screens/
│   ├── home_screen.dart        # Pantalla principal
│   └── remote_control_screen.dart # Control remoto funcional
├── services/
│   ├── network_service.dart    # Escaneo de red y comunicación
│   ├── tv_remote_service.dart  # Servicios de control remoto
│   ├── tv_storage_service.dart # Almacenamiento local
│   └── philips_tv_direct_service.dart # Control específico Philips
├── models/
│   └── smart_tv.dart          # Modelos de datos
├── theme/
│   └── app_theme.dart         # Tema neumórfico
└── widgets/
    ├── bottom_nav_item.dart   # Componentes de navegación
    └── neumorphic_nav_bar.dart # Barra de navegación neumórfica
```

## 🔧 Servicios Principales

Cada servicio tiene una responsabilidad única y está ubicado en el directorio `lib/services/`.

### NetworkService
- **Ubicación**: `lib/services/network_service.dart`
- **Función**: Escaneo de red para encontrar Smart TVs, validación de conexión y emparejamiento.
- **Métodos principales**:
  - `scanNetworkStream()`: Emite un stream de eventos durante el escaneo de la red.
  - `validateSmartTVConnection()`: Verifica si una TV está online.
  - `pairWithTV()`: Inicia el proceso de emparejamiento con una TV.

### TVRemoteService
- **Ubicación**: `lib/services/tv_remote_service.dart`
- **Función**: Envío de comandos de control remoto a diferentes marcas de TV usando el protocolo adecuado (HTTP/WebSocket).
- **Métodos principales**:
  - `sendCommand()`: Envía un comando específico a una TV.
  - `sendCommandSequence()`: Envía una secuencia de comandos.
  - `closeAllConnections()`: Cierra todas las conexiones WebSocket activas.

### StorageService
- **Ubicación**: `lib/services/storage_service.dart`
- **Función**: Persistencia de datos locales (lista de TVs, TV seleccionada, favoritos) usando `shared_preferences`.
- **Métodos principales**:
  - `saveTVs()` / `loadTVs()`: Guarda y carga la lista de televisiones.
  - `setSelectedTVId()` / `getSelectedTVId()`: Gestiona la TV activa.
  - `toggleFavorite()`: Añade o quita una TV de favoritos.

### PhilipsTvDirectService
- **Ubicación**: `lib/services/philips_tv_direct_service.dart`
- **Función**: Implementación específica para controlar TVs Philips a través de su API HTTP.
- **Métodos principales**:
  - `sendKey(String key)`: Envía una tecla de control remoto.
  - `setVolume(double volume)`: Ajusta el volumen.
  - `openApp(String appName)`: Lanza una aplicación.

## 📊 Modelos de Datos

Los modelos de datos están centralizados en el directorio `lib/models/`.

### SmartTV
- **Ubicación**: `lib/models/smart_tv.dart`
- **Descripción**: Representa una televisión con todas sus propiedades, como ID, nombre, marca, IP, estado de conexión, etc. Incluye métodos de serialización (`toJson`/`fromJson`).

### Enums
- **Ubicación**: `lib/models/smart_tv.dart` (y otros archivos de modelos)
- **Descripción**: Se utilizan enums como `TVBrand`, `TVProtocol`, y `TVStatus` para representar estados y tipos de forma segura y legible.

## 🎨 Tema y Diseño

### AppTheme
- **Ubicación**: `lib/theme/app_theme.dart`
- **Descripción**: Define la apariencia visual de la aplicación, incluyendo el tema neumórfico, colores, estilos de texto y decoraciones personalizadas (efectos cóncavos y convexos).

## 🔌 Comunicación con TVs

### Protocolos Soportados

#### Samsung TVs
- **Protocolo**: WebSocket
- **Puerto**: 8001/8080
- **Endpoint**: `/api/v2/channels/samsung.remote.control`
- **Formato**: JSON con comandos específicos

#### LG TVs (WebOS)
- **Protocolo**: WebSocket
- **Puerto**: 3000
- **Endpoint**: `/api/v2/channels/lg.remote.control`
- **Formato**: JSON con códigos de tecla

#### Sony Bravia TVs
- **Protocolo**: HTTP POST
- **Puerto**: 80/8080
- **Endpoint**: `/sony/IRCC`
- **Formato**: JSON con códigos IRCC

#### Philips TVs
- **Protocolo**: HTTP POST
- **Puerto**: 1925
- **Endpoint**: `/6/input/key`
- **Formato**: JSON con nombres de tecla

#### Roku TVs
- **Protocolo**: HTTP POST
- **Puerto**: 8060
- **Endpoint**: `/keypress/{comando}`

## 🛠️ Comandos de Control

### Comandos Universales
- `power` - Encender/Apagar
- `volume_up/down` - Control de volumen
- `mute` - Silenciar
- `channel_up/down` - Cambiar canal
- `home` - Ir al inicio
- `back` - Volver
- `up/down/left/right` - Navegación
- `enter/ok` - Confirmar
- `menu` - Menú

### Comandos Específicos Philips
- `Standby` - Power
- `CursorUp/Down/Left/Right` - Navegación
- `Confirm` - OK
- `VolumeUp/Down` - Volumen
- `Mute` - Silenciar
- `Back/Home/Options` - Navegación
- `Digit0-9` - Números

## 📦 Dependencias

```yaml
dependencies:
  flutter: sdk: flutter
  dio: ^5.3.2                    # Cliente HTTP
  shared_preferences: ^2.2.2     # Almacenamiento local
  uuid: ^4.0.0                   # Generación de IDs
  web_socket_channel: ^2.4.0     # WebSocket
  logger: ^2.4.0                 # Logging
  cupertino_icons: ^1.0.2        # Iconos
```

## 🚀 Instalación y Uso

1. **Clonar el repositorio**
2. **Instalar dependencias**: `flutter pub get`
3. **Ejecutar la aplicación**: `flutter run`
4. **Escanear TVs** en la red local
5. **Seleccionar TV** y usar el control remoto

## 🔧 Configuración

### IP de TV Philips
- **Archivo**: `lib/services/philips_tv_direct_service.dart`
- **Variable**: `_tvIpAddress`
- **Puerto**: 1925 (HTTP)

### Configuración de Red
- **Subnet por defecto**: `192.168.1.x`
- **Rango de escaneo**: IPs 1-50
- **Puertos comunes**: 8080, 8001, 3000, 55000, 8060, 7345

## 🐛 Debugging

### Logs de Red
- Los servicios incluyen logging detallado
- Usar `debugPrint()` para seguimiento
- Verificar conectividad de red

### Problemas Comunes
1. **TV no encontrada**: Verificar IP y puerto
2. **Comandos no funcionan**: Verificar protocolo correcto
3. **Timeout**: Ajustar timeouts en servicios

## 🔄 Flujo de Navegación

```
HomeScreen
├── Escanear TVs → Lista actualizada
├── Registrar TV → Formulario → Validación → Lista
├── Seleccionar TV → Estado actualizado
├── Control Remoto → RemoteControlScreen
└── Configuraciones → SettingsScreen
```

## 📝 Notas de Desarrollo

- **Hot Reload**: Soportado completamente
- **Estado**: Manejado con StatefulWidget
- **Persistencia**: SharedPreferences para datos locales
- **Async**: Uso extensivo de async/await
- **Error Handling**: Try-catch en todos los servicios

## 🔮 Futuras Mejoras

- [ ] Soporte para más marcas de TV
- [ ] Control por voz
- [ ] Macros de comandos
- [ ] Interfaz de configuración avanzada
- [ ] Soporte para múltiples TVs simultáneas
- [ ] Widgets de acceso rápido

---

## 📚 Documentación Completa

Para acceder a toda la documentación del proyecto, consulta:

- **[📍 Índice de Documentación](docs/INDEX.md)** - Navegación completa
- **[🔍 Auditoría Final](docs/AUDITORIA_FINAL.md)** - Reporte de auditoría completo
- **[🚀 Inicio Rápido](docs/INICIO_RAPIDO.md)** - Guía para comenzar
- **[🏗️ Arquitectura](docs/ARCHITECTURE.md)** - Diseño del sistema
- **[📡 Protocolos de TV](docs/TV_PROTOCOLS.md)** - Comunicación con TVs
- **[🐛 Troubleshooting](docs/TROUBLESHOOTING.md)** - Solución de problemas

---

**Desarrollado con Flutter 💙**