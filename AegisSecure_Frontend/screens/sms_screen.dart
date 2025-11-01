import 'dart:async';
import 'dart:math'; 
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/sms_service.dart';

class SmsScreen extends StatefulWidget {
  const SmsScreen({Key? key}) : super(key: key);

  @override
  State<SmsScreen> createState() => _SmsScreenState();
}

class _SmsScreenState extends State<SmsScreen> {
  final SmsService _smsService = SmsService();
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

  void showDebug(String msg) {
    print(msg);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(msg), duration: const Duration(seconds: 2)),
      );
    }
  }

  String getDisplayName(String address, String? contactName) {
    if (contactName != null && contactName.isNotEmpty) return contactName;
    final isBusiness = RegExp(r'[A-Za-z]').hasMatch(address);
    if (isBusiness) return address.replaceAll(RegExp(r'^[A-Z]{2}-'), '');
    return address;
  }

  void listenForIncomingMessages() {
    _smsStream = _smsService.onNewMessage.listen((msg) async {
      await analyzeAndAddNewMessage(msg);
    });
  }

  Future<void> analyzeAndAddNewMessage(Map<String, dynamic> msg) async {
    try {
      final res = await ApiService.analyzeText(msg['body']);
      final score = double.tryParse(res['prediction'].toString()) ?? 0.0;
      setState(() => _messages.insert(0, {...msg, 'score': score}));
    } catch (e) {
      print("Error analyzing message: $e");
      // Add message with default score if analysis fails
      setState(() => _messages.insert(0, {...msg, 'score': 0.0}));
    }
  }

  
  Future<void> fetchLocalSMS() async {
    setState(() => _loading = true); // Start loading
    try {
      final smsList = await _smsService.getAllMessages(limit: 50); // Get latest 50
      final analyzed = <Map<String, dynamic>>[];

      for (final msg in smsList) {
        try {
          final res = await ApiService.analyzeText(msg['body']);
          final score = double.tryParse(res['prediction'].toString()) ?? 0.0;
          analyzed.add({...msg, 'score': score});
        } catch (e) {
         
          // Making the print statement safe by checking string length
          final body = msg['body'] ?? '';
        
          final preview = body.substring(0, min<int>(body.length, 20)); // Get first 20 chars, or less
          print("Analysis failed for msg: $preview... Error: $e");

          analyzed.add({...msg, 'score': 0.0});
          
        }
      }
      setState(() {
        _messages = analyzed;
        _loading = false;
      });
    } catch (e) {
      print("Failed to fetch SMS: $e");
      setState(() => _loading = false);
    }
  }
  

  Future<void> _handleManualInput() async {
    final controller = TextEditingController();
    String prediction = "", confidence = "";

    await showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setStateDialog) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Text("Manual Text Analysis",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: TextField(
                  controller: controller,
                  maxLines: 4,
                  style: const TextStyle(fontSize: 16),
                  decoration: InputDecoration(
                    contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                    hintText: "Enter text to analyze...",
                    border: InputBorder.none,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              if (prediction.isNotEmpty)
                Builder(builder: (_) {
                  final isSpam = prediction == "SPAM";
                  final bg = isSpam ? Colors.red.shade50 : Colors.green.shade50;
                  final tc = isSpam ? Colors.red.shade700 : Colors.green.shade700;
                  return Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: bg,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: isSpam ? Colors.red.shade200 : Colors.green.shade200),
                    ),
                    child: Column(
                      children: [
                        Text(prediction,
                            style: TextStyle(fontWeight: FontWeight.bold, color: tc, fontSize: 18)),
                        if (confidence.isNotEmpty) const SizedBox(height: 6),
                        if (confidence.isNotEmpty)
                          Text("Confidence: $confidence", style: TextStyle(color: tc, fontSize: 14)),
                      ],
                    ),
                  );
                }),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              style: TextButton.styleFrom(foregroundColor: Colors.grey.shade700),
              child: const Text("Cancel"),
            ),
            ElevatedButton(
              onPressed: () async {
                final input = controller.text.trim();
                if (input.isEmpty) return;
                setStateDialog(() {
                  prediction = "Analyzing...";
                  confidence = "";
                });
                try {
                  final result = await ApiService.analyzeText(input);
                  final conf = double.tryParse(result['prediction'] ?? "0") ?? 0.0;
                  final label = conf >= 0.5 ? "SPAM" : "HAM";
                  setStateDialog(() {
                    prediction = label;
                    confidence = conf.toStringAsFixed(2);
                  });
                } catch (e) {
                  setStateDialog(() {
                    prediction = "ERROR";
                    confidence = "";
                  });
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue.shade600,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              child: const Text("Submit"),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageTile(Map<String, dynamic> msg) {
    final sender = getDisplayName(msg['address'] ?? 'Unknown', msg['displayName']);
    final body = msg['body'] ?? '';
    final score = (msg['score'] ?? 0.0).toDouble();
    final date = msg['date'] ?? DateTime.now().millisecondsSinceEpoch;
    final time = DateTime.fromMillisecondsSinceEpoch(date).toLocal();
    final formattedTime =
        "${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}";
    final color = score >= 0.5 ? Colors.red.shade100 : Colors.green.shade100;
    final scoreColor = score >= 0.5 ? Colors.red.shade800 : Colors.green.shade800;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        boxShadow: [BoxShadow(color: Colors.grey.shade200, blurRadius: 4, offset: const Offset(0, 2))],
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              backgroundColor: Colors.primaries[sender.hashCode % Colors.primaries.length],
              child: Text(sender.isNotEmpty ? sender[0].toUpperCase() : "?",
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(sender,
                      style: const TextStyle(
                          fontWeight: FontWeight.bold, fontSize: 15, color: Colors.black)),
                  const SizedBox(height: 2),
                  Text(body,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: Colors.grey.shade700, fontSize: 13)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(10)),
                  child: Text(score.toStringAsFixed(2),
                      style: TextStyle(color: scoreColor, fontWeight: FontWeight.bold, fontSize: 13)),
                ),
                const SizedBox(height: 6),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(formattedTime,
                        style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
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
        leading: IconButton(icon: const Icon(Icons.menu, color: Colors.black87), onPressed: () {}),
        title: const Text("SMS Home Page",
            style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold, fontSize: 18)),
        actions: [
          IconButton(icon: const Icon(Icons.add, color: Colors.black87), onPressed: _handleManualInput),
          IconButton(icon: const Icon(Icons.search, color: Colors.black87), onPressed: () {}),
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
          separatorBuilder: (_, __) => const Divider(height: 0, thickness: 0.3),
          itemBuilder: (context, i) => _buildMessageTile(_messages[i]),
        ),
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [BoxShadow(color: Colors.grey.shade300, blurRadius: 6, offset: const Offset(0, -2))],
          borderRadius: const BorderRadius.only(topLeft: Radius.circular(10), topRight: Radius.circular(10)),
        ),
        child: SafeArea(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              GestureDetector(
                onTap: () => Navigator.pushNamed(context, '/gmail'),
                child: const Icon(Icons.mail_outline, color: Colors.grey, size: 28),
              ),
              GestureDetector(
                onTap: () => Navigator.pushNamed(context, '/home'),
                child: const Icon(Icons.home_outlined, color: Colors.grey, size: 28),
              ),
              const Icon(Icons.sms_outlined, color: Colors.blue, size: 28),
            ],
          ),
        ),
      ),
    );
  }
}

