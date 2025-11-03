# 🔧 Comandos Útiles - Smart TV Manager

## ⚡ Comandos Rápidos

### **Empezar a Desarrollar**
```bash
# 1. Instalar dependencias
flutter pub get

# 2. Ejecutar app
flutter run

# 3. Ejecutar en dispositivo específico
flutter run -d chrome        # Web
flutter run -d windows       # Windows
flutter run -d android       # Android
```

---

## 🧪 Testing

### **Ejecutar Tests**
```bash
# Todos los tests
flutter test

# Test específico
flutter test test/services/network_service_test.dart

# Con cobertura
flutter test --coverage

# Ver cobertura en HTML
genhtml coverage/lcov.info -o coverage/html
```

### **Tests en Watch Mode**
```bash
# Ejecutar tests automáticamente al guardar
flutter test --watch
```

---

## 🔍 Análisis de Código

### **Análisis Completo**
```bash
# Analizar todo el proyecto
flutter analyze

# Análisis sin dependencias
flutter analyze --no-pub

# Solo errores
flutter analyze --no-pub | grep "error"

# Contar issues
flutter analyze --no-pub | tail -1
```

### **Formateo de Código**
```bash
# Formatear todo el proyecto
flutter format .

# Formatear archivo específico
flutter format lib/main.dart

# Ver cambios sin aplicar
flutter format --dry-run .
```

---

## 📦 Gestión de Dependencias

### **Dependencias**
```bash
# Instalar dependencias
flutter pub get

# Actualizar dependencias
flutter pub upgrade

# Ver dependencias desactualizadas
flutter pub outdated

# Añadir dependencia
flutter pub add provider

# Añadir dependencia de desarrollo
flutter pub add --dev flutter_test
```

### **Caché**
```bash
# Limpiar caché
flutter clean

# Limpiar y reinstalar
flutter clean && flutter pub get
```

---

## 🏗️ Build y Deployment

### **Debug Build**
```bash
# Android APK
flutter build apk --debug

# iOS
flutter build ios --debug

# Windows
flutter build windows --debug
```

### **Release Build**
```bash
# Android APK
flutter build apk --release

# Android App Bundle (para Play Store)
flutter build appbundle --release

# iOS
flutter build ios --release

# Windows
flutter build windows --release

# Web
flutter build web --release
```

---

## 🚀 Ejecución

### **Ejecutar en Diferentes Plataformas**
```bash
# Listar dispositivos disponibles
flutter devices

# Ejecutar en dispositivo específico
flutter run -d <device-id>

# Ejecutar en todos los dispositivos
flutter run -d all

# Modo release
flutter run --release

# Modo profile (para performance)
flutter run --profile
```

### **Hot Reload y Restart**
```bash
# Durante ejecución:
r   # Hot reload
R   # Hot restart
q   # Quit
```

---

## 🐛 Debugging

### **Logs y Debug**
```bash
# Ver logs
flutter logs

# Limpiar logs
flutter logs --clear

# Attach debugger a app en ejecución
flutter attach

# Doctor (verificar instalación)
flutter doctor

# Doctor detallado
flutter doctor -v
```

### **Performance**
```bash
# Profile mode
flutter run --profile

# Trace
flutter run --trace-startup

# Observatory
flutter run --observatory-port=8888
```

---

## 📱 Dispositivos

### **Emuladores**
```bash
# Listar emuladores
flutter emulators

# Crear emulador
flutter emulators --create

# Lanzar emulador
flutter emulators --launch <emulator-id>
```

### **Dispositivos Físicos**
```bash
# Listar dispositivos conectados
flutter devices

# Habilitar modo wireless (Android)
adb tcpip 5555
adb connect <device-ip>:5555
```

---

## 🔧 Mantenimiento

### **Actualizar Flutter**
```bash
# Actualizar Flutter SDK
flutter upgrade

# Cambiar canal
flutter channel stable
flutter channel beta

# Verificar versión
flutter --version
```

