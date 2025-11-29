import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:telephony/telephony.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';
import '../models/sms_message.dart';
import '../utils/logger.dart';
import 'base_http_client.dart';
import 'token_service.dart';

class SmsService {
  final Telephony telephony = Telephony.instance;

  static bool allowSyncingSMS = false;

  static Future<void> initAutoSyncFlag() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      allowSyncingSMS = prefs.getBool(AppConfig.autoFetchSmsKey) ?? false;
      AppLogger.info('Auto-sync SMS: $allowSyncingSMS', 'SmsService');
    } catch (e, stackTrace) {
      AppLogger.error('Failed to init auto-sync flag', e, stackTrace, 'SmsService');
    }
  }

  Future<List<SmsMessageModel>> fetchDeviceSms() async {
    try {
      final List<SmsMessage> smsList = await telephony.getInboxSms(
        columns: [
          SmsColumn.ADDRESS,
          SmsColumn.BODY,
          SmsColumn.DATE,
          SmsColumn.TYPE,
        ],
        sortOrder: [OrderBy(SmsColumn.DATE, sort: Sort.DESC)],
      );

      return smsList.take(AppConfig.smsDeviceLimit).map((sms) {
        return SmsMessageModel(
          address: sms.address ?? "Unknown",
          body: sms.body ?? "",
          dateMs: sms.date ?? 0,
          type: sms.type == SmsType.MESSAGE_TYPE_INBOX ? "inbox" : "sent",
        );
      }).toList();
    } catch (e, stackTrace) {
      AppLogger.error('Failed to fetch device SMS', e, stackTrace, 'SmsService');
      return [];
    }
  }

  Future<bool> getAutoFetchSmsEnabled() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getBool(AppConfig.autoFetchSmsKey) ?? false;
    } catch (e, stackTrace) {
      AppLogger.error('Failed to get auto-fetch setting', e, stackTrace, 'SmsService');
      return false;
    }
  }

  Future<void> setAutoFetchSmsEnabled(bool value) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(AppConfig.autoFetchSmsKey, value);
      allowSyncingSMS = value;
      AppLogger.info('Auto-fetch SMS set to: $value', 'SmsService');
    } catch (e, stackTrace) {
      AppLogger.error('Failed to set auto-fetch setting', e, stackTrace, 'SmsService');
    }
  }

  /// Sync SMS messages from device to backend
  Future<bool> syncSmsToBackend() async {
    if (!allowSyncingSMS) {
      AppLogger.info('Auto-fetch SMS disabled by user', 'SmsService');
      return false;
    }

    try {
      final token = await TokenService.getToken();
      if (token == null || token.isEmpty) return false;

      // Fetch all previously synced messages
      final backendMessages = await fetchAllFromBackend();
      int latestBackendDate = 0;

      if (backendMessages.isNotEmpty) {
        backendMessages.sort((a, b) => b.dateMs.compareTo(a.dateMs));
        final limitedBackend = backendMessages.take(AppConfig.smsSyncLimit).toList();
        latestBackendDate = limitedBackend.first.dateMs;
      }

      // Fetch device SMS
      final List<SmsMessage> deviceSms = await telephony.getInboxSms(
        columns: [
          SmsColumn.ADDRESS,
          SmsColumn.BODY,
          SmsColumn.DATE,
          SmsColumn.TYPE,
        ],
        sortOrder: [OrderBy(SmsColumn.DATE, sort: Sort.DESC)],
      );

      // Filter messages newer than latest in backend
      List<SmsMessageModel> smsToSync = deviceSms
          .where((sms) => sms.date != null && sms.date! > latestBackendDate)
          .map(
            (sms) => SmsMessageModel(
              address: sms.address ?? "Unknown",
              body: sms.body ?? "",
              dateMs: sms.date ?? 0,
              type: sms.type == SmsType.MESSAGE_TYPE_INBOX ? "inbox" : "sent",
            ),
          )
          .toList();

      // Apply initial fetch limit if first sync
      if (latestBackendDate == 0 && smsToSync.length > AppConfig.initialSmsFetchLimit) {
        smsToSync = smsToSync.take(AppConfig.initialSmsFetchLimit).toList();
      }

      if (smsToSync.isEmpty) {
        AppLogger.info('No new messages to sync', 'SmsService');
        return true;
      }

      // Send to backend
      final List<Map<String, dynamic>> messagesJson =
          smsToSync.map((sms) => sms.toJson()).toList();

      final response = await BaseHttpClient.postAuth(
        AppConfig.smsSyncEndpoint,
        token,
        body: {"messages": messagesJson},
      );

      if (response.statusCode == 200) {
        AppLogger.info('Synced ${smsToSync.length} messages', 'SmsService');
        return true;
      } else {
        AppLogger.warning('SMS sync failed: ${response.statusCode}', 'SmsService');
        return false;
      }
    } catch (e, stackTrace) {
      AppLogger.error('SMS sync failed', e, stackTrace, 'SmsService');
      return false;
    }
  }

  static Future<List<SmsMessageModel>> fetchAllFromBackend() async {
    try {
      final token = await TokenService.getToken();
      if (token == null) return [];

      final response = await BaseHttpClient.getAuth(
        AppConfig.smsAllEndpoint,
        token,
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => SmsMessageModel.fromJson(json)).toList();
      } else {
        return [];
      }
    } catch (e, stackTrace) {
      AppLogger.error('Failed to fetch SMS from backend', e, stackTrace, 'SmsService');
      return [];
    }
  }

  /// Analyze a list of SMS messages for spam
  static Future<Map<String, dynamic>> analyzeSmsList(
    List<SmsMessage> messages,
  ) async {
    try {
      final token = await TokenService.getToken();
      if (token == null) throw Exception('User is not authenticated');

      final List<String> messageBodies = messages
          .map((msg) => msg.body ?? "")
          .where((body) => body.isNotEmpty)
          .toList();

      if (messageBodies.isEmpty) {
        return {'status': 'success', 'message': 'No new messages to analyze.'};
      }

      final response = await BaseHttpClient.postAuth(
        AppConfig.smsAnalyzeListEndpoint,
        token,
        body: {'texts': messageBodies},
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to analyze SMS list: ${response.body}');
      }
    } catch (e, stackTrace) {
      AppLogger.error('SMS analysis failed', e, stackTrace, 'SmsService');
      rethrow;
    }
  }
}
