# Flutter ProGuard Rules

# Mantener clases de Flutter
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }
-keep class io.flutter.app.** { *; }
-keep class io.flutter.embedding.** { *; }

# Mantener clases de la app
-keep class com.dajarony.smarttvmanager.** { *; }

# Mantener clases de Kotlin
-keep class kotlin.** { *; }
-keep class kotlinx.** { *; }

# Play Core library (requerido para deferred components)
-keep class com.google.android.play.core.** { *; }
-dontwarn com.google.android.play.core.**

# Mantener anotaciones
-keepattributes *Annotation*

# Para debugging
-keepattributes SourceFile,LineNumberTable

# Evitar warnings de clases faltantes
-dontwarn com.google.android.play.core.splitcompat.**
-dontwarn com.google.android.play.core.splitinstall.**
-dontwarn com.google.android.play.core.tasks.**
