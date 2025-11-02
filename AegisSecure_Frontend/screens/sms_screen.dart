import 'dart:async';

import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/sms_service.dart';
import '../widgets/sidebar.dart';

class SmsScreen extends StatefulWidget {
  const SmsScreen({Key? key}) : super(key: key);

  @override
  State<SmsScreen> createState() => _SmsScreenState();
}

class _SmsScreenState extends State<SmsScreen> {
  final SmsService _smsService = SmsService();
  void showDebug(String msg) {
    print("$msg");
    if (mounted && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(msg), duration: const Duration(seconds: 2)),
      );
    }
  }

  String getDisplayName(String address, String? contactName) {
    if (contactName != null && contactName.isNotEmpty) return contactName;
    final isBusinessSender = RegExp(r'[A-Za-z]').hasMatch(address);
    if (isBusinessSender) {
      return address.replaceAll(RegExp(r'^[A-Z]{2}-'), '');
    }
    return address;
  }

  List<Map<String, dynamic>> _messages = [];
  bool _loading = true;
  late StreamSubscription _smsStream;
  @override
  void initState() {
    super.initState();
    fetchLocalSMS();
    listenForIncomingMessages();
  }

  @override
  void dispose() {
    _smsStream.cancel();
    super.dispose();
  }

  void listenForIncomingMessages() {
    _smsStream = _smsService.onNewMessage.listen((message) async {
      await analyzeAndAddNewMessage(message);
    });
  }

  Future<void> analyzeAndAddNewMessage(Map<String, dynamic> msg) async {
    try {
      final response = await ApiService.analyzeText(msg['body']);
      final rawPrediction = response['prediction'];
      final score = double.tryParse(rawPrediction.toString()) ?? 0.0;

      setState(() {
        _messages.insert(0, {...msg, 'score': score});
      });
    } catch (e) {
      print("⚠️ Error analyzing new message: $e");
    }
  }

  Future<void> fetchLocalSMS() async {
    try {
      final smsList = await _smsService.getAllMessages();
      final analyzedMessages = <Map<String, dynamic>>[];

      for (final msg in smsList) {
        try {
          final response = await ApiService.analyzeText(msg['body']);
          final rawPrediction = response['prediction'];
          final score = double.tryParse(rawPrediction.toString()) ?? 0.0;
          analyzedMessages.add({...msg, 'score': score});
        } catch (_) {}
      }

      setState(() {
        _messages = analyzedMessages;
        _loading = false;
      });
    } catch (e) {
      print("❌ Failed to fetch SMS: $e");
      setState(() => _loading = false);
    }
  }

  Future<void> _handleManualInput() async {
    final controller = TextEditingController();
    String prediction = "";
    String confidence = "";

    await showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setStateDialog) => AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          elevation: 8,
          title: const Text(
            "Manual Text Analysis",
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade300),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black12,
                      blurRadius: 4,
                      offset: Offset(0, 2),
                    ),
                  ],
                ),
                child: TextField(
                  controller: controller,
                  maxLines: 4,
                  style: const TextStyle(fontSize: 16),
                  decoration: InputDecoration(
                    contentPadding: const EdgeInsets.symmetric(
                      vertical: 12,
                      horizontal: 16,
                    ),
                    hintText: "Enter text to analyze...",
                    hintStyle: TextStyle(color: Colors.grey.shade500),
                    border: InputBorder.none,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              if (prediction.isNotEmpty)
                Builder(
                  builder: (_) {
                    final isSpam = prediction == "SPAM";
                    final bgColor = isSpam
                        ? Colors.red.shade50
                        : Colors.green.shade50;
                    final textColor = isSpam
                        ? Colors.red.shade700
                        : Colors.green.shade700;

                    return Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: bgColor,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: isSpam
                              ? Colors.red.shade200
                              : Colors.green.shade200,
                        ),
                      ),
                      child: Column(
                        children: [
                          Text(
                            prediction,
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: textColor,
                              fontSize: 18,
                            ),
                          ),
                          if (confidence.isNotEmpty) const SizedBox(height: 6),
                          if (confidence.isNotEmpty)
                            Text(
                              "Confidence: $confidence",
                              style: TextStyle(color: textColor, fontSize: 14),
                            ),
                        ],
                      ),
                    );
                  },
                ),
            ],
          ),
          actionsPadding: const EdgeInsets.symmetric(
            horizontal: 12,
            vertical: 8,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              style: TextButton.styleFrom(
                foregroundColor: Colors.grey.shade700,
              ),
              child: const Text("Cancel"),
            ),
            ElevatedButton(
              onPressed: () async {
                final inputText = controller.text.trim();
                if (inputText.isEmpty) return;

                setStateDialog(() {
                  prediction = "Analyzing...";
                  confidence = "";
                });

                try {
                  final result = await ApiService.analyzeText(inputText);
                  print("DEBUG: Raw API Response = $result");

                  final confStr = result['prediction'] ?? "0.0";
                  final conf = double.tryParse(confStr) ?? 0.0;
                  final label = conf >= 0.5 ? "SPAM" : "HAM";

                  setStateDialog(() {
                    prediction = label;
                    confidence = conf.toStringAsFixed(2);
                    print(
                      "DEBUG: Classified label = $label with confidence = $confidence",
                    );
                  });
                } catch (e) {
                  setStateDialog(() {
                    prediction = "ERROR";
                    confidence = "";
                    print("DEBUG: Error fetching prediction = $e");
                  });
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue.shade600,
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                textStyle: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              child: const Text("Submit"),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageTile(Map<String, dynamic> msg) {
    final rawAddress = msg['address'] ?? 'Unknown';
    final contactName = msg['displayName'];
    final sender = getDisplayName(rawAddress, contactName);
    // final sender = msg['address'] ?? 'Unknown';
    final body = msg['body'] ?? '';
    final score = (msg['score'] ?? 0.0).toDouble();
    final date = msg['date'] ?? DateTime.now().millisecondsSinceEpoch;

    final time = DateTime.fromMillisecondsSinceEpoch(date).toLocal();
    final formattedTime =
        "${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}";

    final color = score >= 0.5 ? Colors.red.shade100 : Colors.green.shade100;
    final scoreTextColor = score >= 0.5
        ? Colors.red.shade800
        : Colors.green.shade800;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.shade200,
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Avatar
            CircleAvatar(
              backgroundColor:
                  Colors.primaries[sender.hashCode % Colors.primaries.length],
              child: Text(
                sender.isNotEmpty ? sender[0].toUpperCase() : "?",
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const SizedBox(width: 12),

            // Sender + message
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    sender,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                      color: Colors.black,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    body,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
                  ),
                ],
              ),
            ),
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    score.toStringAsFixed(2),
                    style: TextStyle(
                      color: scoreTextColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      formattedTime,
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(width: 20),
                    const Icon(Icons.more_vert, size: 18, color: Colors.grey),
                    const SizedBox(width: 13),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.menu, color: Colors.black87),
          onPressed: () {
            showGeneralDialog(
              context: context,
              barrierDismissible: true,
              barrierLabel: '',
              barrierColor: Colors.black54.withOpacity(0.3),
              transitionDuration: const Duration(milliseconds: 300),
              pageBuilder: (context, anim1, anim2) {
                return Align(
                  alignment: Alignment.centerLeft,
                  child: Sidebar(
                    onClose: () => Navigator.of(context).pop(),
                    onMessagesTap: () {
                      Navigator.of(context).pop(); // close sidebar
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text("You are already on Messages!"),
                        ),
                      );
                    },
                  ),
                );
              },
              transitionBuilder:
                  (context, animation, secondaryAnimation, child) {
                    return SlideTransition(
                      position:
                          Tween(
                            begin: const Offset(-1, 0),
                            end: Offset.zero,
                          ).animate(
                            CurvedAnimation(
                              parent: animation,
                              curve: Curves.easeOutCubic,
                            ),
                          ),
                      child: child,
                    );
                  },
            );
          },
        ),
        title: const Text(
          "SMS Home Page",
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.add, color: Colors.black87),
            tooltip: "Manual text input",
            onPressed: _handleManualInput,
          ),
          IconButton(
            icon: const Icon(Icons.search, color: Colors.black87),
            onPressed: () {},
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _messages.isEmpty
          ? const Center(child: Text("No messages found"))
          : RefreshIndicator(
              onRefresh: fetchLocalSMS,
              child: ListView.separated(
                itemCount: _messages.length,
                separatorBuilder: (_, __) =>
                    const Divider(height: 0, thickness: 0.3),
                itemBuilder: (context, index) =>
                    _buildMessageTile(_messages[index]),
              ),
            ),
    );
  }
}
