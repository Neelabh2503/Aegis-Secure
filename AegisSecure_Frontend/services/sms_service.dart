import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:telephony/telephony.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../models/sms_message.dart';
import '../services/api_service.dart';

class SmsService {
  // static const String baseUrl =
      "https://aidyn-findable-greedily.ngrok-free.dev";
  static const String baseUrl = "https://aegissecurebackend.onrender.com";
  // static const String wsUrl =
      "wss://aidyn-findable-greedily.ngrok-free.dev/ws/sms";
  static const String wsUrl = 'wss://aegissecurebackend.onrender.com/ws/emails';

  final Telephony telephony = Telephony.instance;
  WebSocketChannel? _channel;

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
    final limit = 10;
    final allMessages = smsList.map((sms) {
      return SmsMessageModel(
        address: sms.address ?? "Unknown",
        body: sms.body ?? "",
        dateMs: sms.date ?? 0,
        type: sms.type == SmsType.MESSAGE_TYPE_INBOX ? "inbox" : "sent",
      );
    }).toList();
    final last10Messages = allMessages.take(limit).toList();
    return last10Messages;
  }

  Future<void> syncSmsToBackend() async {
    final token = await ApiService.getToken();
    if (token == null || token.isEmpty) {
      print("No JWT token found — user not logged in.");
      return;
    }

    final smsList = await fetchDeviceSms();
    print("Found ${smsList.length} SMS messages on device.");

    final url = Uri.parse("$baseUrl/sms/sync");
    final response = await http.post(
      url,
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer $token",
      },
      body: jsonEncode({"messages": smsList.map((m) => m.toJson()).toList()}),
    );

    if (response.statusCode == 200) {
      print("Synced ${smsList.length} SMS successfully to backend.");
    } else {
      print("Sync failed: ${response.statusCode} → ${response.body}");
    }
  }
  Future<List<SmsMessageModel>> fetchAllFromBackend() async {
    final token = await ApiService.getToken();
    if (token == null) {
      print("Missing token; cannot fetch backend SMS.");
      return [];
    }

    final url = Uri.parse("$baseUrl/sms/all");
    final response = await http.get(
      url,
      headers: {"Authorization": "Bearer $token"},
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final List messages = data["sms_messages"];
      print("Loaded ${messages.length} messages from backend.");
      return messages.map((e) => SmsMessageModel.fromJson(e)).toList();
    } else {
      print("Fetch failed: ${response.statusCode}");
      return [];
    }
  }
  void connectWebSocket(Function(SmsMessageModel) onNewMessage) {
    _channel = WebSocketChannel.connect(Uri.parse(wsUrl));

    _channel!.stream.listen(
      (message) {
        try {
          final data = jsonDecode(message);
          final newMsg = SmsMessageModel.fromJson(data);
          print("New SMS received via WebSocket: ${newMsg.body}");
          onNewMessage(newMsg);
        } catch (e) {
          print("WebSocket message parse error: $e");
        }
      },
      onDone: () {
        print("WebSocket closed. Reconnecting...");
        reconnect(onNewMessage);
      },
      onError: (err) {
        print("WebSocket error: $err");
        reconnect(onNewMessage);
      },
    );
  }

  void reconnect(Function(SmsMessageModel) onNewMessage) {
    Future.delayed(const Duration(seconds: 3), () {
      print("Reconnecting WebSocket...");
      connectWebSocket(onNewMessage);
    });
  }

  void disconnect() {
    _channel?.sink.close();
  }
}
