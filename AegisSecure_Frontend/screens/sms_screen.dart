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
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _loadMessages();
  }

  // NAVIGATION METHODS
  void _goToHome() {
    Navigator.pushNamedAndRemoveUntil(context, '/home', (route) => false);
  }

  void _goToGmail() {
    Navigator.pushNamedAndRemoveUntil(context, '/gmail', (route) => false);
  }


  // Load local SMS messages
  Future<void> _loadMessages() async {
    setState(() => _loading = true);
    try {
      final messages = await _smsService.fetchLocalSms();
      setState(() => _messages = messages);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error loading SMS: $e")),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  // Sync SMS to backend
  Future<void> _syncMessages() async {
    setState(() => _loading = true);

    final token = await ApiService.getToken();
    final backendUrl = ApiService.baseUrl;

    if (token == null || backendUrl.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Missing API token or backend URL")),
      );
      setState(() => _loading = false);
      return;
    }

    try {
      await _smsService.syncSmsToBackend(token, backendUrl);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Messages synced successfully!"),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error syncing SMS: $e")),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  // Shows the full message body in a pop-up dialog.
  Future<void> _showFullMessageDialog(Map<String, dynamic> msg) async {
    return showDialog<void>(
      context: context,
      barrierDismissible: true, // User can tap outside the dialog to close
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          title: Text(msg['address'] ?? 'Unknown Sender'),
          content: SingleChildScrollView(
            child: Text(msg['body'] ?? 'No Content'),
          ),
          actions: <Widget>[
            TextButton(
              child: const Text('Close'),
              onPressed: () {
                Navigator.of(dialogContext).pop(); // Close the dialog
              },
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      //  UPDATED APPBAR
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.menu, color: Colors.black87),
          onPressed: () {
            // TODO: Add logic to open a navigation drawer
          },
        ),
        title: const Text(
          "SMS Inbox",
          style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
        ),
        actions: [
          // Action from gmail_screen
          IconButton(
            icon: const Icon(Icons.search, color: Colors.black87),
            onPressed: () {},
          ),
          // Action from sms_screen
          IconButton(
            icon: const Icon(Icons.sync, color: Colors.black87),
            tooltip: "Sync with backend",
            onPressed: _loading ? null : _syncMessages,
          ),
          // Avatar from gmail_screen
          Padding(
            padding: const EdgeInsets.only(right: 12.0),
            child: CircleAvatar(
              backgroundColor: Colors.purple,
              child: const Text(
                "?",
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        ],
      ),

      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _messages.isEmpty
          ? const Center(
        child: Text(
          "No SMS messages found.",
          style: TextStyle(fontSize: 16, color: Colors.grey),
        ),
      )
          : ListView.builder(
        itemCount: _messages.length,
        itemBuilder: (context, index) {
          final msg = _messages[index];
          return Card(
            margin: const EdgeInsets.symmetric(
                horizontal: 12, vertical: 6),
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
            child: ListTile(
              leading: const Icon(Icons.message,
                  color: Colors.blueAccent),
              title: Text(
                msg['address'] ?? "Unknown Sender",
                style: const TextStyle(
                    fontWeight: FontWeight.bold, fontSize: 16),
              ),
              subtitle: Text(
                msg['body'] ?? "",
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              trailing: Text(
                msg['date'] != null
                    ? DateTime.fromMillisecondsSinceEpoch(
                    msg['date'])
                    .toLocal()
                    .toString()
                    .substring(0, 16)
                    : '',
                style:
                const TextStyle(fontSize: 12, color: Colors.grey),
              ),
              onTap: () {
                _showFullMessageDialog(msg);
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _loading ? null : _loadMessages,
        tooltip: "Refresh messages",
        backgroundColor: Colors.blue,
        child: const Icon(Icons.refresh),
      ),

      // BOTTOM NAVIGATION BAR
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.grey.shade300,
              blurRadius: 6,
              offset: const Offset(0, -2),
            ),
          ],
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(10),
            topRight: Radius.circular(10),
          ),
        ),
        child: SafeArea(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              // Gmail
              GestureDetector(
                onTap: _goToGmail,
                child: const Icon(
                  Icons.mail_outline,
                  color: Colors.grey,
                  size: 28,
                ),
              ),

              // Home
              GestureDetector(
                onTap: _goToHome,
                child: const Icon(
                  Icons.home_outlined,
                  color: Colors.grey,
                  size: 28,
                ),
              ),

              // SMS (Active)
              const Icon(
                Icons.sms_outlined,
                color: Colors.blue, // Active here
                size: 28,
              ),
            ],
          ),
        ),
      ),

    );
  }
}

