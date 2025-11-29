import 'package:flutter/foundation.dart';

class AppLogger {
  AppLogger._();

  /// Log debug messages (only in debug mode)
  static void debug(String message, [String? tag]) {
    if (kDebugMode) {
      final prefix = tag != null ? '[$tag] ' : '';
      debugPrint('🔍 DEBUG: $prefix$message');
    }
  }

  /// Log info messages
  static void info(String message, [String? tag]) {
    if (kDebugMode) {
      final prefix = tag != null ? '[$tag] ' : '';
      debugPrint('ℹ️ INFO: $prefix$message');
    }
  }

  /// Log warning messages
  static void warning(String message, [String? tag]) {
    if (kDebugMode) {
      final prefix = tag != null ? '[$tag] ' : '';
      debugPrint('⚠️ WARNING: $prefix$message');
    }
  }

  /// Log error messages
  static void error(String message, [Object? error, StackTrace? stackTrace, String? tag]) {
    if (kDebugMode) {
      final prefix = tag != null ? '[$tag] ' : '';
      debugPrint('❌ ERROR: $prefix$message');
      if (error != null) {
        debugPrint('Error details: $error');
      }
      if (stackTrace != null) {
        debugPrint('Stack trace: $stackTrace');
      }
    }
  }

  /// Log API responses
  static void apiResponse(int statusCode, String endpoint, [String? body]) {
    if (kDebugMode) {
      debugPrint('🌐 API Response: $statusCode - $endpoint');
      if (body != null) {
        debugPrint('Response body: $body');
      }
    }
  }

  /// Log API requests
  static void apiRequest(String method, String endpoint, [Map<String, dynamic>? body]) {
    if (kDebugMode) {
      debugPrint('📤 API Request: $method $endpoint');
      if (body != null) {
        debugPrint('Request body: $body');
      }
    }
  }
}
