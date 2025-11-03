# CLAUDE.md - Smart TV Manager

## Descripción del Proyecto
Smart TV Manager es una aplicación Flutter para controlar Smart TVs de diferentes marcas con interfaz neumórfica moderna.

## Comandos Principales

### Desarrollo
```bash
# Instalar dependencias
flutter pub get

# Ejecutar aplicación
flutter run

# Ejecutar en plataforma específica
flutter run -d chrome        # Web
flutter run -d windows       # Windows
flutter run -d android       # Android

# Hot reload durante desarrollo
r   # Hot reload
R   # Hot restart
q   # Salir
```

### Testing
```bash
# Ejecutar todos los tests
flutter test

# Test específico
flutter test test/services/network_service_test.dart

# Con cobertura
flutter test --coverage
```

### Análisis y Calidad
```bash
# Analizar código
flutter analyze

# Formatear código
flutter format .

# Ver cambios de formato sin aplicar
flutter format --dry-run .
```

### Build y Deploy
```bash
# Limpiar proyecto
flutter clean

# Build debug
flutter build apk --debug

# Build release
flutter build apk --release       # Android
flutter build windows --release   # Windows
flutter build web --release       # Web
```

## Estructura del Proyecto

```
lib/
├── main.dart                       # Punto de entrada
├── router/
│   └── app_routes.dart            # Configuración de rutas
├── screens/
│   ├── home_screen.dart           # Pantalla principal
│   └── remote_control_screen.dart # Control remoto
├── services/
│   ├── network_service.dart       # Escaneo de red
│   ├── tv_remote_service.dart     # Control de TV
│   ├── tv_storage_service.dart    # Almacenamiento
│   └── philips_tv_direct_service.dart
├── models/
│   └── tv_device.dart             # Modelo de TV
├── providers/
│   └── tv_provider.dart           # Estado global
├── widgets/
│   └── [componentes reutilizables]
└── theme/
    └── app_theme.dart             # Tema neumórfico
```

## Stack Tecnológico

### Dependencias Principales
- **dio**: ^5.3.2 - Cliente HTTP para APIs de TVs
- **shared_preferences**: ^2.2.2 - Almacenamiento local
- **provider**: ^6.1.2 - Gestión de estado
- **web_socket_channel**: ^2.4.0 - WebSocket para Samsung/LG
- **uuid**: ^4.0.0 - Generación de IDs únicos
- **http**: ^1.1.0 - Cliente HTTP adicional
- **logger**: ^2.4.0 - Logging

### Plataformas Soportadas
- Android
- Windows
- Web (Chrome recomendado)

## Estilo de Código

### Convenciones
- **Indentación**: 2 espacios
- **Nombres de archivos**: snake_case (ej: `tv_provider.dart`)
- **Nombres de clases**: PascalCase (ej: `TVProvider`)
- **Nombres de variables/métodos**: camelCase (ej: `scanNetwork`)
- **Constantes**: lowerCamelCase con const (ej: `const maxRetries = 3`)

### Buenas Prácticas
- Usar widgets const cuando sea posible para optimización
- Documentar funciones complejas con comentarios
- Usar try/catch para operaciones asíncronas
- Separar lógica de negocio en servicios
- Usar Provider para gestión de estado
- Mantener widgets pequeños y reutilizables

### Arquitectura
- **Servicios**: Lógica de negocio y comunicación con APIs
- **Providers**: Gestión de estado global
- **Widgets**: Componentes UI reutilizables
- **Screens**: Pantallas completas de la app
- **Models**: Modelos de datos

## Características Principales

### Funcionalidades
- ✅ Control remoto universal para múltiples marcas
- ✅ Escaneo automático de TVs en red local
- ✅ Registro manual de dispositivos
- ✅ Interfaz neumórfica moderna
- ✅ Control directo vía HTTP/WebSocket
- ✅ Almacenamiento local de configuraciones
- ✅ Soporte multi-marca: Samsung, LG, Sony, Philips, Roku

### Pantallas
1. **HomeScreen** (`/`) - Gestión de TVs y escaneo
2. **RemoteControlScreen** (`/remote_control`) - Control remoto funcional
3. **SettingsScreen** (`/settings`) - Configuraciones

## Documentación Adicional

- `README.md` - Descripción general y características
- `COMANDOS_UTILES.md` - Guía completa de comandos
- `ESTADO_ACTUAL.md` - Estado actual del desarrollo
- `INICIO_RAPIDO.md` - Guía de inicio rápido
- `MEJORAS_2024.md` - Mejoras planificadas
- `CHANGELOG.md` - Historial de cambios

## Solución de Problemas

### Errores Comunes

**Error de dependencias:**
```bash
flutter clean
flutter pub get
```

**Error de Gradle (Android):**
```bash
cd android && ./gradlew clean
cd .. && flutter clean && flutter pub get
```

**Reset completo:**
```bash
flutter clean
rm -rf .dart_tool
rm -rf build
rm pubspec.lock
flutter pub get
```

## Workflow de Desarrollo

### Antes de Empezar a Codificar
1. `flutter pub get` - Asegurar dependencias actualizadas
2. `flutter analyze` - Verificar que no hay errores existentes
3. Revisar documentación relevante en los archivos .md

### Durante el Desarrollo
1. Usar hot reload (`r`) para cambios rápidos
2. Ejecutar `flutter analyze` periódicamente
3. Mantener código formateado con `flutter format .`
4. Escribir tests para nueva funcionalidad

### Antes de Commit
1. `flutter analyze` - Sin errores
2. `flutter test` - Todos los tests pasando
3. `flutter format .` - Código formateado
4. Actualizar CHANGELOG.md si es necesario

## Notas Importantes

- ⚠️ El escaneo de red requiere permisos de red local
- ⚠️ Algunas marcas de TV requieren activar control remoto en configuración
- ⚠️ WebSocket solo funciona con Samsung y LG TVs
- ⚠️ La app debe estar en la misma red WiFi que las TVs

## Recursos

- [Flutter Docs](https://flutter.dev/docs)
- [Provider Package](https://pub.dev/packages/provider)
- [Dio HTTP Client](https://pub.dev/packages/dio)
- Documentación interna: Ver archivos .md en la raíz del proyecto
