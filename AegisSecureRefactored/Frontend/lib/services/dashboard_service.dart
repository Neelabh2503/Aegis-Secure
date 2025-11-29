import 'dart:convert';
import '../config/app_config.dart';
import '../utils/logger.dart';
import 'base_http_client.dart';
import 'token_service.dart';

class DashboardService {
  DashboardService._();

  static Future<Map<String, dynamic>?> fetchDashboard({
    String mode = 'both',
    int? days,
  }) async {
    try {
      final token = await TokenService.getToken();
      if (token == null) return null;

      final queryParameters = <String, String>{'mode': mode};
      if (days != null) queryParameters['days'] = days.toString();

      final uri = Uri.parse(AppConfig.dashboardEndpoint)
          .replace(queryParameters: queryParameters);

      final response = await BaseHttpClient.getAuth(uri.toString(), token);

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        return data;
      } else {
        AppLogger.warning('Dashboard fetch returned ${response.statusCode}', 'DashboardService');
        return null;
      }
    } catch (e, stackTrace) {
      AppLogger.error('Dashboard fetch failed', e, stackTrace, 'DashboardService');
      return null;
    }
  }
}
