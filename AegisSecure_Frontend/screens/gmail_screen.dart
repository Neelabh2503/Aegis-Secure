import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../models/gmail_model.dart';
import '../services/api_service.dart';
import '../widgets/sidebar.dart';

class GmailScreen extends StatefulWidget {
  const GmailScreen({Key? key}) : super(key: key);

  @override
  _GmailScreenState createState() => _GmailScreenState();
}

class _GmailScreenState extends State<GmailScreen> {
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Called when this screen reappears
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
      print("⚠️ Failed to load connected Gmail accounts: $e");
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
          print("📩 New mail for $selectedGmailAccount → refreshing inbox");
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
      print("⚠️ Failed to load emails: $e");
    } finally {
      setState(() => _loading = false);
    }
  }

  /// Manual text scoring input
  /// ----------
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

  // --------

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

  /// OAuth Gmail Connection Flow
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
                    onMailTap: () {
                      Navigator.of(context).pop(); // close sidebar
                      // Optional: Show message or stay on home
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text("You are already on Mail Page!"),
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
    );
  }
}
class EmailSearchDelegate extends SearchDelegate<String> {
  final List<EmailMessage> allEmails;
  final Random _random = Random();
  EmailSearchDelegate(this.allEmails);

  // Gmail-like soft color palette for avatars

  @override
  List<Widget>? buildActions(BuildContext context) => [
    if (query.isNotEmpty)
      IconButton(icon: const Icon(Icons.clear), onPressed: () => query = ''),
  ];

  @override
  Widget? buildLeading(BuildContext context) => IconButton(
    icon: const Icon(Icons.arrow_back),
    onPressed: () => close(context, ''),
  );

  @override
  Widget buildResults(BuildContext context) => _buildEmailList(context);

  @override
  Widget buildSuggestions(BuildContext context) => _buildEmailList(context);

  Widget _buildEmailList(BuildContext context) {
    final q = query.toLowerCase();
    final theme = Theme.of(context);

    final filtered = allEmails.where((email) {
      return email.sender.toLowerCase().contains(q) ||
          email.subject.toLowerCase().contains(q) ||
          email.snippet.toLowerCase().contains(q);
    }).toList();

    if (filtered.isEmpty) {
      return const Center(
        child: Text(
          "No matching emails found",
          style: TextStyle(fontSize: 16, color: Colors.grey),
        ),
      );
    }

    return Container(
      color: theme.brightness == Brightness.dark
          ? const Color(0xFF121212)
          : const Color(0xFFF9FAFC),
      child: ListView.separated(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
        itemCount: filtered.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, index) {
          final email = filtered[index];
          final rawPred = email.spamPrediction?.toUpperCase() ?? "UNKNOWN";

          final isSpam =
              rawPred == "SPAM" ||
              double.tryParse(rawPred) != null && double.parse(rawPred) >= 0.5;

          final spamColor = isSpam
              ? Colors.red.shade100
              : Colors.green.shade100;
          final spamTextColor = isSpam
              ? Colors.red.shade700
              : Colors.green.shade700;

          return InkWell(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => EmailDetailScreen(email: email),
                ),
              );
            },

            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border(bottom: BorderSide(color: Colors.grey.shade200)),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  CircleAvatar(
                    radius: 20,
                    backgroundColor: _parseColor(email.charColor ?? "#9E9E9E"),
                    child: Text(
                      email.sender.isNotEmpty
                          ? email.sender[0].toUpperCase()
                          : 'A',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _highlightMatch(
                          email.sender,
                          query,
                          const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                            color: Colors.black,
                          ),
                        ),
                        const SizedBox(height: 2),
                        _highlightMatch(
                          email.subject.isEmpty
                              ? "(No Subject)"
                              : email.subject,
                          query,
                          const TextStyle(
                            fontWeight: FontWeight.w600,
                            color: Colors.black87,
                          ),
                        ),
                        const SizedBox(height: 2),
                        _highlightMatch(
                          email.snippet,
                          query,
                          TextStyle(color: Colors.grey[600], fontSize: 13),
                        ),
                      ],
                    ),
                  ),

                  Column(
                    mainAxisAlignment: MainAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: spamColor,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                            color: spamTextColor.withOpacity(0.3),
                          ),
                        ),
                        child: Text(
                          rawPred.isEmpty ? "UNKNOWN" : rawPred,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: spamTextColor,
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Icon(Icons.more_vert, color: Colors.grey, size: 20),
                    ],
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  /// Highlight matched query inside text
  Widget _highlightMatch(String? text, String query, TextStyle baseStyle) {
    final safeText = text ?? "";
    if (query.isEmpty || safeText.isEmpty) {
      return Text(safeText, style: baseStyle);
    }

    final lower = safeText.toLowerCase();
    final q = query.toLowerCase();

    final spans = <TextSpan>[];
    int start = 0;

    while (true) {
      final index = lower.indexOf(q, start);
      if (index == -1) {
        spans.add(TextSpan(text: safeText.substring(start)));
        break;
      }
      if (index > start) {
        spans.add(TextSpan(text: safeText.substring(start, index)));
      }
      spans.add(
        TextSpan(
          text: safeText.substring(index, index + q.length),
          style: baseStyle.copyWith(
            color: Colors.blueAccent,
            fontWeight: FontWeight.bold,
          ),
        ),
      );
      start = index + q.length;
    }

    return RichText(
      text: TextSpan(style: baseStyle, children: spans),
      overflow: TextOverflow.ellipsis,
      maxLines: 1,
    );
  }

  Color _parseColor(String hex) {
    if (hex.startsWith("#")) hex = hex.substring(1);
    return Color(int.parse("FF$hex", radix: 16));
  }
}