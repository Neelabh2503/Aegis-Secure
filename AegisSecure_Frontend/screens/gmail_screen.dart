import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../models/gmail_model.dart';
import '../services/api_service.dart';

class GmailScreen extends StatefulWidget {
  const GmailScreen({Key? key}) : super(key: key);

  @override
  _GmailScreenState createState() => _GmailScreenState();
}

class _GmailScreenState extends State<GmailScreen> {
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await loadConnectedAccounts();
      await loadEmails();
    });
  }

  List<String> connectedAccounts = [];
  String? selectedGmailAccount;
  List<EmailMessage> emails = [];
  String? currentUserName;
  bool _loading = true;
  bool _userLoading = true;
  Timer? _pollingTimer;
  late WebSocketChannel channel;
  final Random _random = Random();

  void _showAccountSwitcher() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(height: 12),
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                "Switch Gmail Account",
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 16),
              ...connectedAccounts.map((email) {
                final isSelected = email == selectedGmailAccount;
                final color = isSelected
                    ? Colors.blueAccent
                    : Colors.grey.shade600;
                return Container(
                  color: isSelected ? Colors.blue.shade50 : Colors.transparent,
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: color.withOpacity(0.2),
                      child: Text(
                        email[0].toUpperCase(),
                        style: TextStyle(
                          color: color,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    title: Text(
                      email,
                      style: TextStyle(
                        color: color,
                        fontWeight: isSelected
                            ? FontWeight.bold
                            : FontWeight.normal,
                      ),
                    ),
                    trailing: isSelected
                        ? const Icon(Icons.check, color: Colors.blueAccent)
                        : null,
                    onTap: () async {
                      Navigator.pop(context);
                      if (email != selectedGmailAccount) {
                        setState(() => selectedGmailAccount = email);
                        await loadEmails();
                      }
                    },
                  ),
                );
              }),

              const Divider(),
              ListTile(
                leading: const Icon(Icons.add, color: Colors.blueAccent),
                title: const Text("Add another account"),
                onTap: () async {
                  Navigator.pop(context);
                  await ApiService.launchGoogleLogin();
                },
              ),
              const SizedBox(height: 8),
            ],
          ),
        );
      },
    );
  }

  Future<void> loadConnectedAccounts() async {
    try {
      final res = await ApiService.fetchConnectedAccounts();
      final accounts = List<String>.from(
        res['accounts'].map((a) => a['gmail_email']),
      );
      setState(() {
        connectedAccounts = accounts;
        selectedGmailAccount = accounts.isNotEmpty ? accounts.first : null;
      });
    } catch (e) {
      print("Failed to load connected Gmail accounts: $e");
    }
  }

  @override
  void initState() {
    super.initState();
    loadCurrentUser();
    // loadEmails();
    loadConnectedAccounts().then((_) => loadEmails());
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
      final user = await ApiService.fetchCurrentUser();
      setState(() {
        currentUserName = user['name'] ?? 'U';
        _userLoading = false;
      });
    } catch (e) {
      print("⚠️ Failed to load user: $e");
      setState(() => _userLoading = false);
    }
  }

  void connectWebSocket() async {
    channel = WebSocketChannel.connect(
      // Uri.parse('wss://aidyn-findable-greedily.ngrok-free.dev/ws/emails'),
      Uri.parse('wss://aegissecurebackend.onrender.com/ws/emails'),
    );

    channel.stream.listen(
      (event) async {
        final data = jsonDecode(event);
        
        if (data['new_email'] == true &&
            data['gmail_email'] == selectedGmailAccount) {
          print("New mail for $selectedGmailAccount → refreshing inbox");
          final refreshed = await ApiService.fetchEmailsForAccount(
            selectedGmailAccount!,
          );
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


  Future<void> loadEmails() async {
    setState(() => _loading = true);

    if (selectedGmailAccount == null) {
      setState(() {
        emails = [];
        _loading = false;
      });
      return;
    }

    try {
      final data = await ApiService.fetchEmailsForAccount(
        selectedGmailAccount!,
      );
      setState(() {
        emails = data.map((e) => EmailMessage.fromJson(e)).toList();
      });
    } catch (e) {
      print("Failed to load emails: $e");
    } finally {
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

Future<void> _showSearchDialog() async {
  final _searchController = TextEditingController();

  await showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text("Search Emails"),
      content: TextField(
        controller: _searchController,
        autofocus: true, 
        decoration: const InputDecoration(
          hintText: "Search subject, sender, etc...",
          icon: Icon(Icons.search),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text("Cancel"),
        ),
        
        ElevatedButton(
          onPressed: () async {
            final query = _searchController.text.trim();
            if (query.isEmpty) {
              return; 
            }
            
            Navigator.pop(context); 

            setState(() {
              _loading = true; 
            });

            try {
              final data = await ApiService.searchEmails(query);
              
              setState(() {
                emails = data.map((e) => EmailMessage.fromJson(e)).toList();
              });

            } catch (e) {
              print("Failed to search emails: $e");
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text("Search failed: $e")),
                );
              }
            } finally {
              setState(() {
                _loading = false;
              });
            }
          },
          child: const Text("Search"),
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

        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Inbox",
              style: TextStyle(
                color: Colors.black87,
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              selectedGmailAccount ?? "No email linked",
              style: TextStyle(
                color: Colors.grey.shade600,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),

        actions: [
          IconButton(
            icon: const Icon(Icons.add, color: Colors.black87),
            tooltip: "Manual text input",
            onPressed: _handleManualInput,
          ),
          IconButton(
            icon: const Icon(Icons.search, color: Colors.black87),
            onPressed: _showSearchDialog(),
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
              child: GestureDetector(
                onTap: () async {
                  final selectedEmail = await Navigator.pushNamed(
                    context,
                    '/emailAccountManager',
                  );
                  if (selectedEmail != null && selectedEmail is String) {
                    setState(() => selectedGmailAccount = selectedEmail);
                    await loadEmails();
                  }
                },
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
            ),
        ],
      ),

      /// BODY
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

                          // ----------
                          child: Text(
                            email.spamPrediction?.toUpperCase() ?? "UNKNOWN",
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Colors.black87,
                            ),
                          ),

                          // ----------
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
          await ApiService.launchGoogleLogin();
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
              const Icon(
                Icons.chat_bubble_outline,
                color: Colors.grey,
                size: 28,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
