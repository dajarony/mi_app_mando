# Guía de Desarrollo - Smart TV Manager

## 📋 Índice
- [Configuración del Entorno](#configuración-del-entorno)
- [Estructura del Código](#estructura-del-código)
- [Patrones y Convenciones](#patrones-y-convenciones)
- [Testing](#testing)
- [Debugging](#debugging)
- [Extensibilidad](#extensibilidad)
- [Deployment](#deployment)

## 🛠️ Configuración del Entorno

### Requisitos
- **Flutter SDK**: 3.0.0 o superior
- **Dart SDK**: 3.0.0 o superior
- **Android Studio** o **VS Code** con extensiones Flutter
- **Dispositivo Android** o **Emulador** para testing

### Instalación
```bash
# Clonar repositorio
git clone <repository-url>
cd smart_tv_manager

# Instalar dependencias
flutter pub get

# Verificar configuración
flutter doctor

# Ejecutar aplicación
flutter run
```

### Dependencias Principales
```yaml
dependencies:
  dio: ^5.3.2                    # HTTP client
  shared_preferences: ^2.2.2     # Local storage
  uuid: ^4.0.0                   # ID generation
  web_socket_channel: ^2.4.0     # WebSocket support
  logger: ^2.4.0                 # Logging

dev_dependencies:
  flutter_test: sdk: flutter
  flutter_lints: ^2.0.0
```

## 📁 Estructura del Código

### Organización de Archivos
```
lib/
├── main.dart                    # Entry point
├── router/                      # Navigation logic
├── screens/                     # UI screens
├── services/                    # Business logic
├── models/                      # Data models
├── theme/                       # UI theming
├── widgets/                     # Reusable components
└── utils/                       # Utilities (future)
```

### Convenciones de Nombres
- **Archivos**: `snake_case.dart`
- **Clases**: `PascalCase`
- **Variables/Métodos**: `camelCase`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Privados**: Prefijo `_`

## 🎯 Patrones y Convenciones

### Arquitectura de Servicios
```dart
// Singleton pattern para servicios
class NetworkService {
  static final NetworkService _instance = NetworkService._internal();
  factory NetworkService() => _instance;
  NetworkService._internal();
  
  // Métodos públicos
  Future<List<SmartTV>> scanNetwork() async { ... }
}
```

### Manejo de Estado
```dart
class _HomeScreenState extends State<HomeScreen> {
  // Estado local
  List<SmartTV> _tvs = [];
  bool _isLoading = false;
  
  // Métodos de estado
  void _updateTVs(List<SmartTV> tvs) {
    setState(() {
      _tvs = tvs;
    });
  }
}
```

### Manejo de Errores
```dart
Future<bool> performOperation() async {
  try {
    // Operación principal
    await someAsyncOperation();
    return true;
  } catch (e) {
    // Log error
    debugPrint('Error en operación: $e');
    
    // Mostrar mensaje al usuario si es necesario
    if (mounted) {
      _showErrorMessage('Error: $e');
    }
    
    return false;
  }
}
```

### Logging
```dart
// Usar debugPrint para desarrollo
debugPrint('🔍 Iniciando escaneo...');
debugPrint('✅ Operación exitosa');
debugPrint('❌ Error encontrado: $error');

// Usar emojis para categorizar logs
// 🔍 - Información
// ✅ - Éxito
// ❌ - Error
// ⚠️ - Advertencia
// 📺 - TV relacionado
// 🌐 - Red relacionado
```

## 🧪 Testing

### Estructura de Tests
```
test/
├── unit/
│   ├── services/
│   ├── models/
│   └── utils/
├── widget/
│   ├── screens/
│   └── widgets/
└── integration/
    └── app_test.dart
```

### Test de Servicios
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mi_app_expriment2/services/network_service.dart';

void main() {
  group('NetworkService Tests', () {
    late NetworkService networkService;
    
    setUp(() {
      networkService = NetworkService();
    });
    
    test('should scan network successfully', () async {
      // Arrange
      // Act
      final result = await networkService.scanNetworkForTVs();
      
      // Assert
      expect(result, isA<List<SmartTV>>());
    });
  });
}
```

### Test de Widgets
```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mi_app_expriment2/screens/home_screen.dart';

void main() {
  testWidgets('HomeScreen should display correctly', (WidgetTester tester) async {
    // Build widget
    await tester.pumpWidget(
      MaterialApp(home: HomeScreen()),
    );
    
    // Verify elements
    expect(find.text('Smart TV Manager'), findsOneWidget);
    expect(find.byType(FloatingActionButton), findsOneWidget);
  });
}
```

## 🐛 Debugging

### Herramientas de Debug
```dart
// Flutter Inspector
// - Usar para inspeccionar widget tree
// - Verificar propiedades y estado

// Debug Console
debugPrint('Estado actual: $_currentState');

// Breakpoints
// - Colocar en puntos críticos
// - Inspeccionar variables

// Hot Reload
// - Usar 'r' para hot reload
// - Usar 'R' para hot restart
```

### Debug de Red
```dart
// Interceptor para Dio
_dio.interceptors.add(
  LogInterceptor(
    requestBody: true,
    responseBody: true,
    logPrint: (obj) => debugPrint(obj.toString()),
  ),
);

// Debug de WebSocket
channel.stream.listen(
  (data) => debugPrint('📨 WebSocket recibido: $data'),
  onError: (error) => debugPrint('❌ WebSocket error: $error'),
);
```

### Problemas Comunes

#### TV No Encontrada
```dart
// Verificar conectividad
final isReachable = await _pingHost(tvIP);
if (!isReachable) {
  debugPrint('❌ Host no alcanzable: $tvIP');
}

// Verificar puerto
final isPortOpen = await _checkPort(tvIP, port);
if (!isPortOpen) {
  debugPrint('❌ Puerto cerrado: $tvIP:$port');
}
```

#### Timeout de Conexión
```dart
// Ajustar timeouts
final dio = Dio(BaseOptions(
  connectTimeout: Duration(seconds: 10), // Aumentar si es necesario
  receiveTimeout: Duration(seconds: 10),
));
```

## 🔧 Extensibilidad

### Agregar Nueva Marca de TV

#### 1. Actualizar Enum
```dart
// En models/smart_tv.dart
enum TVBrand {
  samsung, lg, sony, philips, tcl, hisense, xiaomi, roku, androidtv,
  newBrand, // Agregar aquí
  unknown
}
```

#### 2. Implementar Detección
```dart
// En RealNetworkService
Future<SmartTV?> _testNewBrandConnection(String ip, int port) async {
  try {
    final response = await _dio.get('http://$ip:$port/api/info');
    
    if (response.statusCode == 200) {
      return SmartTV(
        name: 'New Brand TV',
        brand: TVBrand.newBrand,
        ip: ip,
        port: port,
        protocol: TVProtocol.http,
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
// En TVRemoteService
Future<bool> _sendNewBrandCommand(SmartTV tv, String command) async {
  try {
    final response = await _dio.post(
      'http://${tv.ip}:${tv.port}/api/remote',
      data: {'command': command},
    );
    return response.statusCode == 200;
  } catch (e) {
    return false;
  }
}
```

### Agregar Nueva Pantalla

#### 1. Crear Screen
```dart
// En screens/new_screen.dart
class NewScreen extends StatefulWidget {
  const NewScreen({super.key});
  
  @override
  State<NewScreen> createState() => _NewScreenState();
}

class _NewScreenState extends State<NewScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Nueva Pantalla')),
      body: Container(
        // Implementar UI
      ),
    );
  }
}
```

#### 2. Agregar Ruta
```dart
// En router/app_routes.dart
class AppRoutes {
  static const String newScreen = '/new_screen';
  
  static Map<String, WidgetBuilder> getRoutes() {
    return {
      home: (context) => const HomeScreen(),
      remoteControl: (context) => const RemoteControlScreen(),
      settings: (context) => const SettingsScreen(),
      newScreen: (context) => const NewScreen(), // Agregar aquí
    };
  }
}
```

#### 3. Implementar Navegación
```dart
// Desde cualquier pantalla
Navigator.pushNamed(context, AppRoutes.newScreen);
```

### Agregar Nuevo Servicio

#### 1. Crear Servicio
```dart
// En services/new_service.dart
class NewService {
  static final NewService _instance = NewService._internal();
  factory NewService() => _instance;
  NewService._internal();
  
  Future<void> performAction() async {
    // Implementar funcionalidad
  }
}
```

#### 2. Integrar en Screen
```dart
class _ScreenState extends State<Screen> {
  final NewService _newService = NewService();
  
  void _useNewService() async {
    await _newService.performAction();
  }
}
```

## 🚀 Deployment

### Build para Android
```bash
# Debug build
flutter build apk --debug

# Release build
flutter build apk --release

# Bundle para Play Store
flutter build appbundle --release
```

### Configuración de Release
```dart
// En android/app/build.gradle
android {
    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword keystoreProperties['storePassword']
        }
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            useProguard true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}
```

### Optimizaciones
```dart
// Reducir tamaño del APK
flutter build apk --split-per-abi

// Analizar tamaño
flutter build apk --analyze-size

// Ofuscar código
flutter build apk --obfuscate --split-debug-info=/<project-name>/<directory>
```

## 📝 Mejores Prácticas

### Código Limpio
- **Funciones pequeñas**: Máximo 20-30 líneas
- **Nombres descriptivos**: Variables y métodos claros
- **Comentarios útiles**: Explicar el "por qué", no el "qué"
- **Evitar duplicación**: DRY (Don't Repeat Yourself)

### Performance
- **Lazy loading**: Cargar datos cuando se necesiten
- **Dispose resources**: Cerrar streams, controllers, etc.
- **Optimize builds**: Usar const constructors cuando sea posible
- **Image optimization**: Usar formatos apropiados y tamaños

### Seguridad
- **Validar inputs**: Siempre validar datos de usuario
- **Sanitizar URLs**: Verificar IPs y puertos
- **Handle secrets**: No hardcodear credenciales
- **Network security**: Usar HTTPS cuando sea posible

### UX/UI
- **Loading states**: Mostrar indicadores de carga
- **Error handling**: Mensajes de error claros
- **Responsive design**: Adaptar a diferentes tamaños
- **Accessibility**: Soporte para lectores de pantalla

---

## 🔄 Workflow de Desarrollo

### 1. Feature Development
```bash
# Crear branch
git checkout -b feature/nueva-funcionalidad

# Desarrollar
# - Escribir código
# - Agregar tests
# - Documentar cambios

# Commit
git add .
git commit -m "feat: agregar nueva funcionalidad"

# Push y PR
git push origin feature/nueva-funcionalidad
```

### 2. Code Review
- **Revisar funcionalidad**
- **Verificar tests**
- **Comprobar documentación**
- **Validar performance**

### 3. Testing
```bash
# Unit tests
flutter test

# Widget tests
flutter test test/widget/

# Integration tests
flutter drive --target=test_driver/app.dart
```

### 4. Release
```bash
# Actualizar versión en pubspec.yaml
version: 1.1.0+2

# Build release
flutter build apk --release

# Tag release
git tag v1.1.0
git push origin v1.1.0
```

---

Esta guía proporciona todo lo necesario para desarrollar y mantener Smart TV Manager de manera efectiva.