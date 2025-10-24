import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'api_service.dart';

class EmailMessage {
  final String sender;
  final String subject;
  final String snippet;

  EmailMessage({
    required this.sender,
    required this.subject,
    required this.snippet,
  });

  factory EmailMessage.fromJson(Map<String, dynamic> json) {
    return EmailMessage(
      sender: json['sender'] ?? 'Unknown Sender',
      subject: json['subject'] ?? 'No Subject',
      snippet: json['snippet'] ?? 'No snippet available...',
    );
  }
}

class GmailScreen extends StatefulWidget {
  const GmailScreen({Key? key}) : super(key: key);

  @override
  _GmailScreenState createState() => _GmailScreenState();
}

class _GmailScreenState extends State<GmailScreen> {
  List<EmailMessage> emails = [];
  String? currentUserName;
  bool _loading = true;
  bool _userLoading = true;
  Timer? _pollingTimer;
  late WebSocketChannel channel;
  final Random _random = Random();

  @override
  void initState() {
    super.initState();
    loadCurrentUser();
    loadEmails();
    connectWebSocket();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    channel.sink.close();
    super.dispose();
  }

  Future<void> loadCurrentUser() async {
    try {
      final user = await ApiService.instance.me();

      if (user.containsKey('error')) {
        print("⚠️ Failed to load user: ${user['error']}");
        setState(() => _userLoading = false);
      } else {
        setState(() {
          currentUserName = user['name'] ?? 'U';
          _userLoading = false;
        });
      }
    } catch (e) {
      print("⚠️ Failed to load user: $e");
      setState(() => _userLoading = false);
    }
  }

  void connectWebSocket() async {
    channel = WebSocketChannel.connect(
      Uri.parse('wss://aidyn-findable-greedily.ngrok-free.dev/ws/emails'),
    );

    channel.stream.listen(
          (event) async {
        final data = jsonDecode(event);
        if (data['new_email'] == true) {
          print("📩 New mail received → refreshing inbox");
          final refreshed = await _loadMockEmails();
          setState(() {
            emails = refreshed.map((e) => EmailMessage.fromJson(e)).toList();
          });
        }
      },
      onError: (err) => print("⚠️ WebSocket error: $err"),
      onDone: () {
        print("🔁 WS closed, retrying in 5s...");
        Future.delayed(const Duration(seconds: 5), connectWebSocket);
      },
    );
  }

  Future<List<Map<String, dynamic>>> _loadMockEmails() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return [
      {
        'sender': 'Google',
        'subject': 'Security Alert',
        'snippet': 'A new device signed into your account...'
      },
      {
        'sender': 'Vercel',
        'subject': 'Deployment Successful',
        'snippet': 'Your project "aegis-secure-frontend" was deployed!'
      },
      {
        'sender': 'GitHub',
        'subject': '[aegis-secure] A PR was merged',
        'snippet': 'Your pull request #12 "Fix login bug" was merged'
      },
    ];
  }

  Future<void> loadEmails() async {
    setState(() => _loading = true);
    final data = await _loadMockEmails();
    setState(() {
      emails = data.map((e) => EmailMessage.fromJson(e)).toList();
      _loading = false;
    });
  }

  Future<void> _handleManualInput() async {
    String inputText = '';
    final controller = TextEditingController();

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text("Manual Text Analysis"),
        content: TextField(
          controller: controller,
          maxLines: 3,
          decoration: const InputDecoration(
            hintText: "Enter text to get confidence score",
            border: OutlineInputBorder(),
          ),
          onChanged: (val) => inputText = val,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text("Analyzing text... (mocked for now)"),
                ),
              );
            },
            child: const Text("Submit"),
          ),
        ],
      ),
    );
  }

  Color _getRandomColor() {
    const colors = [
      Colors.red,
      Colors.blue,
      Colors.green,
      Colors.orange,
      Colors.purple,
      Colors.teal,
      Colors.amber,
      Colors.indigo,
      Colors.pink,
      Colors.brown,
    ];
    return colors[_random.nextInt(colors.length)];
  }

  void _startOauthFlow() {
    Navigator.pushNamed(context, '/oauth');
  }

  void _goToHome() {
    Navigator.pushNamedAndRemoveUntil(context, '/home', (route) => false);
  }

  void _goToChat() {
    Navigator.pushNamedAndRemoveUntil(context, '/chat', (route) => false);
  }

  @override
  Widget build(BuildContext context) {
    final firstLetter = (currentUserName != null && currentUserName!.isNotEmpty)
        ? currentUserName![0].toUpperCase()
        : '?';

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.menu, color: Colors.black87),
          onPressed: () {},
        ),
        title: const Text(
          "Inbox",
          style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
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
          if (_userLoading)
            const Padding(
              padding: EdgeInsets.only(right: 12.0),
              child: CircleAvatar(
                backgroundColor: Colors.grey,
                child: SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            )
          else
            Padding(
              padding: const EdgeInsets.only(right: 12.0),
              child: CircleAvatar(
                backgroundColor: Colors.purple.shade300,
                child: Text(
                  firstLetter,
                  style: const TextStyle(
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
          : emails.isEmpty
          ? const Center(child: Text("No emails found"))
          : RefreshIndicator(
        onRefresh: loadEmails,
        child: ListView.separated(
          itemCount: emails.length,
          separatorBuilder: (_, __) =>
          const Divider(height: 0, thickness: 0.3),
          itemBuilder: (context, index) {
            final email = emails[index];
            final avatarColor = _getRandomColor();

            return ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 8,
              ),
              leading: CircleAvatar(
                backgroundColor: avatarColor,
                child: Text(
                  email.sender.isNotEmpty
                      ? email.sender[0].toUpperCase()
                      : '?',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              title: Text(
                email.sender,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 15,
                ),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    email.subject.isEmpty
                        ? "(No Subject)"
                        : email.subject,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    email.snippet,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
              trailing: Column(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    width: 42,
                    height: 22,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    alignment: Alignment.center,
                    child: const Text(
                      "0.00",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                  ),
                  const Icon(
                    Icons.more_vert,
                    size: 20,
                    color: Colors.grey,
                  ),
                ],
              ),
            );
          },
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text("Mock Google Login: Function not in ApiService!"),
            ),
          );
        },
        backgroundColor: Colors.blueAccent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: const Icon(Icons.add, size: 28, color: Colors.white),
      ),
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
              const Icon(Icons.mail_outline, color: Colors.blue, size: 28),
              GestureDetector(
                onTap: _goToHome,
                child: const Icon(
                  Icons.home_outlined,
                  color: Colors.grey,
                  size: 28,
                ),
              ),
              GestureDetector(
                onTap: _goToChat,
                child: const Icon(
                  Icons.chat_bubble_outline,
                  color: Colors.grey,
                  size: 28,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}