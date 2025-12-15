import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'router/app_routes.dart';
import 'providers/tv_provider.dart';
import 'providers/theme_provider.dart';
import 'providers/settings_provider.dart';

void main() {
  // Capturar errores de Flutter
  FlutterError.onError = (FlutterErrorDetails details) {
    FlutterError.presentError(details);
    debugPrint('Flutter Error: ${details.exception}');
  };

  // Ejecutar la app en zona segura para capturar errores async
  runZonedGuarded(
    () {
      WidgetsFlutterBinding.ensureInitialized();
      runApp(const MyApp());
    },
    (error, stackTrace) {
      debugPrint('Uncaught error: $error');
      debugPrint('Stack trace: $stackTrace');
    },
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (context) => TVProvider()..initialize(),
        ),
        ChangeNotifierProvider(
          create: (context) => ThemeProvider()..initialize(),
        ),
        ChangeNotifierProvider(
          create: (context) => SettingsProvider()..initialize(),
        ),
      ],
      child: Consumer<ThemeProvider>(
        builder: (context, themeProvider, child) {
          return MaterialApp(
            title: 'Smart TV Manager',
            debugShowCheckedModeBanner: false,
            theme: themeProvider.themeData,
            routes: AppRoutes.getRoutes(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          );
        },
      ),
    );
  }
}
