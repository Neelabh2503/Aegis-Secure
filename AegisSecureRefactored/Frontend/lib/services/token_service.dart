import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';
import '../utils/logger.dart';

class TokenService {
  TokenService._();

  static Future<void> saveToken(String token) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(AppConfig.jwtTokenKey, token);
      AppLogger.info('Token saved successfully', 'TokenService');
    } catch (e, stackTrace) {
      AppLogger.error('Failed to save token', e, stackTrace, 'TokenService');
      rethrow;
    }
  }

  static Future<String?> getToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(AppConfig.jwtTokenKey);
    } catch (e, stackTrace) {
      AppLogger.error('Failed to get token', e, stackTrace, 'TokenService');
      return null;
    }
  }

  static Future<void> clearToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(AppConfig.jwtTokenKey);
      AppLogger.info('Token cleared successfully', 'TokenService');
    } catch (e, stackTrace) {
      AppLogger.error('Failed to clear token', e, stackTrace, 'TokenService');
      rethrow;
    }
  }

  static Future<String?> getUserId() async {
    try {
      final token = await getToken();
      if (token == null) return null;

      final parts = token.split('.');
      if (parts.length != 3) return null;

      final payload = utf8.decode(
        base64Url.decode(base64Url.normalize(parts[1])),
      );
      final data = jsonDecode(payload);
      return data['user_id'];
    } catch (e, stackTrace) {
      AppLogger.error('Failed to extract user ID', e, stackTrace, 'TokenService');
      return null;
    }
  }

  static Future<bool> isAuthenticated() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }
}
