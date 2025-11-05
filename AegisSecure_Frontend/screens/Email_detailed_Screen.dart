import 'package:flutter/material.dart';
import '../models/gmail_model.dart';

class EmailDetailScreen extends StatelessWidget 
{
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

  @override
  Widget build(BuildContext context) {
    final spamScore = double.tryParse(email.spamPrediction ?? '0') ?? 0.0;
    final isSpam = spamScore >= 0.5;
    final bgColor = isSpam ? Colors.red.shade50 : Colors.green.shade50;
    final textColor = isSpam ? Colors.red.shade700 : Colors.green.shade700;
    final scoreColor = isSpam ? Colors.red.shade800 : Colors.green.shade800;

    final date = email.timestamp;
    final formattedDate =
        "${date.day}/${date.month}/${date.year} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}";

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 1,
        iconTheme: const IconThemeData(color: Colors.black),
        title: const Text(
          "Email Details",
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
      ),
      backgroundColor: Colors.white,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 26,
                  backgroundColor: _parseColor(email.charColor),
                  child: Text(
                    email.sender.isNotEmpty
                        ? email.sender[0].toUpperCase()
                        : "?",
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
                    email.sender,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: bgColor,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: textColor.withOpacity(0.3)),
                  ),
                  child: Text(
                    isSpam ? "SPAM" : "HAM",
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: textColor,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Text(
              email.subject.isEmpty ? "(No Subject)" : email.subject,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: Text(
                email.snippet.isEmpty
                    ? "(No content available)"
                    : email.snippet,
                style: const TextStyle(
                  fontSize: 16,
                  height: 1.4,
                  color: Colors.black87,
                ),
              ),
            ),
            const SizedBox(height: 20),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.grey.shade200,
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Spam Score: ${spamScore.toStringAsFixed(3)}",
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                      color: scoreColor,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Received at: $formattedDate",
                    style: TextStyle(color: Colors.grey.shade700, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "From: ${email.sender}",
                    style: TextStyle(color: Colors.grey.shade700, fontSize: 14),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            Center(
              child: Column(
                children: [
                  Icon(
                    isSpam ? Icons.warning_amber_rounded : Icons.check_circle,
                    size: 48,
                    color: textColor,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    isSpam
                        ? "This email is likely spam."
                        : "This email appears safe.",
                    style: TextStyle(
                      color: textColor,
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
