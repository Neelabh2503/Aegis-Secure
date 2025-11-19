class SmsMessageModel {
  final String address;
  final String body;
  final int dateMs;
  final String type;
  final double? spamScore;
  final double? confidence;
  final String? reasoning;
  final String? highlightedText;
  final String? finalDecision;
  final String? suggestion;

  SmsMessageModel({
    required this.address,
    required this.body,
    required this.dateMs,
    required this.type,
    this.spamScore,
    this.confidence,
    this.reasoning,
    this.highlightedText,
    this.finalDecision,
    this.suggestion,
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
      confidence: (json['confidence'] is num)
          ? json['confidence'].toDouble()
          : null,
      reasoning: json['reasoning'] ?? json['spam_reasoning'] ?? '',
      highlightedText:
          json['highlighted_text'] ?? json['spam_highlighted_text'] ?? '',
      finalDecision: json['final_decision'] ?? json['spam_verdict'] ?? '',
      suggestion: json['suggestion'] ?? json['spam_suggestion'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    "address": address,
    "body": body,
    "date_ms": dateMs,
    "type": type,
    "spam_score": spamScore,
    "confidence": confidence,
    "reasoning": reasoning,
    "highlighted_text": highlightedText,
    "final_decision": finalDecision,
    "suggestion": suggestion,
  };
}
