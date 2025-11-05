import 'package:flutter/material.dart';

import '../models/sms_message.dart';

class SmsDetailedScreen extends StatelessWidget {
  final SmsMessageModel message;

  const SmsDetailedScreen({Key? key, required this.message}) : super(key: key);

  String getDisplayName(String address, String? contactName) {
    if (contactName != null && contactName.isNotEmpty) return contactName;
    final isBusinessSender = RegExp(r'[A-Za-z]').hasMatch(address);
    if (isBusinessSender) {
      return address.replaceAll(RegExp(r'^[A-Z]{2}-'), '');
    }
    return address;
  }

  @override
  Widget build(BuildContext context) {
    final sender = getDisplayName(message.address, null);
    final score = message.spamScore ?? 0.0;
    final isSpam = score >= 0.5;
    final bgColor = isSpam ? Colors.red.shade50 : Colors.green.shade50;
    final textColor = isSpam ? Colors.red.shade700 : Colors.green.shade700;
    final scoreColor = isSpam ? Colors.red.shade800 : Colors.green.shade800;

    final time = DateTime.fromMillisecondsSinceEpoch(message.dateMs).toLocal();
    final formattedTime =
        "${time.day}/${time.month}/${time.year} ${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}";

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 1,
        iconTheme: const IconThemeData(color: Colors.black),
        title: Text(
          "Message Details",
          style: const TextStyle(
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
                  backgroundColor: Colors
                      .primaries[sender.hashCode % Colors.primaries.length],
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
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: Text(
                message.body,
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
                    "Spam Score: ${score.toStringAsFixed(3)}",
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                      color: scoreColor,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Received at: $formattedTime",
                    style: TextStyle(color: Colors.grey.shade700, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Sender Address: ${message.address}",
                    style: TextStyle(color: Colors.grey.shade700, fontSize: 14),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            if (message.spamScore != null)
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
                          ? "This message is likely spam."
                          : "This message appears safe.",
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
