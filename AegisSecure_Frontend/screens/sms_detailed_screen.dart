import 'package:flutter/material.dart';

import '../models/sms_message.dart';

class SmsDetailedScreen extends StatelessWidget {
  final SmsMessageModel message;
  Color generateColorFromString(String input) {
    final colors = [
      Colors.red,
      Colors.blue,
      Colors.green,
      Colors.orange,
      Colors.purple,
      Colors.teal,
      Colors.brown,
      Colors.indigo,
    ];
    final hash = input.hashCode;
    final index = hash % colors.length;
    return colors[index];
  }

  const SmsDetailedScreen({Key? key, required this.message}) : super(key: key);
  String getDisplayName(String address, String? contactName) {
    if (contactName != null && contactName.isNotEmpty) return contactName;
    final isBusinessSender = RegExp(r'[A-Za-z]').hasMatch(address);
    if (isBusinessSender) {
      return address.replaceAll(RegExp(r'^[A-Z]{2}-'), '');
    }
    return address;
  }

  List<TextSpan> highlitedText(
    String text,
    TextStyle normal,
    TextStyle highlight,
  ) {
    final List<TextSpan> spans = [];
    int last = 0;
    final regex = RegExp(r'\@\@(.*?)\@\@');
    final matches = regex.allMatches(text);
    for (final match in matches) {
      if (match.start > last) {
        spans.add(
          TextSpan(text: text.substring(last, match.start), style: normal),
        );
      }
      spans.add(TextSpan(text: match.group(1), style: highlight));
      last = match.end;
    }
    if (last < text.length) {
      spans.add(TextSpan(text: text.substring(last), style: normal));
    }
    return spans;
  }

  Color parseColor(String hexColor) {
    try {
      hexColor = hexColor.replaceAll("#", "");
      if (hexColor.length == 6) hexColor = "FF$hexColor";
      return Color(int.parse(hexColor, radix: 16));
    } catch (_) {
      return Colors.grey.shade400;
    }
  }

  Color scoreBckClr(double score) {
    if (score < 25) return const Color(0xFF27AE60);
    if (score < 50) return const Color(0xFFF39C12);
    if (score < 75) return const Color(0xFFE67E22);
    return const Color(0xFFE74C3C);
  }

  Widget buildSectionHeader(BuildContext context, String title, String icon) {
    return Padding(
      padding: const EdgeInsets.only(top: 24, bottom: 8),
      child: Row(
        children: [
          Text(icon, style: const TextStyle(fontSize: 24)),
          const SizedBox(width: 10),
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final sender = getDisplayName(message.address, null);
    final score = message.spamScore ?? 0.0;
    final badgeColor = scoreBckClr(score);
    final isSpam = score >= 0.5;
    final time = DateTime.fromMillisecondsSinceEpoch(message.dateMs).toLocal();
    final formattedDate =
        "${time.day.toString().padLeft(2, '0')}/${time.month.toString().padLeft(2, '0')}/${time.year} ${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}";

    final normalStyle =
        Theme.of(context).textTheme.bodyLarge?.copyWith(
          color: Colors.black87,
          fontSize: 16,
          height: 1.5,
        ) ??
        const TextStyle(color: Colors.black87, fontSize: 16, height: 1.5);

    final highlightStyle = normalStyle.copyWith(
      color: Colors.black,
      backgroundColor: Colors.red.shade50,
      fontWeight: FontWeight.w600,
    );

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 1,
        iconTheme: const IconThemeData(color: Colors.black87),
        title: const Text(
          "Message Details",
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: message.address.isNotEmpty
                      ? generateColorFromString(message.address)
                      : Colors.grey.shade400,
                  child: Text(
                    sender.isNotEmpty ? sender[0].toUpperCase() : "?",
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 20,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    sender,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 12),
                Column(
                  children: [
                    Container(
                      width: 70,
                      padding: const EdgeInsets.symmetric(
                        vertical: 8,
                        horizontal: 4,
                      ),
                      decoration: BoxDecoration(
                        color: badgeColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        score.toStringAsFixed(1),
                        style: TextStyle(
                          color: badgeColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      formattedDate,
                      style: const TextStyle(fontSize: 13, color: Colors.grey),
                    ),
                  ],
                ),
              ],
            ),

            const SizedBox(height: 22),
            Container(
              padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
              width: double.infinity,
              decoration: BoxDecoration(
                color: badgeColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  Icon(
                    isSpam ? Icons.warning_amber_rounded : Icons.check_circle,
                    color: badgeColor,
                    size: 28,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      message.finalDecision?.isNotEmpty == true
                          ? "Verdict: ${message.finalDecision}"
                          : "No verdict available",
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 17,
                        color: badgeColor,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            RichText(
              text: TextSpan(
                children: highlitedText(
                  (message.highlightedText?.isNotEmpty ?? false)
                      ? message.highlightedText!
                      : (message.body ?? ""),
                  normalStyle,
                  highlightStyle,
                ),
              ),
            ),

            if (message.reasoning?.isNotEmpty == true) ...[
              buildSectionHeader(context, "Reasoning", "🧠"),
              const SizedBox(height: 6),
              Text(message.reasoning!, style: normalStyle),
            ],

            if (message.suggestion?.isNotEmpty == true) ...[
              buildSectionHeader(context, "Suggestion", "💡"),
              const SizedBox(height: 6),
              Text(message.suggestion!, style: normalStyle),
            ],
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}
