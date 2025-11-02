import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:telephony/telephony.dart';
import 'package:telephony/telephony.dart';
import 'package:url_launcher/url_launcher.dart';

class ApiService {
  static const String baseUrl = "https://aegissecurebackend.onrender.com";
  static const String CyberUrl =
      "https://cybersecure-backend-api.onrender.com/predict";
  // static const String baseUrl =
      "https://aidyn-findable-greedily.ngrok-free.dev";
  // neEd to store the JWT tokn in sharedPreferences so that user dont have to logIn again and again every time he opens the App.
  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('jwt_token', token);
  }

  static Future<Map<String, dynamic>> fetchCurrentUser() async {
    final token = await getToken();
    if (token == null || token.isEmpty) {
      throw Exception('No JWT token found');
    }

    final response = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      print(
        "⚠️ Failed to load user: ${response.statusCode} → ${response.body}",
      );
      throw Exception('Failed to load user');
    }
  }

  static Future<http.Response> registerUser(
    String name,
    String email,
    String password,
  ) async {
    final url = Uri.parse('$baseUrl/auth/register');
    // return await http.post(
    //   url,
    //   headers: {'Content-Type': 'application/json'},
    //   body: jsonEncode({'name': name, 'email': email, 'password': password}),
    // );
    final res = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'name': name, 'email': email, 'password': password}),
    );
    print('🔴 Register response: ${res.statusCode} → ${res.body}');
    return res;
  }

  static Future<http.Response> loginUser(String email, String password) async {
    final url = Uri.parse('$baseUrl/auth/login');
    final res = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      final token = data['token'];
      if (token != null) {
        await saveToken(token);
      }
    }
    return res;
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('jwt_token');
  }

  static Future<String?> getUserId() async {
    final token = await getToken();
    if (token == null) return null;

    final parts = token.split('.');
    if (parts.length != 3) return null;

    final payload = utf8.decode(
      base64Url.decode(base64Url.normalize(parts[1])),
    );
    final data = jsonDecode(payload);
    return data['user_id'];
  }

  static Future<String?> getGoogleAccessToken(String gmailEmail) async {
    final userId = await getUserId();
    if (userId == null || gmailEmail.isEmpty) return null;

    final url = Uri.parse(
      '$baseUrl/gmail/refresh?user_id=$userId&gmail_email=$gmailEmail',
    );
    final res = await http.get(
      url,
      headers: {'Content-Type': 'application/json'},
    );

    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      return data['access_token'];
    } else {
      print("⚠️ Failed to refresh access token: ${res.body}");
      return null;
    }
  }

  static Future<Map<String, dynamic>> analyzeText(String text) async {
    final url = Uri.parse(
      "https://cybersecure-backend-api.onrender.com/predict",
    );
    print("DEBUG: Sending POST request to $url with text='$text'");

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"text": text}),
      );

      print("DEBUG: Raw API HTTP status = ${response.statusCode}");
      print("DEBUG: Raw API HTTP body = ${response.body}");

      if (response.statusCode == 200) {
        final decoded = jsonDecode(response.body);
        print("DEBUG: Decoded API JSON = $decoded");
        return decoded;
      } else {
        print("DEBUG: Non-200 response: ${response.statusCode}");
        return {"prediction": "0.0"};
      }
    } catch (e) {
      print("DEBUG: Exception during API call: $e");
      return {"prediction": "0.0"};
    }
  }

  static Future<List<dynamic>> fetchEmails({String? gmailEmail}) async {
    String? token;

    if (gmailEmail != null) {
      token = await getGoogleAccessToken(gmailEmail);
      if (token == null) {
        print("⚠️ Failed to get refreshed Google access token");
        return [];
      }
    } else {
      token = await getToken();
      if (token == null || token.isEmpty) {
        print("⚠️ No JWT token found in SharedPreferences");
        return [];
      }
    }

    final url = Uri.parse('$baseUrl/emails');
    final res = await http.get(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );
    print("🔵 Status code: ${res.statusCode}");
    print("🔵 Response body: ${res.body}");
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      return [];
    }
  }

  static Future<void> launchGoogleLogin() async {
    final clientId =
        "365011130597-3bv38b9aubtt65rebnbl673c2cogt7j3.apps.googleusercontent.com";
    // final redirectUri ="https://aidyn-findable-greedily.ngrok-free.dev/auth/google/callback";
    final redirectUri ="https://aegissecurebackend.onrender.com/auth/google/callback";
    // 1️⃣ Get user_id from login JWT
    final userId = await getUserId();
    if (userId == null) {
      print("⚠️ No user logged in");
      return;
    }

    // 2️⃣ Request fresh state token from backend
    final res = await http.get(
      Uri.parse("$baseUrl/gmail/state-token?user_id=$userId"),
    );
    if (res.statusCode != 200) {
      print("⚠️ Failed to get state token");
      return;
    }
    final stateToken = jsonDecode(res.body)['state'];


    final url = Uri.parse(
      "https://accounts.google.com/o/oauth2/v2/auth"
      "?client_id=$clientId"
      "&response_type=code"
      "&scope=https://www.googleapis.com/auth/gmail.readonly"
      "&redirect_uri=$redirectUri"
      "&access_type=offline"
      "&prompt=consent"
      "&state=$stateToken",
    );

    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } else {
      print("⚠️ Can't launch $url");
    }
  }
  static Future<http.Response> sendOtp(String email) async {
    final url = Uri.parse('$baseUrl/auth/send-otp');
    return await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );
  }

  static Future<http.Response> verifyOtp(String email, String otp) async {
    final url = Uri.parse('$baseUrl/auth/verify-otp');

    print("⭐️" + email);
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email.trim(), 'otp': otp.trim()}),
    );

    print("🔴 Verify OTP response: ${response.statusCode} -> ${response.body}");
    return response; 
  }

  static Future<http.Response> checkEmailVerification(String email) async {
    final url = Uri.parse('$baseUrl/auth/check-email'); 

    try {
      final res = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email}),
      );
      print("Check Email Status: ${res.statusCode}, Body: ${res.body}");
      return res;
    } catch (e) {
      print("Error checking email verification: $e");
      return http.Response('{"error": "network"}', 500);
    }
  }
  static Future<Map<String, dynamic>> fetchConnectedAccounts() async {
    final token = await getToken();
    final url = Uri.parse('$baseUrl/gmail/accounts');
    final res = await http.get(
      url,
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception('Failed to load Gmail accounts');
    }
  }

  static Future<List<dynamic>> fetchEmailsForAccount(String gmailEmail) async {
    final token = await getToken();
    final url = Uri.parse('$baseUrl/emails?account=$gmailEmail');
    final res = await http.get(
      url,
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception('Failed to fetch emails');
    }
  }

  static Future<Map<String, dynamic>> getCurrentUser() async {
    final token = await getToken();
    final res = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception('Failed to fetch user info');
    }
  }

  static Future<List<dynamic>> getConnectedGmailAccounts() async {
    final token = await getToken();
    final res = await http.get(
      Uri.parse('$baseUrl/gmail/accounts'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception('Failed to fetch connected accounts');
    }
  }
  static Future<void> deleteConnectedAccount(String gmailEmail) async {
    final url = Uri.parse('$baseUrl/accounts/delete');
    try {
      final res = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${await getToken()}',
        },
        body: jsonEncode({'gmail_email': gmailEmail}),
      );

      if (res.statusCode != 200) {
        throw Exception('Failed to delete account: ${res.body}');
      }
    } catch (e) {
      throw Exception('Error deleting account: $e');
    }
  }

  static Future<String?> getActiveLinkedAccountEmail() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('active_linked_email');
  }

  static Future<void> setActiveLinkedAccountEmail(String? email) async {
    final prefs = await SharedPreferences.getInstance();
    if (email == null) {
      await prefs.remove('active_linked_email');
    } else {
      await prefs.setString('active_linked_email', email);
    }
  }
  //--⭐️ 
}