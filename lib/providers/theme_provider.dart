import 'package:flutter/material.dart';
import 'package:logger/logger.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_theme.dart';

enum AppThemeType {
  dark,
  light,
  oceanBlue,
  forestGreen,
  sakuraPink,
  royalPurple,
}

class ThemeProvider extends ChangeNotifier {
  final _logger = Logger();
  AppThemeType _currentTheme = AppThemeType.dark;
  static const String _themePreferenceKey = 'selected_theme';

  AppThemeType get currentTheme => _currentTheme;

  ThemeData get themeData {
    switch (_currentTheme) {
      case AppThemeType.dark:
        return AppTheme.darkTheme;
      case AppThemeType.light:
        return AppTheme.lightTheme;
      case AppThemeType.oceanBlue:
        return AppTheme.oceanBlueTheme;
      case AppThemeType.forestGreen:
        return AppTheme.forestGreenTheme;
      case AppThemeType.sakuraPink:
        return AppTheme.sakuraPinkTheme;
      case AppThemeType.royalPurple:
        return AppTheme.royalPurpleTheme;
    }
  }

  String get themeName {
    switch (_currentTheme) {
      case AppThemeType.dark:
        return 'Dark';
      case AppThemeType.light:
        return 'Light';
      case AppThemeType.oceanBlue:
        return 'Ocean Blue';
      case AppThemeType.forestGreen:
        return 'Forest Green';
      case AppThemeType.sakuraPink:
        return 'Sakura Pink';
      case AppThemeType.royalPurple:
        return 'Royal Purple';
    }
  }

  String get themeIcon {
    switch (_currentTheme) {
      case AppThemeType.dark:
        return '🌙';
      case AppThemeType.light:
        return '☀️';
      case AppThemeType.oceanBlue:
        return '🌊';
      case AppThemeType.forestGreen:
        return '🌲';
      case AppThemeType.sakuraPink:
        return '🌸';
      case AppThemeType.royalPurple:
        return '👑';
    }
  }

  // Inicializar y cargar tema guardado
  Future<void> initialize() async {
    await _loadThemePreference();
  }

  // Cambiar tema
  Future<void> setTheme(AppThemeType theme) async {
    _currentTheme = theme;
    await _saveThemePreference();
    notifyListeners();
  }

  // Cargar preferencia de tema
  Future<void> _loadThemePreference() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final themeIndex = prefs.getInt(_themePreferenceKey);

      if (themeIndex != null && themeIndex < AppThemeType.values.length) {
        _currentTheme = AppThemeType.values[themeIndex];
        notifyListeners();
      }
    } catch (e, s) {
      // Si hay error, mantener tema por defecto (dark)
      _logger.e('Error loading theme preference', error: e, stackTrace: s);
    }
  }

  // Guardar preferencia de tema
  Future<void> _saveThemePreference() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_themePreferenceKey, _currentTheme.index);
    } catch (e, s) {
      _logger.e('Error saving theme preference', error: e, stackTrace: s);
    }
  }

  // Obtener todos los temas disponibles
  static List<ThemePreviewData> getAllThemes() {
    return [
      ThemePreviewData(
        type: AppThemeType.dark,
        name: 'Dark',
        icon: '🌙',
        description: 'Elegante tema oscuro',
        primaryColor: AppTheme.accentBlue,
        backgroundColor: Colors.black,
      ),
      ThemePreviewData(
        type: AppThemeType.light,
        name: 'Light',
        icon: '☀️',
        description: 'Clásico tema claro',
        primaryColor: AppTheme.accentBlue,
        backgroundColor: AppTheme.backgroundPrimary,
      ),
      ThemePreviewData(
        type: AppThemeType.oceanBlue,
        name: 'Ocean Blue',
        icon: '🌊',
        description: 'Profundo azul océano',
        primaryColor: const Color(0xFF0077BE),
        backgroundColor: const Color(0xFFE3F2FD),
      ),
      ThemePreviewData(
        type: AppThemeType.forestGreen,
        name: 'Forest Green',
        icon: '🌲',
        description: 'Verde natural y relajante',
        primaryColor: const Color(0xFF2E7D32),
        backgroundColor: const Color(0xFFE8F5E9),
      ),
      ThemePreviewData(
        type: AppThemeType.sakuraPink,
        name: 'Sakura Pink',
        icon: '🌸',
        description: 'Rosa suave y delicado',
        primaryColor: const Color(0xFFE91E63),
        backgroundColor: const Color(0xFFFCE4EC),
      ),
      ThemePreviewData(
        type: AppThemeType.royalPurple,
        name: 'Royal Purple',
        icon: '👑',
        description: 'Morado elegante y premium',
        primaryColor: const Color(0xFF6A1B9A),
        backgroundColor: const Color(0xFFF3E5F5),
      ),
    ];
  }
}

// Clase para datos de preview de temas
class ThemePreviewData {
  final AppThemeType type;
  final String name;
  final String icon;
  final String description;
  final Color primaryColor;
  final Color backgroundColor;

  ThemePreviewData({
    required this.type,
    required this.name,
    required this.icon,
    required this.description,
    required this.primaryColor,
    required this.backgroundColor,
  });
}
