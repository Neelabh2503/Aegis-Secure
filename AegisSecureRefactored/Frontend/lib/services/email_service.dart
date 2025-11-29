import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../utils/logger.dart';
import 'base_http_client.dart';
import 'token_service.dart';
import 'gmail_service.dart';

class EmailService {
  EmailService._();

  static Future<List<dynamic>> fetchEmails({String? gmailEmail}) async {
    try {
      String? token;

      if (gmailEmail != null) {
        // Get Google access token for specific Gmail account
        token = await GmailService.getGoogleAccessToken(gmailEmail);
        if (token == null) {
          AppLogger.warning('Failed to get Google access token', 'EmailService');
          return [];
        }
      } else {
        // Get JWT token
        token = await TokenService.getToken();
        if (token == null || token.isEmpty) {
          AppLogger.warning('No JWT token found', 'EmailService');
          return [];
        }
      }

      final response = await BaseHttpClient.getAuth(
        AppConfig.emailsEndpoint,
        token,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return [];
      }
    } catch (e, stackTrace) {
      AppLogger.error('Failed to fetch emails', e, stackTrace, 'EmailService');
      return [];
    }
  }

  /// Fetch emails for a specific Gmail account
  static Future<List<dynamic>> fetchEmailsForAccount(String gmailEmail) async {
    try {
      final token = await TokenService.getToken();
      if (token == null) throw Exception('No token found');

      final url = '${AppConfig.emailsEndpoint}?account=$gmailEmail';
      final response = await BaseHttpClient.getAuth(url, token);

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to fetch emails');
      }
    } catch (e, stackTrace) {
      AppLogger.error('Failed to fetch account emails', e, stackTrace, 'EmailService');
      rethrow;
    }
  }

  static Future<List<dynamic>> searchEmails(String query) async {
    try {
      final token = await TokenService.getToken();
      if (token == null || token.isEmpty) {
        AppLogger.warning('No JWT token found', 'EmailService');
        return [];
      }

      final url = '${AppConfig.emailsSearchEndpoint}?q=${Uri.encodeComponent(query)}';
      final response = await BaseHttpClient.getAuth(url, token);

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        AppLogger.warning('Search failed with status ${response.statusCode}', 'EmailService');
        return [];
      }
    } catch (e, stackTrace) {
      AppLogger.error('Email search failed', e, stackTrace, 'EmailService');
      return [];
    }
  }
}
