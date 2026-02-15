import 'package:flutter/material.dart';

/// Thème sombre — charte graphique alignée sur le projet Python (views/dark_theme.py).
/// Toutes les couleurs correspondent à DarkTheme.COLORS.
class AppTheme {
  // Base — DarkTheme.COLORS
  static const Color background = Color(0xFF0A0A0A);       // "background"
  static const Color surface = Color(0xFF1A1A1A);         // "surface" / "dialog_bg" / "toolbar_bg"
  static const Color surfaceLight = Color(0xFF2A2A2A);     // "surface_light" / "toolbar_border" / "button_bg"
  static const Color surfaceDark = Color(0xFF151515);      // "surface_dark"
  static const Color surfaceElevated = Color(0xFF252525);  // "surface_elevated"

  // Texte
  static const Color textPrimary = Color(0xFFFFFFFF);      // "text_primary"
  static const Color textSecondary = Color(0xFFB8B8B8);   // "text_secondary"
  static const Color textTertiary = Color(0xFF888888);     // "text_tertiary"
  static const Color textDisabled = Color(0xFF555555);     // "text_disabled"

  // Accent
  static const Color primary = Color(0xFF00D4FF);          // "primary"
  static const Color primaryDark = Color(0xFF0099CC);     // "primary_dark"
  static const Color secondary = Color(0xFFFF6B35);       // "secondary" / "relation_selected"
  static const Color success = Color(0xFF00E676);          // "success"
  static const Color error = Color(0xFFFF1744);            // "error"
  static const Color warning = Color(0xFFFFD600);         // "warning"

  // Entités / Associations (MCD)
  static const Color entityBg = Color(0xFF1E2A3A);        // "entity_bg"
  static const Color entityBorder = Color(0xFF2E3A4A);    // "entity_border"
  static const Color entitySelected = Color(0xFF00D4FF);  // "entity_selected"
  static const Color associationBg = Color(0xFF4A1E3A);  // "relation_bg"
  static const Color associationBorder = Color(0xFF5A2E4A); // "relation_border"
  static const Color associationSelected = Color(0xFFFF6B35); // "relation_selected"
  /// Cardinalité côté association (boîte mauve pour différencier du bleu côté entité).
  static const Color cardinalityAssoc = Color(0xFFB8A0C8);

  // Toolbar / Boutons
  static const Color toolbarBg = Color(0xFF1A1A1A);       // "toolbar_bg"
  static const Color buttonBg = Color(0xFF2A2A2A);        // "button_bg"
  static const Color buttonHover = Color(0xFF3A3A3A);     // "button_hover"
  static const Color buttonBorder = Color(0xFF3A3A3A);    // "button_border"

  // Canvas
  static const Color canvasBackground = Color(0xFF0A0A0A); // "background"
  // Grille (DarkTheme) : tons légèrement éclaircis pour être visibles sur #0A0A0A
  static const Color gridMajor = Color(0xFF484848);        // dérivé "grid_major"
  static const Color gridMinor = Color(0xFF363636);        // dérivé "grid_minor"

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
