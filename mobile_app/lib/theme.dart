import "package:flutter/material.dart";
import "package:google_fonts/google_fonts.dart";

/// Design tokens for the "Field Instrument HUD" aesthetic.
///
/// Single source of truth translated from mobile_app/design/hazard_detect_ui.html.
/// Severity colours (red/orange/amber) are RESERVED for hazard severity only;
/// the phosphor-teal accent carries all neutral system chrome.
class Hud {
  Hud._();

  // ---- instrument palette ----
  static const Color bg = Color(0xFF070B0C); // outer / scaffold
  static const Color panel = Color(0xFF0C1213); // device body
  static const Color panel2 = Color(0xFF11191A); // raised rows
  static const Color line = Color(0xFF1C2829); // hairlines
  static const Color teal = Color(0xFF2DE1C2); // system accent
  static const Color ink = Color(0xFFE8EFEE); // primary text
  static const Color inkMute = Color(0xFF5E7273); // secondary text
  static const Color inkFaint = Color(0xFF38484A); // tertiary / disabled

  // ---- severity semantics (RESERVED) ----
  static const Color sevHigh = Color(0xFFFF4438);
  static const Color sevMed = Color(0xFFFF9A1F);
  static const Color sevLow = Color(0xFFFFD23D);

  /// Map a backend severity string ("high" | "medium" | "low") to its colour.
  static Color severityColor(String severity) {
    switch (severity.toLowerCase()) {
      case "high":
        return sevHigh;
      case "medium":
        return sevMed;
      default:
        return sevLow;
    }
  }

  // ---- typography ----
  // Chakra Petch = technical HUD chrome (labels, buttons, titles).
  // JetBrains Mono = data readouts (metrics, status, advisory body).

  /// HUD label/title style (Chakra Petch). Caller sets size/weight/colour.
  static TextStyle chrome({
    double size = 12,
    FontWeight weight = FontWeight.w600,
    Color color = ink,
    double spacing = 1.5,
  }) {
    return GoogleFonts.chakraPetch(
      fontSize: size,
      fontWeight: weight,
      color: color,
      letterSpacing: spacing,
    );
  }

  /// Data/mono style (JetBrains Mono).
  static TextStyle mono({
    double size = 11,
    FontWeight weight = FontWeight.w400,
    Color color = ink,
    double spacing = 0.5,
    double height = 1.2,
  }) {
    return GoogleFonts.jetBrainsMono(
      fontSize: size,
      fontWeight: weight,
      color: color,
      letterSpacing: spacing,
      height: height,
    );
  }

  /// App-wide dark theme tuned to the instrument palette.
  static ThemeData themeData() {
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: bg,
      colorScheme: base.colorScheme.copyWith(
        primary: teal,
        surface: panel,
        brightness: Brightness.dark,
      ),
      textTheme: GoogleFonts.jetBrainsMonoTextTheme(base.textTheme)
          .apply(bodyColor: ink, displayColor: ink),
    );
  }
}