### **Limpiar Proyecto**
```bash
# Limpiar build
flutter clean

# Limpiar y reinstalar
flutter clean && flutter pub get

# Limpiar caché de pub
flutter pub cache clean
```

---

## 📊 Información del Proyecto

### **Info General**
```bash
# Versión de Flutter
flutter --version

# Info del proyecto
flutter pub deps

# Árbol de dependencias
flutter pub deps --style=compact

# Listar packages
flutter packages get
```

---

## 🎨 Generación de Código

### **Assets y Configuración**
```bash
# Generar iconos de app
flutter pub run flutter_launcher_icons:main

# Generar splash screen
flutter pub run flutter_native_splash:create

# Build runner (si usas generación de código)
flutter pub run build_runner build
flutter pub run build_runner watch
```

---

## 📝 Utilidades Específicas del Proyecto

### **Ejecutar Servicios**
```bash
# Test de red
flutter test test/services/network_service_test.dart

# Test de historial
flutter test test/services/command_history_service_test.dart

# Test de provider
flutter test test/providers/tv_provider_test.dart
```

### **Verificar Arquitectura**
```bash
# Analizar servicios
flutter analyze lib/services/

# Analizar widgets
flutter analyze lib/widgets/

# Analizar modelos
flutter analyze lib/models/
```

---

## 🆘 Solución de Problemas

### **Problemas Comunes**
```bash
# Error de Gradle (Android)
cd android && ./gradlew clean
cd .. && flutter clean && flutter pub get

# Error de Pods (iOS)
cd ios && pod deintegrate && pod install
cd .. && flutter clean && flutter pub get

# Error de dependencias
flutter pub cache repair
flutter clean
flutter pub get

# Error de build
flutter clean
flutter pub get
flutter run
```

### **Reset Completo**
```bash
# Reset total del proyecto
flutter clean
rm -rf .dart_tool
rm -rf build
rm pubspec.lock
flutter pub get
```

---

## 📚 Recursos

### **Documentación**
```bash
# Abrir docs de Flutter
flutter docs

# Abrir API docs
flutter pub global activate dhttpd
dhttpd --path doc/api
```

### **Este Proyecto**
```bash
# Ver mejoras
cat MEJORAS_2024.md

# Ver resumen
cat RESUMEN_FINAL.md

# Ver estado actual
cat ESTADO_ACTUAL.md

# Inicio rápido
cat INICIO_RAPIDO.md
```

---

## ⚡ One-Liners Útiles

```bash
# Limpiar, instalar y ejecutar
flutter clean && flutter pub get && flutter run

# Test con cobertura
flutter test --coverage && genhtml coverage/lcov.info -o coverage/html

# Build para todas las plataformas
flutter build apk && flutter build web && flutter build windows

# Ver solo errores
flutter analyze --no-pub | grep "error"

# Contar warnings
flutter analyze --no-pub | grep "info" | wc -l

# Ejecutar en Chrome
flutter run -d chrome --web-port=8080

# Build optimizado para web
flutter build web --release --web-renderer html
```

---

## 🎯 Comandos para Producción

### **Pre-Deploy Checklist**
```bash
# 1. Limpiar
flutter clean

# 2. Actualizar dependencias
flutter pub upgrade

# 3. Ejecutar tests
flutter test

# 4. Analizar código
flutter analyze

# 5. Build de release
flutter build apk --release    # Android
flutter build ios --release    # iOS
flutter build web --release    # Web
```

### **Deploy**
```bash
# Android - Subir a Play Store
flutter build appbundle --release

# iOS - Subir a App Store
flutter build ios --release
open ios/Runner.xcworkspace

# Web - Deploy a hosting
flutter build web --release
# Subir carpeta build/web/ a tu hosting
```

---

## 💡 Tips

### **Desarrollo más Rápido**
```bash
# Hot reload automático
flutter run

# Profile para performance
flutter run --profile

# Verbose output
flutter run -v
```

### **Debugging**
```bash
# DevTools
flutter pub global activate devtools
flutter pub global run devtools

# Attach a proceso
flutter attach
```

---

**¡Guarda este archivo para referencia rápida! 🚀**

