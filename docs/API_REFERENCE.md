# API Reference - Smart TV Manager

## 📋 Índice
- [Servicios de Red](#servicios-de-red)
- [Servicios de Control Remoto](#servicios-de-control-remoto)
- [Servicio de Almacenamiento](#servicio-de-almacenamiento)
- [Servicio Philips](#servicio-philips)
- [Modelos de Datos](#modelos-de-datos)
- [Utilidades](#utilidades)

## 🌐 Servicios de Red

### RealNetworkService

#### `scanNetworkForTVs()`
Escanea la red local en busca de Smart TVs.

```dart
Future<List<SmartTV>> scanNetworkForTVs()
```

**Retorna**: `Future<List<SmartTV>>` - Lista de TVs encontradas
**Throws**: Ninguna (maneja errores internamente)

**Ejemplo**:
```dart
final networkService = RealNetworkService();
final tvs = await networkService.scanNetworkForTVs();
print('Encontradas ${tvs.length} TVs');
```

#### `validateTVConnection(SmartTV tv)`
Valida la conexión con una TV específica.

```dart
Future<bool> validateTVConnection(SmartTV tv)
```

**Parámetros**:
- `tv`: SmartTV - Objeto TV a validar

**Retorna**: `Future<bool>` - true si la conexión es exitosa
**Throws**: Ninguna (maneja errores internamente)

#### `pairWithTV(SmartTV tv)`
Intenta emparejar con una TV (Samsung/LG requieren emparejamiento).

```dart
Future<bool> pairWithTV(SmartTV tv)
```

**Parámetros**:
- `tv`: SmartTV - TV para emparejar

**Retorna**: `Future<bool>` - true si el emparejamiento es exitoso

---

## 📺 Servicios de Control Remoto

### TVRemoteService

#### `sendCommand(SmartTV tv, String command)`
Envía un comando a la TV especificada.

```dart
Future<bool> sendCommand(SmartTV tv, String command)
```

**Parámetros**:
- `tv`: SmartTV - TV de destino
- `command`: String - Comando a enviar

**Comandos soportados**:
- `power` - Encender/Apagar
- `volume_up` / `volume_down` - Control de volumen
- `mute` - Silenciar
- `channel_up` / `channel_down` - Cambiar canal
- `home` - Ir al inicio
- `back` - Volver
- `up` / `down` / `left` / `right` - Navegación
- `enter` - Confirmar
- `menu` - Menú

**Retorna**: `Future<bool>` - true si el comando se envió exitosamente

**Ejemplo**:
```dart
final remoteService = TVRemoteService();
final success = await remoteService.sendCommand(selectedTV, 'power');
if (success) {
  print('Comando enviado exitosamente');
}
```

### Métodos Internos por Marca

#### `_sendSamsungCommand(SmartTV tv, String command)`
Control específico para TVs Samsung via WebSocket.

**Protocolo**: WebSocket
**Puerto**: 8001/8080
**Formato**: JSON con estructura específica Samsung

#### `_sendLGCommand(SmartTV tv, String command)`
Control específico para TVs LG WebOS via WebSocket.

**Protocolo**: WebSocket
**Puerto**: 3000
**Formato**: JSON con códigos de tecla LG

#### `_sendSonyCommand(SmartTV tv, String command)`
Control específico para TVs Sony Bravia via HTTP.

**Protocolo**: HTTP POST
**Puerto**: 80/8080
**Formato**: JSON con códigos IRCC

#### `_sendRokuCommand(SmartTV tv, String command)`
Control específico para dispositivos Roku via HTTP.

**Protocolo**: HTTP POST
**Puerto**: 8060
**Formato**: Endpoints REST específicos

---

## 💾 Servicio de Almacenamiento

### TVStorageService

#### `loadTVs()`
Carga la lista de TVs guardadas desde el almacenamiento local.

```dart
static Future<List<SmartTV>> loadTVs()
```

**Retorna**: `Future<List<SmartTV>>` - Lista de TVs guardadas
**Throws**: Ninguna (retorna lista vacía en caso de error)

#### `saveTVs(List<SmartTV> tvs)`
Guarda la lista de TVs en el almacenamiento local.

```dart
static Future<void> saveTVs(List<SmartTV> tvs)
```

**Parámetros**:
- `tvs`: List<SmartTV> - Lista de TVs a guardar

#### `getSelectedTVId()`
Obtiene el ID de la TV seleccionada actualmente.

```dart
static Future<String?> getSelectedTVId()
```

**Retorna**: `Future<String?>` - ID de la TV seleccionada o null

#### `setSelectedTVId(String tvId)`
Establece la TV seleccionada por ID.

```dart
static Future<void> setSelectedTVId(String tvId)
```

**Parámetros**:
- `tvId`: String - ID de la TV a seleccionar

---

## 📱 Servicio Philips

### PhilipsTvDirectService

#### Constructor
```dart
PhilipsTvDirectService({String? tvIpAddress})
```

**Parámetros**:
- `tvIpAddress`: String? - IP de la TV Philips (opcional, default: '192.168.0.41')

#### `sendKey(String key)`
Envía una tecla específica a la TV Philips.

```dart
Future<void> sendKey(String key)
```

**Parámetros**:
- `key`: String - Nombre de la tecla a enviar

**Teclas soportadas**:
- `Standby` - Power
- `CursorUp` / `CursorDown` / `CursorLeft` / `CursorRight` - Navegación
- `Confirm` - OK/Enter
- `VolumeUp` / `VolumeDown` - Volumen
- `Mute` - Silenciar
- `Back` / `Home` / `Options` - Navegación
- `Digit0` - `Digit9` - Números

**Ejemplo**:
```dart
final philipsService = PhilipsTvDirectService(tvIpAddress: '192.168.1.100');
await philipsService.sendKey('Standby');
```

#### `setVolume(double volume)`
Establece el volumen de la TV.

```dart
Future<void> setVolume(double volume)
```

**Parámetros**:
- `volume`: double - Nivel de volumen (0-100)

#### `openApp(String appName)`
Abre una aplicación específica en la TV.

```dart
Future<void> openApp(String appName)
```

**Parámetros**:
- `appName`: String - Nombre de la aplicación

**Apps soportadas**:
- `Netflix`
- `YouTube`
- `Disney+`

---

## 📊 Modelos de Datos

### SmartTV

#### Constructor
```dart
SmartTV({
  String? id,
  required String name,
  required TVBrand brand,
  required String ip,
  int port = 8080,
  String room = 'Sin asignar',
  TVProtocol protocol = TVProtocol.http,
  String macAddress = '',
  String model = '',
  Map<String, dynamic> capabilities = const {},
  bool isOnline = false,
  bool isRegistered = false,
  bool isFavorite = false,
  bool isConnecting = false,
  bool isPaired = false,
  DateTime? lastPing,
  DateTime? lastControlled,
  String? authToken,
})
```

#### Métodos

##### `copyWith({...})`
Crea una copia del objeto con propiedades modificadas.

```dart
SmartTV copyWith({
  String? name,
  TVBrand? brand,
  String? ip,
  // ... otros parámetros
})
```

##### `toJson()`
Convierte el objeto a Map para serialización.

```dart
Map<String, dynamic> toJson()
```

##### `fromJson(Map<String, dynamic> json)`
Factory constructor para crear objeto desde JSON.

```dart
factory SmartTV.fromJson(Map<String, dynamic> json)
```

#### Propiedades Calculadas

##### `brandIcon`
Retorna el icono apropiado para la marca.

```dart
IconData get brandIcon
```

##### `statusColor`
Retorna el color de estado basado en la conexión.

```dart
Color get statusColor
```

##### `statusText`
Retorna el texto de estado legible.

```dart
String get statusText
```

### Enums

#### TVBrand
```dart
enum TVBrand {
  samsung,
  lg,
  sony,
  philips,
  tcl,
  hisense,
  xiaomi,
  roku,
  androidtv,
  unknown
}
```

#### TVProtocol
```dart
enum TVProtocol {
  http,
  websocket,
  upnp,
  roku,
  unknown
}
```

---

## 🎨 Utilidades de Tema

### AppTheme

#### Colores
```dart
static const Color backgroundPrimary = Color(0xFFE8E8E8);
static const Color backgroundSecondary = Color(0xFFF5F5F5);
static const Color textPrimary = Color(0xFF2D3748);
static const Color textSecondary = Color(0xFF718096);
static const Color accentBlue = Color(0xFF4299E1);
static const Color accentGreen = Color(0xFF48BB78);
static const Color accentRed = Color(0xFFE53E3E);
```

#### `concaveDecoration({...})`
Crea decoración neumórfica cóncava (hundida).

```dart
static BoxDecoration concaveDecoration({
  required Color backgroundColor,
  double borderRadius = 8.0,
})
```

#### `convexDecoration({...})`
Crea decoración neumórfica convexa (elevada).

```dart
static BoxDecoration convexDecoration({
  required Color backgroundColor,
  double borderRadius = 8.0,
})
```

---

## 🔧 Configuración de Red

### Puertos por Marca
- **Samsung**: 8001, 8080
- **LG**: 3000
- **Sony**: 80, 8080
- **Philips**: 1925
- **Roku**: 8060
- **Android TV**: 7345

### Timeouts
- **Conexión**: 5 segundos
- **Recepción**: 5 segundos
- **Validación**: 3 segundos

### Rangos de Escaneo
- **Subnet**: 192.168.1.x (configurable)
- **Rango IP**: 1-50
- **Escaneo paralelo**: Máximo 10 conexiones simultáneas

---

## 🐛 Manejo de Errores

Todos los servicios implementan manejo robusto de errores:

- **Network timeouts**: Manejados silenciosamente
- **Connection refused**: Logged pero no lanza excepción
- **Invalid responses**: Parseados y manejados apropiadamente
- **Storage errors**: Fallback a valores por defecto

### Logging
```dart
debugPrint('🔍 Iniciando escaneo de red...');
debugPrint('✅ TV encontrada: ${tv.name} (${tv.ip})');
debugPrint('❌ Error en escaneo: $e');
```

---

## 📝 Ejemplos de Uso Completos

### Escanear y Controlar TV
```dart
// Inicializar servicios
final networkService = RealNetworkService();
final remoteService = TVRemoteService();

// Escanear red
final tvs = await networkService.scanNetworkForTVs();

// Seleccionar primera TV encontrada
if (tvs.isNotEmpty) {
  final selectedTV = tvs.first;
  
  // Validar conexión
  final isOnline = await networkService.validateTVConnection(selectedTV);
  
  if (isOnline) {
    // Enviar comando
    await remoteService.sendCommand(selectedTV, 'power');
  }
}
```

### Usar Control Philips Directo
```dart
// Inicializar servicio con IP específica
final philipsService = PhilipsTvDirectService(
  tvIpAddress: '192.168.1.100'
);

// Controlar TV
await philipsService.sendKey('Standby');
await philipsService.setVolume(50);
await philipsService.openApp('Netflix');
```

---

Esta referencia cubre todas las APIs públicas disponibles en Smart TV Manager.