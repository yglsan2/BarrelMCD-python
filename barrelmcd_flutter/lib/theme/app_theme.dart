import 'package:flutter/material.dart';

/// Thème sombre aligné sur l'interface Python (DarkTheme).
class AppTheme {
  // Couleurs de base - tons sombres
  static const Color background = Color(0xFF0A0A0A);
  static const Color surface = Color(0xFF1A1A1A);
  static const Color surfaceLight = Color(0xFF2A2A2A);
  static const Color surfaceDark = Color(0xFF151515);
  static const Color surfaceElevated = Color(0xFF252525);

  // Texte
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xFFB8B8B8);
  static const Color textTertiary = Color(0xFF888888);
  static const Color textDisabled = Color(0xFF555555);

  // Accent
  static const Color primary = Color(0xFF00D4FF);
  static const Color primaryDark = Color(0xFF0099CC);
  static const Color secondary = Color(0xFFFF6B35);
  static const Color success = Color(0xFF00E676);
  static const Color error = Color(0xFFFF1744);
  static const Color warning = Color(0xFFFFD600);

  // Entités / Associations
  static const Color entityBg = Color(0xFF1E2A3A);
  static const Color entityBorder = Color(0xFF2E3A4A);
  static const Color entitySelected = Color(0xFF00D4FF);
  static const Color associationBg = Color(0xFF4A1E3A);
  static const Color associationBorder = Color(0xFF5A2E4A);
  static const Color associationSelected = Color(0xFFFF6B35);

  // Toolbar / Boutons
  static const Color toolbarBg = Color(0xFF1A1A1A);
  static const Color buttonBg = Color(0xFF2A2A2A);
  static const Color buttonHover = Color(0xFF3A3A3A);
  static const Color buttonBorder = Color(0xFF3A3A3A);

  // Canvas
  static const Color canvasBackground = Color(0xFF1E1E1E);
  static const Color gridMajor = Color(0xFF333333);
  static const Color gridMinor = Color(0xFF222222);

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: background,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: secondary,
        surface: surface,
        error: error,
        onPrimary: Colors.black,
        onSecondary: Colors.black,
        onSurface: textPrimary,
        onError: Colors.white,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: toolbarBg,
        foregroundColor: textPrimary,
        elevation: 0,
        centerTitle: false,
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: buttonBg,
          foregroundColor: textPrimary,
          side: const BorderSide(color: buttonBorder),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(6),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: primary,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(6)),
        enabledBorder: const OutlineInputBorder(
          borderSide: BorderSide(color: surfaceLight),
        ),
        focusedBorder: const OutlineInputBorder(
          borderSide: BorderSide(color: primary, width: 2),
        ),
      ),
      dividerColor: surfaceLight,
    );
  }
}
