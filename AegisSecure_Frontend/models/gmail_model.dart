class EmailMessage {
  final String sender;
  final String subject;
  final String snippet;
  final DateTime timestamp;
  final String? spamPrediction; 

  EmailMessage({
    required this.sender,
    required this.subject,
    required this.snippet,
    required this.timestamp,
    this.spamPrediction,
  });

  factory EmailMessage.fromJson(Map<String, dynamic> json) {
    int ms = json['timestamp'] ?? DateTime.now().millisecondsSinceEpoch;
    return EmailMessage(
      sender: json['sender'] ?? json['from'] ?? '',
      subject: json['subject'] ?? '',
      snippet: json['snippet'] ?? '',
      timestamp: DateTime.fromMillisecondsSinceEpoch(ms, isUtc: true).toLocal(),
      spamPrediction:
          json['spam_prediction'] ?? json['prediction'] ?? "unknown", 
    );
  }
}
