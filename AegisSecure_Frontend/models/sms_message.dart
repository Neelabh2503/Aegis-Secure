// lib/models/sms_message.dart
class SmsMessageModel {
  final String address;
  final String body;
  final int dateMs;
  final String type;
  final double? spamScore;

  SmsMessageModel({
    required this.address,
    required this.body,
    required this.dateMs,
    required this.type,
    this.spamScore,
  });

  factory SmsMessageModel.fromJson(Map<String, dynamic> json) {
    return SmsMessageModel(
      address: json['address'] ?? '',
      body: json['body'] ?? '',
      dateMs: json['timestamp'] ?? json['date_ms'] ?? 0,
      type: json['type'] ?? 'inbox',
      spamScore: (json['spam_score'] is num)
          ? json['spam_score'].toDouble()
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
    "address": address,
    "body": body,
    "date_ms": dateMs,
    "type": type,
  };
}