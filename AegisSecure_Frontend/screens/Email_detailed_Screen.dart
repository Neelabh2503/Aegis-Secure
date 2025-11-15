import 'package:flutter/material.dart';

import '../models/gmail_model.dart';

class EmailDetailScreen extends StatelessWidget {
  final EmailMessage email;
  const EmailDetailScreen({Key? key, required this.email}) : super(key: key);

  Color _parseColor(String hexColor) {
    try {
      hexColor = hexColor.replaceAll("#", "");
      if (hexColor.length == 6) hexColor = "FF$hexColor";
      return Color(int.parse(hexColor, radix: 16));
    } catch (_) {
      return Colors.grey.shade400;
    }
  }

  List<TextSpan> _highlightedText(
    String text,
    TextStyle normal,
    TextStyle highlight,
  ) {
    final List<TextSpan> spans = [];
    int last = 0;
    final regex = RegExp(r'\$(.*?)\$');
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

  @override
  Widget build(BuildContext context) {
    final spamScore = double.tryParse(email.spamPrediction ?? '0') ?? 0.0;
    final scoreBckColors = [
      Color(0xFF27AE60),
      Color(0xFFF39C12),
      Color(0xFFE67E22),
      Color(0xFFE74C3C),
    ];
    Color scoreBckColor;
    if (spamScore < 25) {
      scoreBckColor = scoreBckColors[0];
    } else if (spamScore < 50) {
      scoreBckColor = scoreBckColors[1];
    } else if (spamScore < 75) {
      scoreBckColor = scoreBckColors[2];
    } else {
      scoreBckColor = scoreBckColors[3];
    }

    final date = email.timestamp;
    final formattedDate =
        "${date.day}/${date.month}/${date.year} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}";

    final normalStyle =
        Theme.of(context).textTheme.bodyLarge?.copyWith(
          color: Colors.black87,
          height: 1.6,
          fontSize: 17,
        ) ??
        const TextStyle(color: Colors.black87, fontSize: 17, height: 1.6);

    final highlightStyle = normalStyle.copyWith(
      color: Colors.black,
      backgroundColor: Colors.red.shade50,
      fontWeight: FontWeight.w600,
    );

    return Scaffold(
      backgroundColor: Colors.white,
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            pinned: true,
            backgroundColor: Colors.white,
            foregroundColor: Colors.black87,
            elevation: 1,
            title: Text(
              email.subject.isNotEmpty ? email.subject : "(No Subject)",
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: Colors.black87,
                fontWeight: FontWeight.bold,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16.0),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CircleAvatar(
                      radius: 28,
                      backgroundColor: _parseColor(
                        email.charColor ?? '#888888',
                      ),
                      child: Text(
                        email.sender.isNotEmpty
                            ? email.sender[0].toUpperCase()
                            : "?",
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 24,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            email.sender.isNotEmpty
                                ? email.sender
                                : "(Unknown Sender)",
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 18,
                                ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            email.fromEmail.isNotEmpty
                                ? email.fromEmail
                                : "(No Email)",
                            style: Theme.of(context).textTheme.bodyMedium
                                ?.copyWith(
                                  color: Colors.grey.shade600,
                                  fontSize: 14,
                                ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Container(
                          width: 70,
                          padding: const EdgeInsets.symmetric(
                            vertical: 7,
                            horizontal: 4,
                          ),
                          decoration: BoxDecoration(
                            color: scoreBckColor.withOpacity(0.07),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Column(
                            children: [
                              Text(
                                spamScore.toStringAsFixed(1),
                                style: TextStyle(
                                  color: scoreBckColor,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 17,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          formattedDate,
                          style: const TextStyle(
                            fontSize: 13,
                            color: Colors.grey,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: scoreBckColor.withOpacity(0.09),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        email.spamVerdict.toLowerCase().contains("spam")
                            ? Icons.warning_amber_rounded
                            : Icons.check_circle_outline,
                        size: 28,
                        color: scoreBckColor,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          email.spamVerdict.isNotEmpty
                              ? "Verdict: ${email.spamVerdict}"
                              : "No verdict available.",
                          style: TextStyle(
                            color: scoreBckColor,
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                RichText(
                  text: TextSpan(
                    children: _highlightedText(
                      email.spamHighlightedText.isNotEmpty
                          ? email.spamHighlightedText
                          : email.body,
                      normalStyle,
                      highlightStyle,
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                if ((email.spamReasoning ?? '').isNotEmpty)
                  _buildSectionHeader(context, "Reasoning", "🧠"),
                if ((email.spamReasoning ?? '').isNotEmpty)
                  const Divider(thickness: 0.5, height: 16),
                if ((email.spamReasoning ?? '').isNotEmpty)
                  RichText(
                    text: TextSpan(
                      children: _highlightedText(
                        email.spamReasoning!,
                        normalStyle.copyWith(fontSize: 15),
                        highlightStyle.copyWith(fontSize: 15),
                      ),
                    ),
                  ),
                if ((email.spamSuggestion ?? '').isNotEmpty)
                  _buildSectionHeader(context, "Suggestion", "💡"),
                if ((email.spamSuggestion ?? '').isNotEmpty)
                  const Divider(thickness: 0.5, height: 16),
                if ((email.spamSuggestion ?? '').isNotEmpty)
                  RichText(
                    text: TextSpan(
                      children: _highlightedText(
                        email.spamSuggestion!,
                        normalStyle.copyWith(fontSize: 15),
                        highlightStyle.copyWith(fontSize: 15),
                      ),
                    ),
                  ),
                const SizedBox(height: 48),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(BuildContext context, String title, String icon) {
    return Padding(
      padding: const EdgeInsets.only(top: 16.0),
      child: Row(
        children: [
          Text(icon, style: const TextStyle(fontSize: 22)),
          const SizedBox(width: 8),
          Text(
            title,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
