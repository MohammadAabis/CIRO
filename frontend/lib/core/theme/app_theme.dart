import 'package:flutter/material.dart';

/// CIRO Design System — centralised theme tokens.
class AppTheme {
  AppTheme._();

  // ── Brand Palette ───────────────────────────
  static const Color primaryBlue    = Color(0xFF3B82F6);
  static const Color accentCyan     = Color(0xFF06B6D4);
  static const Color criticalRed    = Color(0xFFEF4444);
  static const Color warningAmber   = Color(0xFFF59E0B);
  static const Color successGreen   = Color(0xFF10B981);
  static const Color surfaceDark    = Color(0xFF0F172A);
  static const Color cardDark       = Color(0xFF1E293B);
  static const Color textPrimary    = Color(0xFFF1F5F9);
  static const Color textSecondary  = Color(0xFF94A3B8);

  // ── Severity Colours ────────────────────────
  static const List<Color> severityColors = [
    Color(0xFF22C55E), // 1 — Minor
    Color(0xFFFACC15), // 2 — Moderate
    Color(0xFFF97316), // 3 — Significant
    Color(0xFFEF4444), // 4 — Severe
    Color(0xFF991B1B), // 5 — Catastrophic
  ];

  // ── Dark Theme ──────────────────────────────
  static final ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    fontFamily: 'Inter',
    scaffoldBackgroundColor: surfaceDark,
    colorScheme: const ColorScheme.dark(
      primary: primaryBlue,
      secondary: accentCyan,
      error: criticalRed,
      surface: cardDark,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: surfaceDark,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontFamily: 'Inter',
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: textPrimary,
      ),
    ),
    cardTheme: CardThemeData(
      color: cardDark,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    textTheme: const TextTheme(
      headlineLarge: TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: textPrimary),
      headlineMedium: TextStyle(fontSize: 22, fontWeight: FontWeight.w600, color: textPrimary),
      titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: textPrimary),
      bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w400, color: textSecondary),
      labelSmall: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: textSecondary),
    ),
  );
}
