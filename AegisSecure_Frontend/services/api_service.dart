import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

class ApiService {
  // static const String baseUrl = "https://aegissecurebackend.onrender.com";
  static const String baseUrl =
      "https://aidyn-findable-greedily.ngrok-free.dev";
  // neEd to store the JWT tokn in sharedPreferences so that user dont have to logIn again and again every time he opens the App.
  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('jwt_token', token);
  }

  static Future<Map<String, dynamic>> fetchCurrentUser() async {
    final response = await http.get(Uri.parse('$baseUrl/user/me'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load user');
    }
  }

  static Future<http.Response> registerUser(
    String name,
    String email,
    String password,
  ) async {
    final url = Uri.parse('$baseUrl/auth/register');
    return await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'name': name, 'email': email, 'password': password}),
    );
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
    final redirectUri =
        "https://aidyn-findable-greedily.ngrok-free.dev/auth/google/callback";
    // final redirectUri = "https://aegissecurebackend.onrender.com/auth/google/callback";
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

    // 3️⃣ Launch Google login with fresh state
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
}