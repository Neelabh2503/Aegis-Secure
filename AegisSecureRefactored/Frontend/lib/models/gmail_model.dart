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

  const EmailMessage({
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

  /// Create EmailMessage from JSON
  factory EmailMessage.fromJson(Map<String, dynamic> json) {
    // Parse timestamp
    int ms = 0;
    try {
      ms = json['timestamp'] is int
          ? json['timestamp']
          : int.tryParse(json['timestamp'].toString()) ??
              DateTime.now().millisecondsSinceEpoch;
    } catch (_) {
      ms = DateTime.now().millisecondsSinceEpoch;
    }

    // Parse spam prediction
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

  /// Convert EmailMessage to JSON
  Map<String, dynamic> toJson() {
    return {
      'from': sender,
      'from_email': fromEmail,
      'subject': subject,
      'snippet': snippet,
      'body': body,
      'spam_reasoning': spamReasoning,
      'spam_suggestion': spamSuggestion,
      'spam_verdict': spamVerdict,
      'spam_highlighted_text': spamHighlightedText,
      'timestamp': timestamp.millisecondsSinceEpoch,
      'char_color': charColor,
      'spam_prediction': spamPrediction,
      'gmail_id': gmailId,
      'user_id': userId,
      'last_history_id': lastHistoryId,
    };
  }

  /// Create a copy with modified fields
  EmailMessage copyWith({
    String? sender,
    String? fromEmail,
    String? subject,
    String? snippet,
    String? body,
    String? spamReasoning,
    String? spamSuggestion,
    String? spamVerdict,
    String? spamHighlightedText,
    DateTime? timestamp,
    String? charColor,
    String? spamPrediction,
    String? gmailId,
    String? userId,
    String? lastHistoryId,
  }) {
    return EmailMessage(
      sender: sender ?? this.sender,
      fromEmail: fromEmail ?? this.fromEmail,
      subject: subject ?? this.subject,
      snippet: snippet ?? this.snippet,
      body: body ?? this.body,
      spamReasoning: spamReasoning ?? this.spamReasoning,
      spamSuggestion: spamSuggestion ?? this.spamSuggestion,
      spamVerdict: spamVerdict ?? this.spamVerdict,
      spamHighlightedText: spamHighlightedText ?? this.spamHighlightedText,
      timestamp: timestamp ?? this.timestamp,
      charColor: charColor ?? this.charColor,
      spamPrediction: spamPrediction ?? this.spamPrediction,
      gmailId: gmailId ?? this.gmailId,
      userId: userId ?? this.userId,
      lastHistoryId: lastHistoryId ?? this.lastHistoryId,
    );
  }

  /// Check if email is likely spam based on prediction score
  bool get isSpam {
    try {
      final score = double.tryParse(spamPrediction) ?? 0.0;
      return score > 0.5;
    } catch (_) {
      return false;
    }
  }

  /// Get spam confidence percentage
  double get spamConfidence {
    try {
      return (double.tryParse(spamPrediction) ?? 0.0) * 100;
    } catch (_) {
      return 0.0;
    }
  }

  @override
  String toString() => 'EmailMessage(from: $sender, subject: $subject, timestamp: $timestamp)';
}
