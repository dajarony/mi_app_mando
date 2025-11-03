# Guía de Solución de Problemas - Smart TV Manager

## 📋 Índice
- [Problemas Comunes](#problemas-comunes)
- [Problemas de Red](#problemas-de-red)
- [Problemas de TV Específicos](#problemas-de-tv-específicos)
- [Problemas de la Aplicación](#problemas-de-la-aplicación)
- [Herramientas de Diagnóstico](#herramientas-de-diagnóstico)
- [FAQ](#faq)

## 🚨 Problemas Comunes

### 1. TV No Encontrada Durante el Escaneo

#### Síntomas
- El escaneo no encuentra ninguna TV
- TVs conocidas no aparecen en la lista
- Mensaje "No se encontraron TVs nuevas en la red"

#### Causas Posibles
- TV no está en la misma red
- TV tiene funciones de red deshabilitadas
- Firewall bloqueando conexiones
- TV en modo standby profundo

#### Soluciones
```dart
// 1. Verificar conectividad básica
Future<bool> _pingTV(String ip) async {
  try {
    final result = await Process.run('ping', ['-c', '1', ip]);
    return result.exitCode == 0;
  } catch (e) {
    return false;
  }
}

// 2. Verificar puertos específicos
Future<bool> _checkPort(String ip, int port) async {
  try {
    final socket = await Socket.connect(ip, port, timeout: Duration(seconds: 3));
    socket.destroy();
    return true;
  } catch (e) {
    return false;
  }
}
```

#### Pasos de Diagnóstico
1. **Verificar red**: Asegurar que dispositivo y TV están en la misma red WiFi
2. **Habilitar funciones de red en TV**: Ir a configuraciones de red de la TV
3. **Probar registro manual**: Usar la IP conocida de la TV
4. **Verificar firewall**: Temporalmente deshabilitar firewall del router

### 2. Comandos de Control Remoto No Funcionan

#### Síntomas
- Botones no responden
- TV no reacciona a comandos
- Timeout en envío de comandos

#### Diagnóstico
```dart
// Verificar estado de conexión
Future<void> _diagnoseConnection(SmartTV tv) async {
  debugPrint('🔍 Diagnosticando TV: ${tv.name}');
  debugPrint('📍 IP: ${tv.ip}:${tv.port}');
  debugPrint('🏷️ Marca: ${tv.brand}');
  debugPrint('🔌 Protocolo: ${tv.protocol}');
  
  // Test básico de conectividad
  final isReachable = await _pingTV(tv.ip);
  debugPrint('🌐 Ping: ${isReachable ? "✅" : "❌"}');
  
  // Test de puerto específico
  final isPortOpen = await _checkPort(tv.ip, tv.port);
  debugPrint('🚪 Puerto ${tv.port}: ${isPortOpen ? "✅" : "❌"}');
  
  // Test de protocolo específico
  final protocolTest = await _testProtocol(tv);
  debugPrint('📡 Protocolo: ${protocolTest ? "✅" : "❌"}');
}
```

#### Soluciones por Marca

##### Samsung
```dart
// Verificar WebSocket
Future<bool> _testSamsungConnection(SmartTV tv) async {
  try {
    final channel = WebSocketChannel.connect(
      Uri.parse('ws://${tv.ip}:${tv.port}/api/v2/')
    );
    
    // Enviar comando de prueba
    channel.sink.add(json.encode({
      'method': 'ms.remote.control',
      'params': {
        'Cmd': 'Click',
        'DataOfCmd': 'KEY_POWER',
        'Option': 'false',
        'TypeOfRemote': 'SendRemoteKey'
      }
    }));
    
    await Future.delayed(Duration(seconds: 2));
    channel.sink.close();
    return true;
  } catch (e) {
    debugPrint('❌ Samsung test failed: $e');
    return false;
  }
}
```

##### Philips
```dart
// Verificar API HTTP
Future<bool> _testPhilipsConnection(String ip) async {
  try {
    final dio = Dio();
    final response = await dio.post(
      'http://$ip:1925/6/input/key',
      data: {'key': 'Standby'},
      options: Options(
        receiveTimeout: Duration(seconds: 3),
        sendTimeout: Duration(seconds: 3),
      ),
    );
    return response.statusCode == 200;
  } catch (e) {
    debugPrint('❌ Philips test failed: $e');
    return false;
  }
}
```

### 3. Aplicación Se Cuelga o Crashea

#### Síntomas
- App se cierra inesperadamente
- Pantalla en blanco
- No responde a toques

#### Logs de Debug
```dart
// Habilitar logging detallado
void _enableDebugLogging() {
  // En main.dart
  if (kDebugMode) {
    // Capturar errores de Flutter
    FlutterError.onError = (FlutterErrorDetails details) {
      debugPrint('🚨 Flutter Error: ${details.exception}');
      debugPrint('📍 Stack: ${details.stack}');
    };
    
    // Capturar errores de Dart
    PlatformDispatcher.instance.onError = (error, stack) {
      debugPrint('🚨 Dart Error: $error');
      debugPrint('📍 Stack: $stack');
      return true;
    };
  }
}
```

#### Soluciones
1. **Restart en caliente**: `flutter run` y presionar `R`
2. **Limpiar build**: `flutter clean && flutter pub get`
3. **Verificar memoria**: Cerrar otras apps
4. **Actualizar dependencias**: `flutter pub upgrade`

## 🌐 Problemas de Red

### 1. Timeout de Conexión

#### Configuración de Timeouts
```dart
// Ajustar timeouts según la red
final dio = Dio(BaseOptions(
  connectTimeout: Duration(seconds: 10), // Aumentar para redes lentas
  receiveTimeout: Duration(seconds: 10),
  sendTimeout: Duration(seconds: 5),
));
```

#### Implementar Retry Logic
```dart
Future<bool> _sendCommandWithRetry(SmartTV tv, String command) async {
  const maxRetries = 3;
  const baseDelay = Duration(seconds: 1);
  
  for (int attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      final success = await _sendCommand(tv, command);
      if (success) return true;
    } catch (e) {
      debugPrint('❌ Intento $attempt falló: $e');
      
      if (attempt < maxRetries) {
        // Exponential backoff
        final delay = baseDelay * (1 << (attempt - 1));
        await Future.delayed(delay);
      }
    }
  }
  
  return false;
}
```

### 2. Problemas de Firewall

#### Puertos que Deben Estar Abiertos
```dart
const requiredPorts = {
  'Samsung': [8001, 8080],
  'LG': [3000],
  'Sony': [80, 8080],
  'Philips': [1925],
  'Roku': [8060],
  'Android TV': [7345],
};
```

#### Test de Puertos
```dart
Future<Map<int, bool>> _testPorts(String ip, List<int> ports) async {
  final results = <int, bool>{};
  
  for (final port in ports) {
    try {
      final socket = await Socket.connect(
        ip, 
        port, 
        timeout: Duration(seconds: 3)
      );
      socket.destroy();
      results[port] = true;
      debugPrint('✅ Puerto $port abierto');
    } catch (e) {
      results[port] = false;
      debugPrint('❌ Puerto $port cerrado: $e');
    }
  }
  
  return results;
}
```

### 3. Problemas de Subnet

#### Detectar Subnet Actual
```dart
Future<String?> _getCurrentSubnet() async {
  try {
    // Obtener interfaces de red
    final interfaces = await NetworkInterface.list();
    
    for (final interface in interfaces) {
      for (final addr in interface.addresses) {
        if (addr.type == InternetAddressType.IPv4 && 
            !addr.isLoopback && 
            addr.address.startsWith('192.168.')) {
          
          final parts = addr.address.split('.');
          return '${parts[0]}.${parts[1]}.${parts[2]}';
        }
      }
    }
  } catch (e) {
    debugPrint('❌ Error obteniendo subnet: $e');
  }
  
  return '192.168.1'; // Fallback
}
```

## 📺 Problemas de TV Específicos

### Samsung Smart TV

#### Problema: WebSocket Connection Failed
```dart
// Solución: Verificar certificados SSL
Future<bool> _connectSamsungSecure(SmartTV tv) async {
  try {
    // Intentar HTTPS primero
    final secureChannel = WebSocketChannel.connect(
      Uri.parse('wss://${tv.ip}:8001/api/v2/channels/samsung.remote.control')
    );
    
    // Si falla, usar HTTP
    if (secureChannel == null) {
      final channel = WebSocketChannel.connect(
        Uri.parse('ws://${tv.ip}:8080/api/v2/channels/samsung.remote.control')
      );
      return channel != null;
    }
    
    return true;
  } catch (e) {
    debugPrint('❌ Samsung connection error: $e');
    return false;
  }
}
```

#### Problema: Requiere Emparejamiento
```dart
Future<bool> _pairSamsung(SmartTV tv) async {
  try {
    // Mostrar código de emparejamiento en TV
    final pairingData = {
      'method': 'ms.channel.connect',
      'params': {
        'name': 'Smart TV Manager',
        'description': 'Control remoto móvil',
        'id': 'smart_tv_manager',
        'token': tv.authToken ?? '',
      }
    };
    
    // Enviar solicitud de emparejamiento
    // Usuario debe aceptar en TV
    
    return true;
  } catch (e) {
    return false;
  }
}
```

### LG WebOS

#### Problema: Pairing Required
```dart
Future<String?> _pairLG(SmartTV tv) async {
  try {
    final channel = WebSocketChannel.connect(
      Uri.parse('ws://${tv.ip}:3000/')
    );
    
    // Solicitar emparejamiento
    final pairingRequest = {
      'type': 'register',
      'id': 'register_0',
      'payload': {
        'forcePairing': false,
        'pairingType': 'PROMPT',
        'manifest': {
          'manifestVersion': 1,
          'appVersion': '1.0.0',
          'signed': {
            'created': DateTime.now().toIso8601String(),
            'appId': 'com.smarttvmanager.remote',
            'vendorId': 'com.smarttvmanager',
            'localizedAppNames': {
              'english': 'Smart TV Manager',
              'spanish': 'Smart TV Manager'
            },
            'permissions': [
              'LAUNCH',
              'LAUNCH_WEBAPP',
              'APP_TO_APP',
              'CLOSE',
              'TEST_OPEN',
              'TEST_PROTECTED',
              'CONTROL_AUDIO',
              'CONTROL_DISPLAY',
              'CONTROL_INPUT_JOYSTICK',
              'CONTROL_INPUT_MEDIA_RECORDING',
              'CONTROL_INPUT_MEDIA_PLAYBACK',
              'CONTROL_INPUT_TV',
              'CONTROL_POWER',
              'READ_APP_STATUS',
              'READ_CURRENT_CHANNEL',
              'READ_INPUT_DEVICE_LIST',
              'READ_NETWORK_STATE',
              'READ_RUNNING_APPS',
              'READ_TV_CHANNEL_LIST',
              'WRITE_NOTIFICATION_TOAST',
              'READ_POWER_STATE',
              'READ_COUNTRY_INFO'
            ]
          }
        }
      }
    };
    
    channel.sink.add(json.encode(pairingRequest));
    
    // Escuchar respuesta
    await for (final message in channel.stream) {
      final data = json.decode(message);
      if (data['type'] == 'registered') {
        return data['payload']['client-key'];
      }
    }
    
    return null;
  } catch (e) {
    debugPrint('❌ LG pairing error: $e');
    return null;
  }
}
```

### Sony Bravia

#### Problema: PSK Required
```dart
// Configurar Pre-Shared Key
Future<bool> _configureSonyPSK(SmartTV tv, String psk) async {
  try {
    final updatedTV = tv.copyWith(authToken: psk);
    
    // Test con PSK
    final response = await _dio.post(
      'http://${tv.ip}:${tv.port}/sony/system',
      data: {
        'method': 'getSystemInformation',
        'params': [],
        'id': 1,
        'version': '1.0'
      },
      options: Options(
        headers: {
          'X-Auth-PSK': psk,
        },
      ),
    );
    
    return response.statusCode == 200;
  } catch (e) {
    debugPrint('❌ Sony PSK error: $e');
    return false;
  }
}
```

### Philips Android TV

#### Problema: API No Responde
```dart
Future<bool> _troubleshootPhilips(String ip) async {
  // Test diferentes endpoints
  final endpoints = [
    '/6/input/key',
    '/1/input/key',
    '/api/v1/input/key',
  ];
  
  for (final endpoint in endpoints) {
    try {
      final response = await _dio.post(
        'http://$ip:1925$endpoint',
        data: {'key': 'Standby'},
      );
      
      if (response.statusCode == 200) {
        debugPrint('✅ Philips endpoint funcional: $endpoint');
        return true;
      }
    } catch (e) {
      debugPrint('❌ Endpoint $endpoint falló: $e');
    }
  }
  
  return false;
}
```

## 📱 Problemas de la Aplicación

### 1. UI Overflow Errors

#### Solución para Dropdowns
```dart
// Usar isExpanded para evitar overflow
DropdownButtonFormField<TVBrand>(
  isExpanded: true, // Importante!
  value: _selectedBrand,
  decoration: InputDecoration(
    contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 16),
  ),
  items: TVBrand.values.map((brand) {
    return DropdownMenuItem(
      value: brand,
      child: Text(
        brand.name.toUpperCase(),
        overflow: TextOverflow.ellipsis, // Evitar overflow de texto
      ),
    );
  }).toList(),
)
```

### 2. Memory Leaks

#### Cerrar Recursos Correctamente
```dart
class _RemoteControlScreenState extends State<RemoteControlScreen> {
  late StreamSubscription _subscription;
  late Timer _timer;
  
  @override
  void dispose() {
    // Cerrar WebSocket connections
    _remoteService.closeAllConnections();
    
    // Cancelar subscriptions
    _subscription.cancel();
    
    // Cancelar timers
    _timer.cancel();
    
    super.dispose();
  }
}
```

### 3. State Management Issues

#### Verificar mounted antes de setState
```dart
Future<void> _updateTVStatus() async {
  final isOnline = await _networkService.validateTVConnection(tv);
  
  // Siempre verificar mounted
  if (mounted) {
    setState(() {
      _selectedTV = _selectedTV?.copyWith(isOnline: isOnline);
    });
  }
}
```

## 🔧 Herramientas de Diagnóstico

### 1. Network Scanner Tool

```dart
class NetworkDiagnostic {
  static Future<Map<String, dynamic>> scanNetwork() async {
    final results = <String, dynamic>{};
    
    // Obtener información de red
    results['subnet'] = await _getCurrentSubnet();
    results['interfaces'] = await _getNetworkInterfaces();
    
    // Escanear dispositivos
    results['devices'] = await _scanDevices();
    
    // Test de conectividad
    results['connectivity'] = await _testConnectivity();
    
    return results;
  }
  
  static Future<List<String>> _scanDevices() async {
    final devices = <String>[];
    final subnet = await _getCurrentSubnet() ?? '192.168.1';
    
    final futures = <Future>[];
    for (int i = 1; i <= 254; i++) {
      futures.add(_pingDevice('$subnet.$i').then((isAlive) {
        if (isAlive) devices.add('$subnet.$i');
      }));
    }
    
    await Future.wait(futures);
    return devices;
  }
}
```

### 2. TV Protocol Tester

```dart
class ProtocolTester {
  static Future<Map<String, bool>> testAllProtocols(String ip) async {
    final results = <String, bool>{};
    
    // Test Samsung
    results['Samsung'] = await _testSamsung(ip);
    
    // Test LG
    results['LG'] = await _testLG(ip);
    
    // Test Sony
    results['Sony'] = await _testSony(ip);
    
    // Test Philips
    results['Philips'] = await _testPhilips(ip);
    
    // Test Roku
    results['Roku'] = await _testRoku(ip);
    
    return results;
  }
}
```

### 3. Debug Panel

```dart
class DebugPanel extends StatelessWidget {
  final SmartTV tv;
  
  const DebugPanel({required this.tv});
  
  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      title: Text('Debug Info'),
      children: [
        ListTile(
          title: Text('IP Address'),
          subtitle: Text(tv.ip),
        ),
        ListTile(
          title: Text('Port'),
          subtitle: Text(tv.port.toString()),
        ),
        ListTile(
          title: Text('Protocol'),
          subtitle: Text(tv.protocol.name),
        ),
        ListTile(
          title: Text('Status'),
          subtitle: Text(tv.statusText),
          trailing: Icon(
            Icons.circle,
            color: tv.statusColor,
          ),
        ),
        ElevatedButton(
          onPressed: () => _runDiagnostic(tv),
          child: Text('Run Diagnostic'),
        ),
      ],
    );
  }
}
```

## ❓ FAQ

### P: ¿Por qué mi TV Samsung no aparece en el escaneo?
**R**: Asegúrate de que:
- La TV esté encendida y conectada a WiFi
- Las funciones de red estén habilitadas en configuraciones
- No haya firewall bloqueando los puertos 8001/8080

### P: ¿Los comandos funcionan pero la TV no responde?
**R**: Esto puede indicar:
- Protocolo incorrecto para tu modelo de TV
- TV en modo que no acepta comandos remotos
- Necesidad de emparejamiento previo

### P: ¿La aplicación se cuelga al escanear la red?
**R**: Intenta:
- Reducir el rango de escaneo (IPs 1-20 en lugar de 1-50)
- Aumentar los timeouts de conexión
- Verificar que no haya problemas de memoria

### P: ¿Cómo puedo agregar soporte para mi marca de TV?
**R**: Sigue la guía en `docs/TV_PROTOCOLS.md` para implementar un nuevo protocolo.

### P: ¿La app funciona sin internet?
**R**: Sí, solo necesita conexión a la red local WiFi donde están las TVs.

---

## 📞 Soporte Adicional

Si los problemas persisten:

1. **Habilita logging detallado** en modo debug
2. **Captura logs** durante la reproducción del problema
3. **Documenta pasos** para reproducir el issue
4. **Incluye información** del dispositivo y TV

### Información Útil para Reportes
- Modelo y marca de TV
- Versión de firmware de TV
- IP y configuración de red
- Logs de la aplicación
- Pasos para reproducir el problema

---

Esta guía cubre los problemas más comunes y sus soluciones. Para casos específicos, consulta la documentación técnica correspondiente.