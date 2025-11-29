import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';
import '../utils/logger.dart';
import 'base_http_client.dart';
import 'token_service.dart';

class AuthService {
  AuthService._();

  static Future<http.Response> registerUser(
    String name,
    String email,
    String password,
  ) async {
    try {
      final response = await BaseHttpClient.post(
        AppConfig.authRegisterEndpoint,
        body: {
          'name': name,
          'email': email,
          'password': password,
        },
      );
      return response;
    } catch (e, stackTrace) {
      AppLogger.error('Registration failed', e, stackTrace, 'AuthService');
      rethrow;
    }
  }

  /// Login user
  static Future<http.Response> loginUser(String email, String password) async {
    try {
      final response = await BaseHttpClient.post(
        AppConfig.authLoginEndpoint,
        body: {
          'email': email,
          'password': password,
        },
      );

      // Save token if login successful
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final token = data['token'];
        if (token != null) {
          await TokenService.saveToken(token);
          
          // Save account credentials
          await _saveAccountCredentials(email, password);
        }
      }

      return response;
    } catch (e, stackTrace) {
      AppLogger.error('Login failed', e, stackTrace, 'AuthService');
      rethrow;
    }
  }

  /// Save account credentials to local storage
  static Future<void> _saveAccountCredentials(String email, String password) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      List<String> savedAccounts = prefs.getStringList(AppConfig.savedAccountsKey) ?? [];
      
      final newAccount = '$email:$password';
      bool accountUpdated = false;

      // Update existing account or add new
      for (int i = 0; i < savedAccounts.length; i++) {
        final parts = savedAccounts[i].split(':');
        if (parts.isNotEmpty && parts[0] == email) {
          savedAccounts[i] = newAccount;
          accountUpdated = true;
          break;
        }
      }

      if (!accountUpdated) {
        savedAccounts.add(newAccount);
      }

      await prefs.setStringList(AppConfig.savedAccountsKey, savedAccounts);
    } catch (e, stackTrace) {
      AppLogger.error('Failed to save credentials', e, stackTrace, 'AuthService');
    }
  }

  /// Fetch current user information
  static Future<Map<String, dynamic>> fetchCurrentUser() async {
    final token = await TokenService.getToken();
    if (token == null || token.isEmpty) {
      throw Exception('No JWT token found');
    }

    try {
      final response = await BaseHttpClient.getAuth(
        AppConfig.authMeEndpoint,
        token,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load user: ${response.statusCode}');
      }
    } catch (e, stackTrace) {
      AppLogger.error('Failed to fetch user', e, stackTrace, 'AuthService');
      rethrow;
    }
  }

  /// Send OTP to email
  static Future<http.Response> sendOtp(String email) async {
    try {
      return await BaseHttpClient.post(
        AppConfig.authSendOtpEndpoint,
        body: {'email': email},
      );
    } catch (e, stackTrace) {
      AppLogger.error('Send OTP failed', e, stackTrace, 'AuthService');
      rethrow;
    }
  }

  /// Verify OTP
  static Future<http.Response> verifyOtp(String email, String otp) async {
    try {
      final response = await BaseHttpClient.post(
        AppConfig.authVerifyOtpEndpoint,
        body: {
          'email': email.trim(),
          'otp': otp.trim(),
        },
      );
      return response;
    } catch (e, stackTrace) {
      AppLogger.error('Verify OTP failed', e, stackTrace, 'AuthService');
      rethrow;
    }
  }

  /// Check email verification status
  static Future<http.Response> checkEmailVerification(String email) async {
    try {
      final response = await BaseHttpClient.post(
        AppConfig.authCheckEmailEndpoint,
        body: {'email': email},
      );
      return response;
    } catch (e, stackTrace) {
      AppLogger.error('Check email verification failed', e, stackTrace, 'AuthService');
      return http.Response('{"error": "network"}', 500);
    }
  }

  static Future<http.Response> resetPassword(
    String email,
    String otp,
    String newPassword,
  ) async {
    try {
      return await BaseHttpClient.post(
        AppConfig.authResetPasswordEndpoint,
        body: {
          'email': email,
          'otp': otp,
          'new_password': newPassword,
        },
      );
    } catch (e, stackTrace) {
      AppLogger.error('Reset password failed', e, stackTrace, 'AuthService');
      rethrow;
    }
  }

  static Future<void> logout() async {
    try {
      await TokenService.clearToken();
      AppLogger.info('User logged out', 'AuthService');
    } catch (e, stackTrace) {
      AppLogger.error('Logout failed', e, stackTrace, 'AuthService');
      rethrow;
    }
  }
}
