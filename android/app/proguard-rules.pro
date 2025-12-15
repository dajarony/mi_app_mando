# Flutter ProGuard Rules
# Mantener clases de Flutter
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Mantener clases de la app
-keep class com.dajarony.smarttvmanager.** { *; }

# Mantener clases de Kotlin
-keep class kotlin.** { *; }
-keep class kotlinx.** { *; }

# Mantener anotaciones
-keepattributes *Annotation*

# Para debugging
-keepattributes SourceFile,LineNumberTable
