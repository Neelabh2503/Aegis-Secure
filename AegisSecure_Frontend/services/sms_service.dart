import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:permission_handler/permission_handler.dart';
import 'package:telephony/telephony.dart';

@pragma('vm:entry-point')
void backgroundSmsHandler(SmsMessage message) {
  print("Background SMS received: ${message.body}");
}

class SmsService {
  final Telephony _telephony = Telephony.instance;

  /// ✅ Request SMS permission
  Future<bool> requestSmsPermission() async {
    var status = await Permission.sms.status;
    if (status.isGranted) return true;

    var result = await Permission.sms.request();
    if (result.isGranted) return true;

    if (result.isPermanentlyDenied) {
      openAppSettings();
    }
    return false;
  }

  /// ✅ Fetch SMS messages locally (used in screen)
  Future<List<Map<String, dynamic>>> fetchLocalSms() async {
    bool hasPermission = await requestSmsPermission();
    if (!hasPermission) {
      print("No SMS permission granted");
      return [];
    }

    List<SmsMessage> messages = await _telephony.getInboxSms(
      columns: [
        SmsColumn.ADDRESS,
        SmsColumn.BODY,
        SmsColumn.DATE,
        SmsColumn.TYPE,
      ],
    );

    return messages.map((msg) {
      String type;
      if (msg.type == SmsType.MESSAGE_TYPE_SENT) {
        type = "sent";
      } else if (msg.type == SmsType.MESSAGE_TYPE_INBOX) {
        type = "inbox";
      } else {
        type = "other";
      }

      return {
        "address": msg.address,
        "body": msg.body,
        "date": msg.date,
        "type": type,
      };
    }).toList();
  }

  /// ✅ Sync SMS with backend
  Future<void> syncSmsToBackend(String userAuthToken, String backendUrl) async {
    bool hasPermission = await requestSmsPermission();
    if (!hasPermission) {
      print("Sync failed: No SMS permission.");
      return;
    }

    try {
      List<SmsMessage> messages = await _telephony.getInboxSms(
        columns: [
          SmsColumn.ADDRESS,
          SmsColumn.BODY,
          SmsColumn.DATE,
          SmsColumn.TYPE,
        ],
      );

      List<Map<String, dynamic>> smsJsonList = messages.map((msg) {
        String type;
        if (msg.type == SmsType.MESSAGE_TYPE_SENT) {
          type = "sent";
        } else if (msg.type == SmsType.MESSAGE_TYPE_INBOX) {
          type = "inbox";
        } else {
          type = "other";
        }

        return {
          "address": msg.address,
          "body": msg.body,
          "date_ms": msg.date,
          "type": type,
        };
      }).toList();

      final response = await http.post(
        Uri.parse('$backendUrl/sms/sync'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $userAuthToken',
          'ngrok-skip-browser-warning': 'true',
        },
        body: json.encode({"messages": smsJsonList}),
      );

      if (response.statusCode == 200) {
        print("Successfully synced ${messages.length} SMS messages.");
      } else {
        print("Failed to sync SMS. Status: ${response.statusCode}");
        print("Response: ${response.body}");
      }
    } catch (e) {
      print("Error syncing SMS: $e");
    }
  }

  /// ✅ Optional background listener
  void listenForIncomingSms() {
    _telephony.listenIncomingSms(
      onNewMessage: (SmsMessage message) {
        print("New SMS received: ${message.body}");
      },
      onBackgroundMessage: backgroundSmsHandler,
      listenInBackground: true,
    );
  }
}
