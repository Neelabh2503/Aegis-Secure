import 'dart:convert';

import 'package:http/http.dart' as http;

import '../services/api_service.dart';

class DashboardApi {
  static Future<Map<String, dynamic>?> fetchDashboard({
    String mode = 'both',
    int? days,
  }) async {
    final token = await ApiService.getToken();
    if (token == null) return null;

    final queryParameters = <String, String>{'mode': mode};
    if (days != null) queryParameters['days'] = days.toString();

    final uri = Uri.parse(
      '${ApiService.baseUrl}/dashboard',
    ).replace(queryParameters: queryParameters);

    try {
      final res = await http.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (res.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(res.body);
        return data;
      } else {
        // print('Dashboard fetch failed: ${res.statusCode} -> ${res.body}');
        return null;
      }
    } catch (e) {
      // print('Dashboard fetch exception: $e');
      return null;
    }
  }
}
