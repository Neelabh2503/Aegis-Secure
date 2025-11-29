import 'package:flutter/material.dart';

class ColorUtils {
  ColorUtils._();

  static Color parseHexColor(String? hexColor, {Color fallback = Colors.grey}) {
    if (hexColor == null || hexColor.isEmpty) return fallback;
    
    try {
      String colorString = hexColor.replaceAll("#", "");
      
      if (colorString.length == 6) {
        colorString = "FF$colorString";
      }
      
      return Color(int.parse(colorString, radix: 16));
    } catch (e) {
      return fallback;
    }
  }

  static String colorToHex(Color color, {bool includeAlpha = true}) {
    if (includeAlpha) {
      return '#${color.alpha.toRadixString(16).padLeft(2, '0')}'
          '${color.red.toRadixString(16).padLeft(2, '0')}'
          '${color.green.toRadixString(16).padLeft(2, '0')}'
          '${color.blue.toRadixString(16).padLeft(2, '0')}'
          .toUpperCase();
    } else {
      return '#${color.red.toRadixString(16).padLeft(2, '0')}'
          '${color.green.toRadixString(16).padLeft(2, '0')}'
          '${color.blue.toRadixString(16).padLeft(2, '0')}'
          .toUpperCase();
    }
  }

  static Color getContrastingTextColor(Color backgroundColor) {
    final luminance = (0.299 * backgroundColor.red +
                      0.587 * backgroundColor.green +
                      0.114 * backgroundColor.blue) / 255;
    
    return luminance > 0.5 ? Colors.black : Colors.white;
  }

  static Color lighten(Color color, [double amount = 0.1]) {
    assert(amount >= 0 && amount <= 1, 'Amount must be between 0 and 1');
    
    final hsl = HSLColor.fromColor(color);
    final lightness = (hsl.lightness + amount).clamp(0.0, 1.0);
    
    return hsl.withLightness(lightness).toColor();
  }

  static Color darken(Color color, [double amount = 0.1]) {
    assert(amount >= 0 && amount <= 1, 'Amount must be between 0 and 1');
    
    final hsl = HSLColor.fromColor(color);
    final lightness = (hsl.lightness - amount).clamp(0.0, 1.0);
    
    return hsl.withLightness(lightness).toColor();
  }

  static Color generateColorFromString(String text) {
    if (text.isEmpty) return Colors.grey;
    
    int hash = 0;
    for (int i = 0; i < text.length; i++) {
      hash = text.codeUnitAt(i) + ((hash << 5) - hash);
    }
    
    final hue = (hash % 360).toDouble();
    return HSLColor.fromAHSL(1.0, hue, 0.6, 0.5).toColor();
  }
}
