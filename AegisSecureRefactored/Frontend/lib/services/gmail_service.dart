import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';
import '../utils/logger.dart';
import 'base_http_client.dart';
import 'token_service.dart';

class GmailService {
  GmailService._();

  static String? selectedEmailAccount;

  static Future<void> launchGoogleLogin() async {
    try {
      final userId = await TokenService.getUserId();
      if (userId == null) {
        AppLogger.warning('No user logged in', 'GmailService');
        return;
      }

      // Get state token
      final response = await BaseHttpClient.get(
        '${AppConfig.gmailStateTokenEndpoint}?user_id=$userId',
      );

      if (response.statusCode != 200) {
        AppLogger.error('Failed to get state token', null, null, 'GmailService');
        return;
      }

      final stateToken = jsonDecode(response.body)['state'];

      // Build OAuth URL
      final url = Uri.parse(
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?client_id=${AppConfig.googleClientId}"
        "&response_type=code"
        "&scope=${AppConfig.googleAuthScope}"
        "&redirect_uri=${AppConfig.googleRedirectUri}"
        "&access_type=offline"
        "&prompt=consent"
        "&state=$stateToken",
      );

      if (await canLaunchUrl(url)) {
        await launchUrl(url, mode: LaunchMode.externalApplication);
      } else {
        AppLogger.error("Can't launch URL", null, null, 'GmailService');
      }
    } catch (e, stackTrace) {
      AppLogger.error('Google login failed', e, stackTrace, 'GmailService');
      rethrow;
    }
  }

  static Future<String?> getGoogleAccessToken(String gmailEmail) async {
    try {
      final userId = await TokenService.getUserId();
      if (userId == null || gmailEmail.isEmpty) return null;

      final url = '${AppConfig.gmailRefreshEndpoint}?user_id=$userId&gmail_email=$gmailEmail';
      final response = await BaseHttpClient.get(url);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['access_token'];
      } else {
        AppLogger.warning('Failed to refresh access token', 'GmailService');
        return null;
      }
    } catch (e, stackTrace) {
      AppLogger.error('Get access token failed', e, stackTrace, 'GmailService');
      return null;
    }
  }

  static Future<Map<String, dynamic>> fetchConnectedAccounts() async {
    try {
      final token = await TokenService.getToken();
      if (token == null) throw Exception('No token found');

      final response = await BaseHttpClient.getAuth(
        AppConfig.gmailAccountsEndpoint,
        token,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load Gmail accounts');
      }
    } catch (e, stackTrace) {
      AppLogger.error('Failed to fetch connected accounts', e, stackTrace, 'GmailService');
      rethrow;
    }
  }

  static Future<List<dynamic>> getConnectedGmailAccounts() async {
    try {
      final token = await TokenService.getToken();
      if (token == null) throw Exception('No token found');

      final response = await BaseHttpClient.getAuth(
        AppConfig.gmailAccountsEndpoint,
        token,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to fetch connected accounts');
      }
    } catch (e, stackTrace) {
      AppLogger.error('Failed to get Gmail accounts', e, stackTrace, 'GmailService');
      rethrow;
    }
  }

  static Future<void> deleteConnectedAccount(String gmailEmail) async {
    try {
      final token = await TokenService.getToken();
      if (token == null) throw Exception('No token found');

      final response = await BaseHttpClient.postAuth(
        AppConfig.accountsDeleteEndpoint,
        token,
        body: {'gmail_email': gmailEmail},
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to delete account: ${response.body}');
      }
    } catch (e, stackTrace) {
      AppLogger.error('Delete account failed', e, stackTrace, 'GmailService');
      rethrow;
    }
  }

  /// Get active linked account email from preferences
  static Future<String?> getActiveLinkedAccountEmail() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(AppConfig.activeLinkedEmailKey);
    } catch (e, stackTrace) {
      AppLogger.error('Failed to get active account', e, stackTrace, 'GmailService');
      return null;
    }
  }

  /// Set active linked account email in preferences
  static Future<void> setActiveLinkedAccountEmail(String? email) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (email == null) {
        await prefs.remove(AppConfig.activeLinkedEmailKey);
      } else {
        await prefs.setString(AppConfig.activeLinkedEmailKey, email);
      }
    } catch (e, stackTrace) {
      AppLogger.error('Failed to set active account', e, stackTrace, 'GmailService');
      rethrow;
    }
  }
}
