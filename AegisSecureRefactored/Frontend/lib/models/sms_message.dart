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

  const SmsMessageModel({
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
      spamScore: _parseDouble(json['spam_score']),
      confidence: _parseDouble(json['confidence']),
      reasoning: json['reasoning'] ?? json['spam_reasoning'] ?? '',
      highlightedText: json['highlighted_text'] ?? json['spam_highlighted_text'] ?? '',
      finalDecision: json['final_decision'] ?? json['spam_verdict'] ?? '',
      suggestion: json['suggestion'] ?? json['spam_suggestion'] ?? '',
    );
  }

  /// Parse value to double
  static double? _parseDouble(dynamic value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();
    if (value is String) return double.tryParse(value);
    return null;
  }

  /// Convert SmsMessageModel to JSON
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

  /// Create a copy with modified fields
  SmsMessageModel copyWith({
    String? address,
    String? body,
    int? dateMs,
    String? type,
    double? spamScore,
    double? confidence,
    String? reasoning,
    String? highlightedText,
    String? finalDecision,
    String? suggestion,
  }) {
    return SmsMessageModel(
      address: address ?? this.address,
      body: body ?? this.body,
      dateMs: dateMs ?? this.dateMs,
      type: type ?? this.type,
      spamScore: spamScore ?? this.spamScore,
      confidence: confidence ?? this.confidence,
      reasoning: reasoning ?? this.reasoning,
      highlightedText: highlightedText ?? this.highlightedText,
      finalDecision: finalDecision ?? this.finalDecision,
      suggestion: suggestion ?? this.suggestion,
    );
  }

  /// Get timestamp as DateTime
  DateTime get timestamp =>
      DateTime.fromMillisecondsSinceEpoch(dateMs, isUtc: true).toLocal();

  /// Check if SMS is likely spam
  bool get isSpam {
    if (spamScore != null) return spamScore! > 0.5;
    if (finalDecision != null) {
      return finalDecision!.toLowerCase().contains('spam') ||
          finalDecision!.toLowerCase().contains('malicious');
    }
    return false;
  }

  /// Get spam confidence percentage
  double get spamConfidencePercent {
    if (spamScore != null) return spamScore! * 100;
    if (confidence != null) return confidence!;
    return 0.0;
  }

  /// Check if message is from inbox (received)
  bool get isInbox => type.toLowerCase() == 'inbox';

  /// Check if message is sent
  bool get isSent => type.toLowerCase() == 'sent';

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is SmsMessageModel &&
          runtimeType == other.runtimeType &&
          address == other.address &&
          body == other.body &&
          dateMs == other.dateMs;

  @override
  int get hashCode => address.hashCode ^ body.hashCode ^ dateMs.hashCode;

  @override
  String toString() =>
      'SmsMessageModel(address: $address, body: ${body.substring(0, body.length > 20 ? 20 : body.length)}..., dateMs: $dateMs)';
}
