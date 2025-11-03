# Arquitectura de Smart TV Manager

## 📋 Índice
- [Visión General](#visión-general)
- [Estructura de Carpetas](#estructura-de-carpetas)
- [Componentes Principales](#componentes-principales)
- [Flujo de Datos](#flujo-de-datos)
- [Servicios](#servicios)
- [Modelos](#modelos)
- [UI/UX](#uiux)

## 🏗️ Visión General

Smart TV Manager sigue una arquitectura modular con separación clara de responsabilidades:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Presentation  │    │    Business     │    │      Data       │
│     Layer       │◄──►│     Logic       │◄──►│     Layer       │
│                 │    │     Layer       │    │                 │
│ - Screens       │    │ - Services      │    │ - Storage       │
│ - Widgets       │    │ - Controllers   │    │ - Network       │
│ - Themes        │    │ - Validators    │    │ - Models        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Estructura de Carpetas

```
lib/
├── main.dart                           # Entry point
├── router/                            # Navigation
│   └── app_routes.dart               # Route definitions
├── screens/                          # UI Screens
│   ├── home_screen.dart             # Main dashboard
│   └── remote_control_screen.dart   # TV remote control
├── services/                         # Business logic
│   ├── network_service.dart         # Network operations
│   ├── tv_remote_service.dart       # TV communication
│   ├── tv_storage_service.dart      # Local storage
│   └── philips_tv_direct_service.dart # Philips specific
├── models/                           # Data models
│   └── smart_tv.dart               # TV data structure
├── theme/                           # UI theming
│   └── app_theme.dart              # Neumorphic theme
└── widgets/                         # Reusable components
    ├── bottom_nav_item.dart        # Navigation items
    └── neumorphic_nav_bar.dart     # Custom nav bar
```

## 🧩 Componentes Principales

### 1. Main Application (`main.dart`)
```dart
MyApp
├── MaterialApp
├── Theme Configuration
├── Route Management
└── Initial Screen (HomeScreen)
```

### 2. Navigation (`router/app_routes.dart`)
```dart
AppRoutes
├── Static route definitions
├── Route builders
├── Navigation guards
└── Route generation
```

### 3. Screens
#### HomeScreen
- **Responsabilidad**: Dashboard principal, gestión de TVs
- **Estado**: Lista de TVs, TV seleccionada, estados de carga
- **Servicios**: NetworkService, StorageService, RemoteService

#### RemoteControlScreen
- **Responsabilidad**: Control remoto funcional
- **Estado**: Modo de entrada (D-pad/números), estados de botones
- **Servicios**: PhilipsTvDirectService

## 🔄 Flujo de Datos

### Inicialización de la App
```
main() → MyApp → MaterialApp → HomeScreen → initState()
                                    ↓
                            loadStoredTVs() → verifyTVsStatus()
```

### Escaneo de Red
```
User Action → _scanForTVs() → RealNetworkService.scanNetworkForTVs()
                                    ↓
                            Parallel IP scanning → TV validation
                                    ↓
                            Update UI state → Save to storage
```

### Control de TV
```
User selects TV → Navigate to RemoteControlScreen
                                    ↓
                    Initialize PhilipsTvDirectService with TV IP
                                    ↓
                    User presses button → sendKey() → HTTP request
```

## 🛠️ Servicios

### RealNetworkService
```dart
class RealNetworkService {
  // Singleton pattern
  static final _instance = RealNetworkService._internal();
  
  // Core methods
  Future<List<SmartTV>> scanNetworkForTVs()
  Future<bool> validateTVConnection(SmartTV tv)
  Future<bool> pairWithTV(SmartTV tv)
  
  // Private helpers
  Future<SmartTV?> _checkIPForTV(String ip)
  Future<SmartTV?> _testTVConnection(String ip, int port)
}
```

### TVRemoteService
```dart
class TVRemoteService {
  // Multi-brand support
  Future<bool> sendCommand(SmartTV tv, String command)
  
  // Brand-specific implementations
  Future<bool> _sendSamsungCommand(SmartTV tv, String command)
  Future<bool> _sendLGCommand(SmartTV tv, String command)
  Future<bool> _sendSonyCommand(SmartTV tv, String command)
  Future<bool> _sendRokuCommand(SmartTV tv, String command)
}
```

### PhilipsTvDirectService
```dart
class PhilipsTvDirectService {
  // Direct HTTP communication
  Future<void> sendKey(String key)
  Future<void> setVolume(double volume)
  Future<void> openApp(String appName)
}
```

### TVStorageService
```dart
class TVStorageService {
  // Persistent storage
  static Future<List<SmartTV>> loadTVs()
  static Future<void> saveTVs(List<SmartTV> tvs)
  static Future<String?> getSelectedTVId()
  static Future<void> setSelectedTVId(String tvId)
}
```

## 📊 Modelos

### SmartTV Model
```dart
class SmartTV {
  // Core properties
  final String id;
  final String name;
  final TVBrand brand;
  final String ip;
  final int port;
  
  // State properties
  bool isOnline;
  bool isRegistered;
  bool isPaired;
  
  // Methods
  SmartTV copyWith({...})
  Map<String, dynamic> toJson()
  factory SmartTV.fromJson(Map<String, dynamic> json)
}
```

### Enums
```dart
enum TVBrand {
  samsung, lg, sony, philips, tcl, 
  hisense, xiaomi, roku, androidtv, unknown
}

enum TVProtocol {
  http, websocket, upnp, roku, unknown
}
```

## 🎨 UI/UX

### Theme System
```dart
class AppTheme {
  // Color palette
  static const Color backgroundPrimary = Color(0xFFE8E8E8);
  static const Color backgroundSecondary = Color(0xFFF5F5F5);
  static const Color textPrimary = Color(0xFF2D3748);
  
  // Neumorphic decorations
  static BoxDecoration concaveDecoration({...})
  static BoxDecoration convexDecoration({...})
}
```

### Widget Hierarchy
```
Scaffold
├── AppBar (with navigation buttons)
├── Body
│   ├── Loading indicator (conditional)
│   ├── TV List (GridView)
│   ├── Selected TV info
│   ├── Quick controls
│   └── Registration form (conditional)
└── FloatingActionButton (scan)
```

## 🔌 Comunicación de Red

### Protocolos por Marca
```
Samsung  → WebSocket (puerto 8001/8080)
LG       → WebSocket (puerto 3000)
Sony     → HTTP POST (puerto 80/8080)
Philips  → HTTP POST (puerto 1925)
Roku     → HTTP POST (puerto 8060)
```

### Estructura de Comandos
```dart
// Samsung
{
  "method": "ms.remote.control",
  "params": {
    "Cmd": "Click",
    "DataOfCmd": "KEY_POWER",
    "Option": "false",
    "TypeOfRemote": "SendRemoteKey"
  }
}

// Philips
{
  "key": "Standby"
}
```

## 🔄 Estado de la Aplicación

### HomeScreen State
```dart
class _HomeScreenState {
  List<SmartTV> _registeredTVs = [];
  SmartTV? _selectedTV;
  bool _isScanning = false;
  bool _isLoading = false;
  bool _isRegistering = false;
}
```

### RemoteControlScreen State
```dart
class _RemoteControlScreenState {
  bool _showNumberPad = false;
  PhilipsTvDirectService _apiService;
}
```

## 🚀 Patrones de Diseño Utilizados

1. **Singleton**: NetworkService, RemoteService
2. **Factory**: SmartTV.fromJson()
3. **Builder**: Neumorphic button builder
4. **Observer**: StatefulWidget para cambios de estado
5. **Strategy**: Diferentes implementaciones por marca de TV

## 🔧 Configuración y Extensibilidad

### Agregar Nueva Marca de TV
1. Añadir enum en `TVBrand`
2. Implementar método en `TVRemoteService`
3. Agregar detección en `RealNetworkService`
4. Definir protocolo en `TVProtocol`

### Agregar Nueva Pantalla
1. Crear archivo en `screens/`
2. Añadir ruta en `app_routes.dart`
3. Implementar navegación
4. Aplicar tema consistente

---

Esta arquitectura permite escalabilidad, mantenibilidad y testing efectivo del código.