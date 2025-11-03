#!/usr/bin/env python3
# Script temporal para añadir temas completos

# Leer el archivo actual
with open('lib/theme/app_theme.dart', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar la última línea (})
last_line_index = -1
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == '}':
        last_line_index = i
        break

# Temas completos para insertar
new_themes = '''
  // 🌊 Ocean Blue Theme - COMPLETO
  static final ThemeData oceanBlueTheme = _createCompleteTheme(
    primaryColor: const Color(0xFF0077BE),
    secondaryColor: const Color(0xFF00BCD4),
    surfaceColor: const Color(0xFFE3F2FD),
    onSurfaceColor: const Color(0xFF01579B),
    scaffoldBgColor: const Color(0xFFE3F2FD),
    cardColor: const Color(0xFFFFFFFF),
    inputBorderColor: const Color(0xFFB3E5FC),
  );

  // 🌲 Forest Green Theme - COMPLETO
  static final ThemeData forestGreenTheme = _createCompleteTheme(
    primaryColor: const Color(0xFF2E7D32),
    secondaryColor: const Color(0xFF66BB6A),
    surfaceColor: const Color(0xFFE8F5E9),
    onSurfaceColor: const Color(0xFF1B5E20),
    scaffoldBgColor: const Color(0xFFE8F5E9),
    cardColor: const Color(0xFFFFFFFF),
    inputBorderColor: const Color(0xFFC8E6C9),
  );

  // 🌸 Sakura Pink Theme - COMPLETO
  static final ThemeData sakuraPinkTheme = _createCompleteTheme(
    primaryColor: const Color(0xFFE91E63),
    secondaryColor: const Color(0xFFF48FB1),
    surfaceColor: const Color(0xFFFCE4EC),
    onSurfaceColor: const Color(0xFF880E4F),
    scaffoldBgColor: const Color(0xFFFCE4EC),
    cardColor: const Color(0xFFFFFFFF),
    inputBorderColor: const Color(0xFFF8BBD0),
  );

  // 👑 Royal Purple Theme - COMPLETO
  static final ThemeData royalPurpleTheme = _createCompleteTheme(
    primaryColor: const Color(0xFF6A1B9A),
    secondaryColor: const Color(0xFFBA68C8),
    surfaceColor: const Color(0xFFF3E5F5),
    onSurfaceColor: const Color(0xFF4A148C),
    scaffoldBgColor: const Color(0xFFF3E5F5),
    cardColor: const Color(0xFFFFFFFF),
    inputBorderColor: const Color(0xFFE1BEE7),
  );

  // Helper method para crear temas completos
  static ThemeData _createCompleteTheme({
    required Color primaryColor,
    required Color secondaryColor,
    required Color surfaceColor,
    required Color onSurfaceColor,
    required Color scaffoldBgColor,
    required Color cardColor,
    required Color inputBorderColor,
  }) {
    return ThemeData.light().copyWith(
      primaryColor: primaryColor,
      colorScheme: ColorScheme.light(
        primary: primaryColor,
        secondary: secondaryColor,
        surface: surfaceColor,
        onSurface: onSurfaceColor,
        error: alertRed,
        onError: neutralWhite,
      ),
      scaffoldBackgroundColor: scaffoldBgColor,
      appBarTheme: AppBarTheme(
        color: scaffoldBgColor,
        elevation: 0,
        titleTextStyle: TextStyle(
          color: onSurfaceColor,
          fontSize: 1.4 * 16,
          fontWeight: FontWeight.w600,
        ),
        iconTheme: IconThemeData(color: primaryColor),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: primaryColor,
          textStyle: const TextStyle(
            fontWeight: FontWeight.w500,
            fontSize: 1.0 * 16,
          ),
        ),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: primaryColor,
        elevation: 5,
        foregroundColor: neutralWhite,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryColor,
          foregroundColor: neutralWhite,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(1.2 * 16),
          ),
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 2.0 * 16, vertical: 0.9 * 16),
          textStyle: const TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 1.0 * 16,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        floatingLabelStyle: TextStyle(color: primaryColor),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide(color: inputBorderColor, width: 1.5),
          borderRadius: BorderRadius.circular(1.1 * 16),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: BorderSide(color: primaryColor, width: 1.5),
          borderRadius: BorderRadius.circular(1.1 * 16),
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(1.1 * 16),
        ),
        fillColor: neutralWhite,
        filled: true,
        contentPadding: const EdgeInsets.symmetric(horizontal: 1.2 * 16, vertical: 0.8 * 16),
        hintStyle: TextStyle(color: onSurfaceColor.withAlpha((0.7 * 255).round())),
        labelStyle: TextStyle(color: onSurfaceColor),
      ),
      cardTheme: CardTheme(
        color: cardColor,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(2.0 * 16),
        ),
        margin: const EdgeInsets.only(bottom: 1.3 * 16),
        elevation: 8,
        shadowColor: primaryColor.withAlpha((0.15 * 255).round()),
      ),
      iconTheme: IconThemeData(
        size: 1.3 * 16,
        color: primaryColor,
      ),
      textTheme: TextTheme(
        displayLarge: TextStyle(
          fontSize: 2.2 * 16,
          fontWeight: FontWeight.w700,
          color: onSurfaceColor,
        ),
        titleLarge: TextStyle(
          fontSize: 1.4 * 16,
          fontWeight: FontWeight.w600,
          color: onSurfaceColor,
        ),
        titleMedium: TextStyle(
          fontSize: 1.1 * 16,
          fontWeight: FontWeight.w500,
          color: onSurfaceColor,
        ),
        bodyLarge: TextStyle(
          fontSize: 1.0 * 16,
          fontWeight: FontWeight.w400,
          color: onSurfaceColor,
        ),
        bodyMedium: TextStyle(
          fontSize: 0.87 * 16,
          fontWeight: FontWeight.w400,
          color: primaryColor,
        ),
      ),
    );
  }
'''

# Insertar antes de la última línea
lines.insert(last_line_index, new_themes)

# Escribir el archivo
with open('lib/theme/app_theme.dart', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('✅ Temas completos añadidos correctamente!')
