import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:telephony/telephony.dart';

import '../models/sms_message.dart';
import '../services/api_service.dart';

class SmsService {
  static const String baseUrl =
      "https://AEGIS14211-AegisSecureBackend.hf.space";
  // static const String baseUrl = "https://dodgily-kempt-bert.ngrok-free.dev";
  final Telephony telephony = Telephony.instance;

  static bool allowSyncingSMS = false;
  static Future<void> initAutoSyncFlag() async {
    final prefs = await SharedPreferences.getInstance();
    allowSyncingSMS = prefs.getBool(autoFetchSmsKey) ?? false;
  }

  Future<List<SmsMessageModel>> fetchDeviceSms() async {
    final List<SmsMessage> smsList = await telephony.getInboxSms(
      columns: [
        SmsColumn.ADDRESS,
        SmsColumn.BODY,
        SmsColumn.DATE,
        SmsColumn.TYPE,
      ],
      sortOrder: [OrderBy(SmsColumn.DATE, sort: Sort.DESC)],
    );

    const limit = 2;

    return smsList.take(limit).map((sms) {
      return SmsMessageModel(
        address: sms.address ?? "Unknown",
        body: sms.body ?? "",
        dateMs: sms.date ?? 0,
        type: sms.type == SmsType.MESSAGE_TYPE_INBOX ? "inbox" : "sent",
      );
    }).toList();
  }

  static const String autoFetchSmsKey = 'auto_fetch_sms_enabled';

  Future<bool> getAutoFetchSmsEnabled() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(autoFetchSmsKey) ?? false;
  }

  Future<void> setAutoFetchSmsEnabled(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(autoFetchSmsKey, value);
  }

  Future<bool> syncSmsToBackend() async {
    if (!allowSyncingSMS) {
      print("Auto-fetch SMS disabled by user.");
      return false;
    }

    try {
      final token = await ApiService.getToken();
      if (token == null || token.isEmpty) return false;

      // Fetch all previously synced messages
      final backendMessages = await fetchAllFromBackend();
      int latestBackendDate = 0;

      // if (backendMessages.isNotEmpty) {
      //   // Get the latest date among synced messages
      //   latestBackendDate = backendMessages
      //       .map((e) => e.dateMs)
      //       .reduce((a, b) => a > b ? a : b);
      // }

      if (backendMessages.isNotEmpty) {
        backendMessages.sort((a, b) => b.dateMs.compareTo(a.dateMs));
        final limitedBackend = backendMessages.take(25).toList();
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

      // Take only messages newer than the latest in backend
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

      // If this is the first sync, apply a fetch limit
      const int initialFetchLimit = 10;
      if (latestBackendDate == 0 && smsToSync.length > initialFetchLimit) {
        smsToSync = smsToSync.take(initialFetchLimit).toList();
      }

      if (smsToSync.isEmpty) {
        print("No new messages to sync.");
        return true;
      }

      // Send to backend
      final List<Map<String, dynamic>> messagesJson = smsToSync
          .map((sms) => sms.toJson())
          .toList();
      final url = Uri.parse("$baseUrl/sms/sync");
      final response = await http.post(
        url,
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer $token",
        },
        body: jsonEncode({"messages": messagesJson}),
      );

      if (response.statusCode == 200) {
        print("Synced ${smsToSync.length} messages successfully.");
      } else {
        print("Failed to sync messages. Status: ${response.statusCode}");
      }

      return response.statusCode == 200;
    } catch (e) {
      print("SMS sync failed: $e");
      return false;
    }
  }

  Future<List<SmsMessageModel>> fetchAllFromBackend() async {
    final token = await ApiService.getToken();
    if (token == null) return [];

    final url = Uri.parse("$baseUrl/sms/all");
    final response = await http.get(
      url,
      headers: {"Authorization": "Bearer $token"},
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final List messages = data["sms_messages"];
      return messages.map((e) => SmsMessageModel.fromJson(e)).toList();
    }
    return [];
  }
}
