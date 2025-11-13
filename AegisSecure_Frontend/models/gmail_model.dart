class EmailMessage {
  final String sender;
  final String fromEmail;
  final String subject;
  final String snippet;
  final String body;
  final String spamReasoning;
  final String spamSuggestion;
  final String spamVerdict;
  final String spamHighlightedText;
  final DateTime timestamp;
  final String charColor;
  final String spamPrediction;
  final String gmailId;
  final String userId;
  final String lastHistoryId;

  EmailMessage({
    required this.sender,
    required this.fromEmail,
    required this.subject,
    required this.snippet,
    required this.body,
    required this.spamReasoning,
    required this.spamSuggestion,
    required this.spamVerdict,
    required this.spamHighlightedText,
    required this.timestamp,
    required this.charColor,
    required this.spamPrediction,
    required this.gmailId,
    required this.userId,
    required this.lastHistoryId,
  });

  factory EmailMessage.fromJson(Map<String, dynamic> json) {
    int ms = 0;
    try {
      ms = json['timestamp'] is int
          ? json['timestamp']
          : int.tryParse(json['timestamp'].toString()) ??
                DateTime.now().millisecondsSinceEpoch;
    } catch (_) {
      ms = DateTime.now().millisecondsSinceEpoch;
    }

    final spamPredictionValue = json['spam_prediction'];
    final spamPredictionStr = spamPredictionValue != null
        ? spamPredictionValue.toString()
        : (json['prediction']?.toString() ?? "0");

    return EmailMessage(
      sender: json['from'] ?? json['sender'] ?? '',
      fromEmail: json['from_email'] ?? '',
      subject: json['subject'] ?? '',
      snippet: json['snippet'] ?? '',
      body: json['body'] ?? '',
      spamReasoning: json['spam_reasoning'] ?? '',
      spamSuggestion: json['spam_suggestion'] ?? '',
      spamVerdict: json['spam_verdict'] ?? '',
      spamHighlightedText: json['spam_highlighted_text'] ?? '',
      timestamp: DateTime.fromMillisecondsSinceEpoch(ms, isUtc: true).toLocal(),
      charColor: json['char_color'] ?? '#90A4AE',
      spamPrediction: spamPredictionStr,
      gmailId: json['gmail_id'] ?? '',
      userId: json['user_id'] ?? '',
      lastHistoryId: json['last_history_id'] ?? '',
    );
  }
}
