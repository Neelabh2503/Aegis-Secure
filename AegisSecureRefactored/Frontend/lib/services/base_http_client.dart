import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../utils/logger.dart';

class BaseHttpClient {
  BaseHttpClient._();

  static Map<String, String> _getAuthHeaders(String token) {
    return {
      'Content-Type': AppConfig.contentTypeJson,
      'Authorization': 'Bearer $token',
    };
  }

  static Map<String, String> _getCommonHeaders() {
    return {
      'Content-Type': AppConfig.contentTypeJson,
      'ngrok-skip-browser-warning': AppConfig.ngrokSkipBrowserWarning,
    };
  }

  static Future<http.Response> getAuth(
    String url,
    String token, {
    Map<String, String>? additionalHeaders,
  }) async {
    AppLogger.apiRequest('GET', url);
    
    final headers = {..._getAuthHeaders(token), ...?additionalHeaders};
    
    try {
      final response = await http.get(Uri.parse(url), headers: headers);
      AppLogger.apiResponse(response.statusCode, url, response.body);
      return response;
    } catch (e, stackTrace) {
      AppLogger.error('GET request failed', e, stackTrace, 'BaseHttpClient');
      rethrow;
    }
  }

  static Future<http.Response> postAuth(
    String url,
    String token, {
    Map<String, dynamic>? body,
    Map<String, String>? additionalHeaders,
  }) async {
    AppLogger.apiRequest('POST', url, body);
    
    final headers = {..._getAuthHeaders(token), ...?additionalHeaders};
    
    try {
      final response = await http.post(
        Uri.parse(url),
        headers: headers,
        body: body != null ? jsonEncode(body) : null,
      );
      AppLogger.apiResponse(response.statusCode, url, response.body);
      return response;
    } catch (e, stackTrace) {
      AppLogger.error('POST request failed', e, stackTrace, 'BaseHttpClient');
      rethrow;
    }
  }

  static Future<http.Response> get(
    String url, {
    Map<String, String>? additionalHeaders,
  }) async {
    AppLogger.apiRequest('GET', url);
    
    final headers = {..._getCommonHeaders(), ...?additionalHeaders};
    
    try {
      final response = await http.get(Uri.parse(url), headers: headers);
      AppLogger.apiResponse(response.statusCode, url, response.body);
      return response;
    } catch (e, stackTrace) {
      AppLogger.error('GET request failed', e, stackTrace, 'BaseHttpClient');
      rethrow;
    }
  }

  static Future<http.Response> post(
    String url, {
    Map<String, dynamic>? body,
    Map<String, String>? additionalHeaders,
  }) async {
    AppLogger.apiRequest('POST', url, body);
    
    final headers = {..._getCommonHeaders(), ...?additionalHeaders};
    
    try {
      final response = await http.post(
        Uri.parse(url),
        headers: headers,
        body: body != null ? jsonEncode(body) : null,
      );
      AppLogger.apiResponse(response.statusCode, url, response.body);
      return response;
    } catch (e, stackTrace) {
      AppLogger.error('POST request failed', e, stackTrace, 'BaseHttpClient');
      rethrow;
    }
  }
}
