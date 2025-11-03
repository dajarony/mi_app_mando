import 'package:flutter/material.dart';

class AppTheme {
  // Color Palette
  static const Color backgroundPrimary = Color(0xFFF7F8FA);
  static const Color backgroundSecondary = Color(0xFFE7EAF0);
  static const Color accentBlue = Color(0xFF3B82F6);
  static const Color accentPurple = Color(0xFFA78BFA);
  static const Color neutralWhite = Color(0xFFFFFFFF);
  static const Color textPrimary = Color(0xFF161B22);
  static const Color textSecondary = Color(0xFF48506A);
  static const Color successGreen = Color(0xFFA3DE83);
  static const Color alertRed = Color(0xFFF87171);
  static const Color dividerGray = Color(0xFFE5E7EB);

  // Aliases required por componentes neumorficos existentes
  static const Color accentGreen = successGreen;
  static const Color accentRed = alertRed;
  static const Color shadowDark = Color(0xFFBEBEBE);
  static const Color shadowLight = Color(0xFFFFFFFF);

  static final ThemeData lightTheme = ThemeData.light().copyWith(
    // Primary Color
    primaryColor: accentBlue,
    colorScheme: const ColorScheme.light(
      primary: accentBlue,
      secondary: accentPurple,
      surface: backgroundPrimary,
      onSurface: textPrimary,
      error: alertRed,
      onError: neutralWhite,
    ),

    // Scaffold Background
    scaffoldBackgroundColor: backgroundPrimary,

    // AppBar Theme
    appBarTheme: const AppBarTheme(
      color: backgroundPrimary,
      elevation: 0,
      titleTextStyle: TextStyle(
        color: textPrimary,
        fontSize: 1.4 * 16,
        fontWeight: FontWeight.w600,
      ),
      iconTheme: IconThemeData(color: accentBlue),
    ),

    // TextButton Theme
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: accentBlue,
        textStyle: const TextStyle(
          fontWeight: FontWeight.w500,
          fontSize: 1.0 * 16,
        ),
      ),
    ),

    // FloatingActionButtons
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: accentBlue,
      elevation: 5,
      foregroundColor: neutralWhite,
    ),

    // ElevatedButtons (Primary Button)
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: accentBlue,
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

    // Input Decoration Theme
    inputDecorationTheme: InputDecorationTheme(
      floatingLabelStyle: const TextStyle(color: accentBlue),
      enabledBorder: OutlineInputBorder(
        borderSide: const BorderSide(color: dividerGray, width: 1.5),
        borderRadius: BorderRadius.circular(1.1 * 16),
      ),
      focusedBorder: OutlineInputBorder(
        borderSide: const BorderSide(color: accentBlue, width: 1.5),
        borderRadius: BorderRadius.circular(1.1 * 16),
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(1.1 * 16),
      ),
      fillColor: neutralWhite,
      filled: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 1.2 * 16, vertical: 0.8 * 16),
      hintStyle: TextStyle(color: textSecondary.withAlpha((0.7 * 255).round())),
      labelStyle: const TextStyle(color: textSecondary),
    ),

    // Card Theme
    cardTheme: CardTheme(
      color: neutralWhite,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(2.0 * 16),
      ),
      margin: const EdgeInsets.only(bottom: 1.3 * 16),
      elevation: 8,
      shadowColor: const Color(0xFF4466F2).withAlpha((0.08 * 255).round()),
    ),

    // Icon Theme
    iconTheme: const IconThemeData(
      size: 1.3 * 16,
      color: accentBlue,
    ),

    // Text Theme (Typography)
    textTheme: const TextTheme(
      displayLarge: TextStyle(
        fontSize: 2.2 * 16,
        fontWeight: FontWeight.w700,
        color: textPrimary,
      ),
      titleLarge: TextStyle(
        fontSize: 1.4 * 16,
        fontWeight: FontWeight.w600,
        color: textPrimary,
      ),
      titleMedium: TextStyle(
        fontSize: 1.1 * 16,
        fontWeight: FontWeight.w500,
        color: textPrimary,
      ),
      bodyLarge: TextStyle(
        fontSize: 1.0 * 16,
        fontWeight: FontWeight.w400,
        color: textPrimary,
      ),
      bodyMedium: TextStyle(
        fontSize: 0.87 * 16,
        fontWeight: FontWeight.w400,
        color: textSecondary,
      ),
    ),
  );

  static final ThemeData darkTheme = ThemeData.dark().copyWith(
    // Primary Color
    primaryColor: accentBlue,
    colorScheme: const ColorScheme.dark(
      primary: accentBlue,
      secondary: accentPurple,
      surface: Colors.black,
      onSurface: neutralWhite,
      error: alertRed,
      onError: neutralWhite,
    ),
    scaffoldBackgroundColor: Colors.black,
    appBarTheme: const AppBarTheme(
      color: Colors.black,
      elevation: 0,
      titleTextStyle: TextStyle(
        color: neutralWhite,
        fontSize: 1.4 * 16,
        fontWeight: FontWeight.w600,
      ),
      iconTheme: IconThemeData(color: accentBlue),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: accentBlue,
        textStyle: const TextStyle(
          fontWeight: FontWeight.w500,
          fontSize: 1.0 * 16,
        ),
      ),
    ),
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: accentBlue,
      elevation: 5,
      foregroundColor: neutralWhite,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: accentBlue,
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
      floatingLabelStyle: const TextStyle(color: accentBlue),
      enabledBorder: OutlineInputBorder(
        borderSide: BorderSide(color: dividerGray.withAlpha((0.5 * 255).round()), width: 1.5),
        borderRadius: BorderRadius.circular(1.1 * 16),
      ),
      focusedBorder: OutlineInputBorder(
        borderSide: const BorderSide(color: accentBlue, width: 1.5),
        borderRadius: BorderRadius.circular(1.1 * 16),
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(1.1 * 16),
      ),
      fillColor: const Color(0xFF1A1A1A),
      filled: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 1.2 * 16, vertical: 0.8 * 16),
      hintStyle: TextStyle(color: neutralWhite.withAlpha((0.7 * 255).round())),
      labelStyle: const TextStyle(color: neutralWhite),
    ),
    cardTheme: CardTheme(
      color: const Color(0xFF1A1A1A),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(2.0 * 16),
      ),
      margin: const EdgeInsets.only(bottom: 1.3 * 16),
      elevation: 8,
      shadowColor: Colors.black.withAlpha((0.3 * 255).round()),
    ),
    iconTheme: const IconThemeData(
      size: 1.3 * 16,
      color: accentBlue,
    ),
    textTheme: TextTheme(
      displayLarge: const TextStyle(
        fontSize: 2.2 * 16,
        fontWeight: FontWeight.w700,
        color: neutralWhite,
      ),
      titleLarge: const TextStyle(
        fontSize: 1.4 * 16,
        fontWeight: FontWeight.w600,
        color: neutralWhite,
      ),
      titleMedium: const TextStyle(
        fontSize: 1.1 * 16,
        fontWeight: FontWeight.w500,
        color: neutralWhite,
      ),
      bodyLarge: const TextStyle(
        fontSize: 1.0 * 16,
        fontWeight: FontWeight.w400,
        color: neutralWhite,
      ),
      bodyMedium: TextStyle(
        fontSize: 0.87 * 16,
        fontWeight: FontWeight.w400,
        color: textSecondary.withAlpha((0.8 * 255).round()),
      ),
    ),
  );

  static final ThemeData oceanBlueTheme = lightTheme.copyWith(
    primaryColor: const Color(0xFF0077BE),
    scaffoldBackgroundColor: const Color(0xFFE3F2FD),
    colorScheme: lightTheme.colorScheme.copyWith(
      primary: const Color(0xFF0077BE),
      surface: const Color(0xFFE3F2FD),
    ),
    appBarTheme: const AppBarTheme(
      color: Color(0xFFE3F2FD),
      elevation: 0,
      titleTextStyle: TextStyle(
        color: textPrimary,
        fontSize: 1.4 * 16,
        fontWeight: FontWeight.w600,
      ),
      iconTheme: IconThemeData(color: Color(0xFF0077BE)),
    ),
  );

  static final ThemeData forestGreenTheme = lightTheme.copyWith(
    primaryColor: const Color(0xFF2E7D32),
    scaffoldBackgroundColor: const Color(0xFFE8F5E9),
    colorScheme: lightTheme.colorScheme.copyWith(
      primary: const Color(0xFF2E7D32),
      surface: const Color(0xFFE8F5E9),
    ),
    appBarTheme: const AppBarTheme(
      color: Color(0xFFE8F5E9),
      elevation: 0,
      titleTextStyle: TextStyle(
        color: textPrimary,
        fontSize: 1.4 * 16,
        fontWeight: FontWeight.w600,
      ),
      iconTheme: IconThemeData(color: Color(0xFF2E7D32)),
    ),
  );

  static final ThemeData sakuraPinkTheme = lightTheme.copyWith(
    primaryColor: const Color(0xFFE91E63),
    scaffoldBackgroundColor: const Color(0xFFFCE4EC),
    colorScheme: lightTheme.colorScheme.copyWith(
      primary: const Color(0xFFE91E63),
      surface: const Color(0xFFFCE4EC),
    ),
    appBarTheme: const AppBarTheme(
      color: Color(0xFFFCE4EC),
      elevation: 0,
      titleTextStyle: TextStyle(
        color: textPrimary,
        fontSize: 1.4 * 16,
        fontWeight: FontWeight.w600,
      ),
      iconTheme: IconThemeData(color: Color(0xFFE91E63)),
    ),
  );

  static final ThemeData royalPurpleTheme = lightTheme.copyWith(
    primaryColor: const Color(0xFF6A1B9A),
    scaffoldBackgroundColor: const Color(0xFFF3E5F5),
    colorScheme: lightTheme.colorScheme.copyWith(
      primary: const Color(0xFF6A1B9A),
      surface: const Color(0xFFF3E5F5),
    ),
    appBarTheme: const AppBarTheme(
      color: Color(0xFFF3E5F5),
      elevation: 0,
      titleTextStyle: TextStyle(
        color: textPrimary,
        fontSize: 1.4 * 16,
        fontWeight: FontWeight.w600,
      ),
      iconTheme: IconThemeData(color: Color(0xFF6A1B9A)),
    ),
  );

  // --- Neumorphic Styles ---

  static BoxDecoration concaveDecoration({
    required Color backgroundColor,
    double borderRadius = 8.0,
  }) {
    return BoxDecoration(
      color: backgroundColor,
      borderRadius: BorderRadius.circular(borderRadius),
      boxShadow: [
        BoxShadow(
          color: shadowDark.withAlpha((0.6 * 255).round()),
          offset: const Offset(3, 3),
          blurRadius: 6,
          spreadRadius: -2,
        ),
        BoxShadow(
          color: shadowLight.withAlpha((0.8 * 255).round()),
          offset: const Offset(-3, -3),
          blurRadius: 6,
          spreadRadius: -2,
        ),
      ],
    );
  }

  static BoxDecoration convexDecoration({
    required Color backgroundColor,
    double borderRadius = 8.0,
  }) {
    return BoxDecoration(
      color: backgroundColor,
      borderRadius: BorderRadius.circular(borderRadius),
      boxShadow: [
        BoxShadow(
          color: shadowLight.withAlpha((0.7 * 255).round()),
          offset: const Offset(-4, -4),
          blurRadius: 8,
          spreadRadius: 0,
        ),
        BoxShadow(
          color: shadowDark.withAlpha((0.5 * 255).round()),
          offset: const Offset(4, 4),
          blurRadius: 8,
          spreadRadius: 0,
        ),
      ],
    );
  }

  static List<BoxShadow> _getNeumorphicShadows({
    required Color baseColor,
    required Color backgroundColor,
    double depth = 8,
    Offset lightSource = const Offset(-0.75, -0.75),
    double blurRadius = 10,
  }) {
    final Color lightShadowColor = Color.lerp(backgroundColor, Colors.white, 0.7)!;
    final Color darkShadowColor = Color.lerp(backgroundColor, Colors.black, 0.2)!;

    return [
      BoxShadow(
        color: darkShadowColor,
        offset: Offset(depth * lightSource.dx, depth * lightSource.dy),
        blurRadius: blurRadius,
      ),
      BoxShadow(
        color: lightShadowColor,
        offset: Offset(-depth * lightSource.dx, -depth * lightSource.dy),
        blurRadius: blurRadius,
      ),
    ];
  }

  static BoxDecoration neumorphicDecoration({
    required Color baseColor,
    required Color backgroundColor,
    double borderRadius = 12,
    double depth = 8,
    Offset lightSource = const Offset(-0.75, -0.75),
    bool isConcave = false,
    bool isConvex = false,
  }) {
    List<BoxShadow> shadows = [];
    if (isConcave) {
      shadows = [
        BoxShadow(
          color: Colors.black.withAlpha((0.15 * 255).round()),
          offset: Offset(depth * lightSource.dx, depth * lightSource.dy),
          blurRadius: depth * 2,
          spreadRadius: -depth / 2,
        ),
        BoxShadow(
          color: Colors.white.withAlpha((0.7 * 255).round()),
          offset: Offset(-depth * lightSource.dx, -depth * lightSource.dy),
          blurRadius: depth * 2,
          spreadRadius: -depth / 2,
        ),
      ];
    } else if (isConvex) {
      shadows = _getNeumorphicShadows(
        baseColor: baseColor,
        backgroundColor: backgroundColor,
        depth: depth,
        lightSource: lightSource,
      );
    } else {
      shadows = _getNeumorphicShadows(
        baseColor: baseColor,
        backgroundColor: backgroundColor,
        depth: depth / 2,
        lightSource: lightSource,
        blurRadius: 10,
      );
    }

    return BoxDecoration(
      color: baseColor,
      borderRadius: BorderRadius.circular(borderRadius),
      boxShadow: shadows,
    );
  }
}
