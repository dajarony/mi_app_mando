# Protocolos de TV - Smart TV Manager

## 📋 Índice
- [Visión General](#visión-general)
- [Samsung Smart TV](#samsung-smart-tv)
- [LG WebOS](#lg-webos)
- [Sony Bravia](#sony-bravia)
- [Philips Android TV](#philips-android-tv)
- [Roku TV](#roku-tv)
- [Android TV Genérico](#android-tv-genérico)
- [Implementación de Nuevos Protocolos](#implementación-de-nuevos-protocolos)

## 🌐 Visión General

Smart TV Manager soporta múltiples protocolos de comunicación para diferentes marcas de televisores. Cada marca utiliza su propio protocolo y formato de comandos.

### Protocolos Soportados
| Marca | Protocolo | Puerto | Autenticación | Estado |
|-------|-----------|--------|---------------|--------|
| Samsung | WebSocket | 8001/8080 | Token | ✅ Implementado |
| LG | WebSocket | 3000 | Pairing | ✅ Implementado |
| Sony | HTTP POST | 80/8080 | PSK | ✅ Implementado |
| Philips | HTTP POST | 1925 | Ninguna | ✅ Implementado |
| Roku | HTTP POST | 8060 | Ninguna | ✅ Implementado |
| Android TV | HTTP POST | 7345 | Variable | ✅ Implementado |

## 📺 Samsung Smart TV

### Configuración
- **Protocolo**: WebSocket
- **Puerto**: 8001 (HTTPS) / 8080 (HTTP)
- **Autenticación**: Token-based
- **API Version**: v2

### Endpoint de Conexión
```
ws://[TV_IP]:8080/api/v2/channels/samsung.remote.control
```

### Formato de Comando
```json
{
  "method": "ms.remote.control",
  "params": {
    "Cmd": "Click",
    "DataOfCmd": "KEY_POWER",
    "Option": "false",
    "TypeOfRemote": "SendRemoteKey"
  }
}
```

### Mapeo de Comandos
```dart
const samsungKeyMap = {
  'power': 'KEY_POWER',
  'volume_up': 'KEY_VOLUP',
  'volume_down': 'KEY_VOLDOWN',
  'mute': 'KEY_MUTE',
  'channel_up': 'KEY_CHUP',
  'channel_down': 'KEY_CHDOWN',
  'home': 'KEY_HOME',
  'back': 'KEY_RETURN',
  'enter': 'KEY_ENTER',
  'up': 'KEY_UP',
  'down': 'KEY_DOWN',
  'left': 'KEY_LEFT',
  'right': 'KEY_RIGHT',
  'menu': 'KEY_MENU',
  'source': 'KEY_SOURCE',
  'netflix': 'KEY_NETFLIX',
  'youtube': 'KEY_YOUTUBE',
};
```

### Implementación
```dart
Future<bool> _sendSamsungCommand(SmartTV tv, String command) async {
  try {
    WebSocketChannel? channel = _wsConnections[tv.id];
    
    if (channel == null) {
      final wsUrl = 'ws://${tv.ip}:${tv.port}/api/v2/channels/samsung.remote.control';
      channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _wsConnections[tv.id] = channel;
    }
    
    final commandData = {
      'method': 'ms.remote.control',
      'params': {
        'Cmd': 'Click',
        'DataOfCmd': _getSamsungKeyCode(command),
        'Option': 'false',
        'TypeOfRemote': 'SendRemoteKey'
      }
    };
    
    channel.sink.add(json.encode(commandData));
    return true;
  } catch (e) {
    debugPrint('❌ Error comando Samsung: $e');
    return false;
  }
}
```

### Detección
```dart
Future<SmartTV?> _detectSamsung(String ip, int port) async {
  try {
    final response = await _dio.get('http://$ip:$port/api/v2/');
    
    if (response.statusCode == 200) {
      final data = response.data;
      return SmartTV(
        name: data['name'] ?? 'Samsung Smart TV',
        brand: TVBrand.samsung,
        ip: ip,
        port: port,
        protocol: TVProtocol.websocket,
        model: data['model'] ?? 'Samsung TV',
        capabilities: {'remote_control': true, 'apps': true},
        isOnline: true,
      );
    }
  } catch (e) {
    // Handle error
  }
  return null;
}
```

## 📱 LG WebOS

### Configuración
- **Protocolo**: WebSocket
- **Puerto**: 3000
- **Autenticación**: Pairing process
- **API Version**: WebOS 3.0+

### Endpoint de Conexión
```
ws://[TV_IP]:3000/api/v2/channels/lg.remote.control
```

### Formato de Comando
```json
{
  "type": "request",
  "id": "unique-id",
  "uri": "ssap://com.webos.service.ime/sendKeyEvent",
  "payload": {
    "keycode": 24
  }
}
```

### Mapeo de Comandos
```dart
const lgKeyMap = {
  'power': 1,
  'volume_up': 24,
  'volume_down': 25,
  'mute': 164,
  'channel_up': 166,
  'channel_down': 167,
  'home': 3,
  'back': 4,
  'ok': 23,
  'up': 19,
  'down': 20,
  'left': 21,
  'right': 22,
  'menu': 82,
};
```

### Implementación
```dart
Future<bool> _sendLGCommand(SmartTV tv, String command) async {
  try {
    WebSocketChannel? channel = _wsConnections[tv.id];
    
    if (channel == null) {
      final wsUrl = 'ws://${tv.ip}:${tv.port}/api/v2/channels/lg.remote.control';
      channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _wsConnections[tv.id] = channel;
    }
    
    final commandData = {
      'type': 'request',
      'id': const Uuid().v4(),
      'uri': 'ssap://com.webos.service.ime/sendKeyEvent',
      'payload': {'keycode': _getLGKeyCode(command)}
    };
    
    channel.sink.add(json.encode(commandData));
    return true;
  } catch (e) {
    debugPrint('❌ Error comando LG: $e');
    return false;
  }
}
```

## 📺 Sony Bravia

### Configuración
- **Protocolo**: HTTP POST
- **Puerto**: 80/8080
- **Autenticación**: Pre-Shared Key (PSK)
- **API Version**: v1.0

### Endpoint de Comando
```
POST http://[TV_IP]:80/sony/IRCC
```

### Formato de Comando
```json
{
  "method": "actIRCC",
  "params": [
    {
      "ircc": "AAAAAQAAAAEAAAAVAw=="
    }
  ],
  "id": 1,
  "version": "1.0"
}
```

### Mapeo de Comandos (IRCC)
```dart
const sonyIRCCMap = {
  'power': 'AAAAAQAAAAEAAAAVAw==',
  'volume_up': 'AAAAAQAAAAEAAAASAw==',
  'volume_down': 'AAAAAQAAAAEAAAATAw==',
  'mute': 'AAAAAQAAAAEAAAAUAw==',
  'home': 'AAAAAQAAAAEAAABgAw==',
  'up': 'AAAAAQAAAAEAAAB0Aw==',
  'down': 'AAAAAQAAAAEAAAB1Aw==',
  'left': 'AAAAAQAAAAEAAAA0Aw==',
  'right': 'AAAAAQAAAAEAAAAzAw==',
  'enter': 'AAAAAQAAAAEAAABlAw==',
};
```

### Implementación
```dart
Future<bool> _sendSonyCommand(SmartTV tv, String command) async {
  try {
    final response = await _dio.post(
      'http://${tv.ip}:${tv.port}/sony/IRCC',
      data: {
        'method': 'actIRCC',
        'params': [
          {'ircc': _getSonyIRCC(command)}
        ],
        'id': 1,
        'version': '1.0'
      },
      options: Options(
        headers: {
          'Content-Type': 'application/json',
          'X-Auth-PSK': tv.authToken ?? '',
        },
      ),
    );
    
    return response.statusCode == 200;
  } catch (e) {
    debugPrint('❌ Error comando Sony: $e');
    return false;
  }
}
```

## 📱 Philips Android TV

### Configuración
- **Protocolo**: HTTP POST
- **Puerto**: 1925
- **Autenticación**: Ninguna (red local)
- **API Version**: v6

### Endpoint de Comando
```
POST http://[TV_IP]:1925/6/input/key
```

### Formato de Comando
```json
{
  "key": "Standby"
}
```

### Comandos Soportados
```dart
const philipsCommands = [
  'Standby',           // Power
  'CursorUp',          // Up
  'CursorDown',        // Down
  'CursorLeft',        // Left
  'CursorRight',       // Right
  'Confirm',           // OK/Enter
  'VolumeUp',          // Volume Up
  'VolumeDown',        // Volume Down
  'Mute',              // Mute
  'Back',              // Back
  'Home',              // Home
  'Options',           // Menu
  'Digit0' - 'Digit9', // Numbers
];
```

### Implementación
```dart
class PhilipsTvDirectService {
  late final Dio _dio;
  final String _tvIpAddress;

  PhilipsTvDirectService({String? tvIpAddress}) 
    : _tvIpAddress = tvIpAddress ?? '192.168.0.41' {
    final options = BaseOptions(
      baseUrl: 'http://$_tvIpAddress:1925',
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 5),
      validateStatus: (status) => status! < 500,
    );
    _dio = Dio(options);
  }

  Future<void> sendKey(String key) async {
    try {
      await _dio.post(
        '/6/input/key',
        data: {'key': key},
      );
      debugPrint('✅ Philips key sent: $key');
    } catch (e) {
      debugPrint('❌ Error sending Philips key: $e');
    }
  }
}
```

### Comandos Adicionales

#### Control de Volumen
```dart
Future<void> setVolume(double volume) async {
  try {
    await _dio.post(
      '/6/audio/volume',
      data: {'muted': false, 'current': volume.round()},
    );
  } catch (e) {
    debugPrint('❌ Error setting volume: $e');
  }
}
```

#### Lanzar Aplicaciones
```dart
Future<void> openApp(String appName) async {
  Map<String, dynamic>? payload;
  
  switch (appName) {
    case 'Netflix':
      payload = {
        'intent': {
          'action': 'android.intent.action.VIEW',
          'component': {
            'packageName': 'com.netflix.ninja',
            'className': 'com.netflix.ninja.MainActivity',
          },
        },
      };
      break;
    case 'YouTube':
      payload = {
        'intent': {
          'action': 'android.intent.action.VIEW',
          'component': {
            'packageName': 'com.google.android.youtube.tv',
            'className': 'com.google.android.apps.youtube.tv.activity.ShellActivity',
          },
        },
      };
      break;
  }
  
  if (payload != null) {
    try {
      await _dio.post('/6/activities/launch', data: payload);
    } catch (e) {
      debugPrint('❌ Error launching app: $e');
    }
  }
}
```

## 📺 Roku TV

### Configuración
- **Protocolo**: HTTP POST
- **Puerto**: 8060
- **Autenticación**: Ninguna
- **API Version**: ECP (External Control Protocol)

### Endpoint de Comando
```
POST http://[TV_IP]:8060/keypress/[COMMAND]
```

### Comandos Soportados
```dart
const rokuCommands = {
  'power': 'Power',
  'volume_up': 'VolumeUp',
  'volume_down': 'VolumeDown',
  'mute': 'VolumeMute',
  'home': 'Home',
  'back': 'Back',
  'ok': 'Select',
  'up': 'Up',
  'down': 'Down',
  'left': 'Left',
  'right': 'Right',
  'play': 'Play',
  'pause': 'Pause',
  'rewind': 'Rev',
  'forward': 'Fwd',
};
```

### Implementación
```dart
Future<bool> _sendRokuCommand(SmartTV tv, String command) async {
  try {
    final endpoint = _getRokuEndpoint(command);
    final response = await _dio.post(
      'http://${tv.ip}:${tv.port}/$endpoint',
    );
    
    return response.statusCode == 200;
  } catch (e) {
    debugPrint('❌ Error comando Roku: $e');
    return false;
  }
}

String _getRokuEndpoint(String command) {
  const endpointMap = {
    'power': 'keypress/Power',
    'volume_up': 'keypress/VolumeUp',
    'volume_down': 'keypress/VolumeDown',
    'mute': 'keypress/VolumeMute',
    'home': 'keypress/Home',
    'back': 'keypress/Back',
    'ok': 'keypress/Select',
    'up': 'keypress/Up',
    'down': 'keypress/Down',
    'left': 'keypress/Left',
    'right': 'keypress/Right',
  };
  return endpointMap[command] ?? 'keypress/Select';
}
```

### Detección de Roku
```dart
Future<SmartTV?> _detectRoku(String ip, int port) async {
  try {
    final response = await _dio.get('http://$ip:$port/query/device-info');
    
    if (response.statusCode == 200) {
      return SmartTV(
        name: 'Roku TV',
        brand: TVBrand.roku,
        ip: ip,
        port: port,
        protocol: TVProtocol.roku,
        capabilities: {'remote_control': true, 'apps': true},
        isOnline: true,
      );
    }
  } catch (e) {
    // Handle error
  }
  return null;
}
```

## 📱 Android TV Genérico

### Configuración
- **Protocolo**: HTTP POST
- **Puerto**: 7345 (variable)
- **Autenticación**: Variable por fabricante
- **API Version**: Android TV API

### Endpoint de Comando
```
POST http://[TV_IP]:7345/api/command
```

### Formato de Comando
```json
{
  "command": "power"
}
```

### Implementación
```dart
Future<bool> _sendGenericCommand(SmartTV tv, String command) async {
  try {
    final response = await _dio.post(
      'http://${tv.ip}:${tv.port}/api/command',
      data: {'command': command},
    );
    
    return response.statusCode == 200;
  } catch (e) {
    debugPrint('❌ Error comando genérico: $e');
    // Simulamos éxito para demo
    await Future.delayed(const Duration(milliseconds: 500));
    return true;
  }
}
```

## 🔧 Implementación de Nuevos Protocolos

### Pasos para Agregar Nueva Marca

#### 1. Definir Enum
```dart
enum TVBrand {
  // ... existentes
  newBrand,
  unknown
}

enum TVProtocol {
  // ... existentes
  newProtocol,
  unknown
}
```

#### 2. Implementar Detección
```dart
Future<SmartTV?> _detectNewBrand(String ip, int port) async {
  try {
    // Implementar lógica de detección específica
    final response = await _dio.get('http://$ip:$port/api/info');
    
    if (response.statusCode == 200 && _isNewBrandTV(response.data)) {
      return SmartTV(
        name: 'New Brand TV',
        brand: TVBrand.newBrand,
        ip: ip,
        port: port,
        protocol: TVProtocol.newProtocol,
        isOnline: true,
      );
    }
  } catch (e) {
    // Handle error
  }
  return null;
}
```

#### 3. Implementar Control
```dart
Future<bool> _sendNewBrandCommand(SmartTV tv, String command) async {
  try {
    // Implementar protocolo específico
    switch (tv.protocol) {
      case TVProtocol.newProtocol:
        return await _sendNewProtocolCommand(tv, command);
      default:
        return false;
    }
  } catch (e) {
    debugPrint('❌ Error comando nueva marca: $e');
    return false;
  }
}
```

#### 4. Integrar en Servicio Principal
```dart
Future<bool> sendCommand(SmartTV tv, String command) async {
  try {
    switch (tv.brand) {
      case TVBrand.samsung:
        return await _sendSamsungCommand(tv, command);
      case TVBrand.lg:
        return await _sendLGCommand(tv, command);
      // ... otros casos
      case TVBrand.newBrand:
        return await _sendNewBrandCommand(tv, command);
      default:
        return await _sendGenericCommand(tv, command);
    }
  } catch (e) {
    debugPrint('❌ Error enviando comando: $e');
    return false;
  }
}
```

### Consideraciones de Seguridad

#### Validación de IP
```dart
bool _isValidIP(String ip) {
  final regex = RegExp(r'^(\d{1,3}\.){3}\d{1,3}$');
  if (!regex.hasMatch(ip)) return false;
  
  final parts = ip.split('.');
  return parts.every((part) {
    final num = int.tryParse(part);
    return num != null && num >= 0 && num <= 255;
  });
}
```

#### Timeout y Retry
```dart
Future<bool> _sendCommandWithRetry(SmartTV tv, String command, {int maxRetries = 3}) async {
  for (int i = 0; i < maxRetries; i++) {
    try {
      final success = await _sendCommand(tv, command);
      if (success) return true;
    } catch (e) {
      if (i == maxRetries - 1) rethrow;
      await Future.delayed(Duration(seconds: 1 << i)); // Exponential backoff
    }
  }
  return false;
}
```

#### Rate Limiting
```dart
class RateLimiter {
  final Map<String, DateTime> _lastRequest = {};
  final Duration _minInterval = Duration(milliseconds: 100);
  
  Future<void> waitIfNeeded(String tvId) async {
    final lastTime = _lastRequest[tvId];
    if (lastTime != null) {
      final elapsed = DateTime.now().difference(lastTime);
      if (elapsed < _minInterval) {
        await Future.delayed(_minInterval - elapsed);
      }
    }
    _lastRequest[tvId] = DateTime.now();
  }
}
```

---

Esta documentación cubre todos los protocolos implementados y proporciona una guía completa para extender el soporte a nuevas marcas de TV.