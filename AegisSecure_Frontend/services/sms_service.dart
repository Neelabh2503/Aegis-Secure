import 'dart:async';
import 'package:permission_handler/permission_handler.dart';
import 'package:telephony/telephony.dart';

@pragma('vm:entry-point')
void backgroundSmsHandler(SmsMessage message) {
  print("BG SMS: ${message.body}");
}

class SmsService {
  final Telephony _telephony = Telephony.instance;
  final StreamController<Map<String, dynamic>> _smsStreamController =
  StreamController.broadcast();

  Stream<Map<String, dynamic>> get onNewMessage => _smsStreamController.stream;

  Future<bool> requestSmsPermission() async {
    var status = await Permission.sms.status;
    if (status.isGranted) return true;
    var result = await Permission.sms.request();
    if (result.isGranted) return true;
    if (result.isPermanentlyDenied) openAppSettings();
    return false;
  }

  Future<List<Map<String, dynamic>>> getAllMessages({int limit = 10}) async {
    bool hasPermission = await requestSmsPermission();
    if (!hasPermission) {
      print("No SMS permission");
      return [];
    }

    try {
      print("Fetching latest $limit SMS...");
      List<SmsMessage> messages = await _telephony.getInboxSms(
        columns: [
          SmsColumn.ADDRESS,
          SmsColumn.BODY,
          SmsColumn.DATE,
          SmsColumn.TYPE,
        ],
        sortOrder: [OrderBy(SmsColumn.DATE, sort: Sort.DESC)],
      );

      final recent = messages.take(limit).toList();
      print("Fetched ${recent.length} SMS");

      return recent
          .map(
            (msg) => {
          "address": msg.address ?? "Unknown",
          "body": msg.body ?? "",
          "date": msg.date,
          "type": msg.type == SmsType.MESSAGE_TYPE_INBOX
              ? "inbox"
              : msg.type == SmsType.MESSAGE_TYPE_SENT
              ? "sent"
              : "other",
        },
      )
          .toList();
    } catch (e, st) {
      print("Error in getAllMessages: $e\n$st");
      return [];
    }
  }

  void startListeningForIncomingSms() {
    _telephony.listenIncomingSms(
      onNewMessage: (SmsMessage message) {
        final data = {
          "address": message.address ?? "Unknown",
          "body": message.body ?? "",
          "date": message.date,
          "type": "inbox",
        };
        print("New SMS: ${message.body}");
        _smsStreamController.add(data);
      },
      onBackgroundMessage: backgroundSmsHandler,
      listenInBackground: true,
    );
  }
}
