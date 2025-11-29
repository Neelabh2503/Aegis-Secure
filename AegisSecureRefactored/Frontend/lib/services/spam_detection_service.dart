import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../utils/logger.dart';
import 'base_http_client.dart';

class SpamDetectionService {
  SpamDetectionService._();

  static Future<Map<String, dynamic>> analyzeText(String text) async {
    try {
      final response = await http.post(
        Uri.parse(AppConfig.cyberApiUrl),
        headers: {'Content-Type': AppConfig.contentTypeJson},
        body: jsonEncode({
          "sender": "",
          "subject": "",
          "text": text,
        }),
      );

      if (response.statusCode == 200) {
        final decoded = jsonDecode(response.body);
        return decoded;
      } else {
        AppLogger.warning('Spam detection returned non-200: ${response.statusCode}', 'SpamDetectionService');
        return {"prediction": "0.0"};
      }
    } catch (e, stackTrace) {
      AppLogger.error('Spam detection failed', e, stackTrace, 'SpamDetectionService');
      return {"prediction": "0.0"};
    }
  }
}
