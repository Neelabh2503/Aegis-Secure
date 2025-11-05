import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../models/gmail_model.dart';
import '../screens/Email_detail_screen.dart';
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
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await loadConnectedAccounts();
      await loadEmails();
    });
  }

  Color _parseColor(String hexColor) {
    try {
      hexColor = hexColor.replaceAll("#", "");
      if (hexColor.length == 6) hexColor = "FF$hexColor";
      return Color(int.parse(hexColor, radix: 16));
    } catch (_) {
      return Colors.grey.shade400;
    }
  }

  String _formatTime(DateTime dt) {
    final now = DateTime.now();
    if (now.difference(dt).inDays == 0) {
      return "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
    } else {
      return "${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}";
    }
  }

  List<String> connectedAccounts = [];
  String? selectedGmailAccount;
  List<EmailMessage> emails = [];
  List<EmailMessage> allEmails = [];
  String? currentUserName;
  bool _loading = true;
  bool _userLoading = true;
  Timer? _pollingTimer;
  late WebSocketChannel channel;
  final Random _random = Random();

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
              if (query.isEmpty) return;

              Navigator.pop(context);
              setState(() => _loading = true);

              try {
                final results = await ApiService.searchEmails(query);
                setState(() {
                  emails = results
                      .map((e) => EmailMessage.fromJson(e))
                      .toList();
                });
              } catch (e) {
                print("Search failed: $e");
                if (mounted) {
                  ScaffoldMessenger.of(
                    context,
                  ).showSnackBar(SnackBar(content: Text("Search failed: $e")));
                }
              } finally {
                setState(() => _loading = false);
              }
            },
            child: const Text("Search"),
          ),
        ],
      ),
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
      print("Failed to load user: $e");
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
          // print("⭐️New mail for $selectedGmailAccount → refreshing inbox");
          final refreshed = await ApiService.fetchEmailsForAccount(
            selectedGmailAccount!,
          );
          setState(() {
            emails = refreshed.map((e) => EmailMessage.fromJson(e)).toList();
          });
        }
      },
      onError: (err) => print("WebSocket error: $err"),
      onDone: () {
        print("WS closed, retrying in 5s...");
        Future.delayed(const Duration(seconds: 5), connectWebSocket);
      },
    );
  }

  Future<void> loadEmails() async {
    setState(() => _loading = true);

    if (selectedGmailAccount == null) {
      setState(() {
        emails = allEmails;
        _loading = false;
      });
      return;
    }

    try {
      final data = await ApiService.fetchEmailsForAccount(
        selectedGmailAccount!,
      );
      final loadedEmails = data.map((e) => EmailMessage.fromJson(e)).toList();

      setState(() {
        allEmails = loadedEmails;
        emails = loadedEmails;
      });
    } catch (e) {
      print("Failed to load emails: $e");
    } finally {
      setState(() => _loading = false);
    }
  }

  void _performSearch(String query) {
    query = query.toLowerCase();

    if (query.isEmpty) {
      setState(() => emails = allEmails);
      return;
    }

    final filtered = allEmails.where((email) {
      final from = email.sender.toLowerCase();
      final subject = email.subject.toLowerCase();
      final snippet = email.snippet.toLowerCase();

      return from.contains(query) ||
          subject.contains(query) ||
          snippet.contains(query);
    }).toList();

    setState(() => emails = filtered);
  }

  Future<void> _handleManualInput() async {
    final controller = TextEditingController();
    String prediction = "";
    String confidence = "";

    await showDialog(
      context: context,
      barrierDismissible: true, 
      builder: (context) => StatefulBuilder(
        builder: (context, setStateDialog) {
          return Dialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
            insetPadding: const EdgeInsets.symmetric(
              horizontal: 20,
              vertical: 40,
            ),
            child: Container(
              width: double.infinity,
              constraints: const BoxConstraints(maxHeight: 580),
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black26.withOpacity(0.08),
                    blurRadius: 20,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        "Manual Text Analysis",
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 22,
                          color: Colors.black87,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Colors.grey),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: Colors.grey.shade300),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.04),
                          blurRadius: 8,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: TextField(
                      controller: controller,
                      maxLines: 8,
                      style: const TextStyle(fontSize: 15, height: 1.5),
                      decoration: InputDecoration(
                        hintText: "Enter text to analyze...",
                        hintStyle: TextStyle(color: Colors.grey.shade500),
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 14,
                        ),
                        border: InputBorder.none,
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  if (prediction.isNotEmpty)
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 400),
                      curve: Curves.easeOut,
                      padding: const EdgeInsets.all(18),
                      margin: const EdgeInsets.only(bottom: 10),
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: prediction == "SPAM"
                            ? Colors.red.shade50
                            : Colors.green.shade50,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                          color: prediction == "SPAM"
                              ? Colors.red.shade200
                              : Colors.green.shade200,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black12,
                            blurRadius: 6,
                            offset: const Offset(0, 3),
                          ),
                        ],
                      ),
                      child: Column(
                        children: [
                          Text(
                            prediction,
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: prediction == "SPAM"
                                  ? Colors.red.shade700
                                  : Colors.green.shade700,
                            ),
                          ),
                          if (confidence.isNotEmpty) const SizedBox(height: 6),
                          if (confidence.isNotEmpty)
                            Text(
                              "Confidence: $confidence",
                              style: TextStyle(
                                fontSize: 14,
                                color: prediction == "SPAM"
                                    ? Colors.red.shade700
                                    : Colors.green.shade700,
                              ),
                            ),
                        ],
                      ),
                    ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        style: TextButton.styleFrom(
                          foregroundColor: Colors.grey.shade700,
                          textStyle: const TextStyle(fontSize: 15),
                        ),
                        child: const Text("Cancel"),
                      ),
                      const SizedBox(width: 10),
                      ElevatedButton(
                        onPressed: () async {
                          final inputText = controller.text.trim();
                          if (inputText.isEmpty) return;

                          setStateDialog(() {
                            prediction = "Analyzing...";
                            confidence = "";
                          });

                          try {
                            final result = await ApiService.analyzeText(
                              inputText,
                            );
                            final confStr = result['prediction'] ?? "0.0";
                            final conf = double.tryParse(confStr) ?? 0.0;
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
                          backgroundColor: Colors.blue.shade700,
                          padding: const EdgeInsets.symmetric(
                            horizontal: 22,
                            vertical: 14,
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          textStyle: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                          ),
                          elevation: 4,
                        ),
                        child: const Text(
                          "Analyze",
                          style: TextStyle(color: Colors.white),
                        ),
                      ),
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

  @override
  Widget build(BuildContext context) {
    final firstLetter = (currentUserName != null && currentUserName!.isNotEmpty)
        ? currentUserName![0].toUpperCase()
        : 'A';

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
                      Navigator.of(context).pop(); 
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
            onPressed: () {
              showSearch(
                context: context,
                delegate: EmailSearchDelegate(allEmails),
              );
            },
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

      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : emails.isEmpty
          ? const Center(child: Text("No emails found"))
          : RefreshIndicator(
              onRefresh: loadEmails,
              child: ListView.separated(
                itemCount: emails.length,
                separatorBuilder: (_, __) =>
                    Divider(thickness: 0.8, color: Colors.grey.shade300),
                itemBuilder: (context, index) {
                  final email = emails[index];
                  final rawPred =
                      email.spamPrediction?.toUpperCase() ?? "UNKNOWN";

                  final isSpam =
                      rawPred == "SPAM" ||
                      double.tryParse(rawPred) != null &&
                          double.parse(rawPred) >= 0.5;

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
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
                      color: Colors.white,
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          CircleAvatar(
                            backgroundColor: _parseColor(
                              email.charColor ?? "#9E9E9E",
                            ),
                            child: Text(
                              email.sender.isNotEmpty
                                  ? email.sender[0].toUpperCase()
                                  : 'A',
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  email.sender,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 15,
                                  ),
                                ),
                                const SizedBox(height: 2),
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
                          ),
                          const SizedBox(width: 8),
                          Column(
                            mainAxisAlignment: MainAxisAlignment.start,
                            crossAxisAlignment: CrossAxisAlignment.center,
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
                                  email.spamPrediction.toString(),
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: spamTextColor,
                                  ),
                                ),
                              ),
                              const SizedBox(height: 12),
                              const Icon(
                                Icons.more_vert,
                                size: 20,
                                color: Colors.grey,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
      // floatingActionButton: FloatingActionButton(
      //   onPressed: () async {
      //     await ApiService.launchGoogleLogin();
      //   },
      //   backgroundColor: Colors.blueAccent,
      //   shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      //   child: const Icon(Icons.add, size: 28, color: Colors.white),
      // ),
    );
  }
}

class EmailSearchDelegate extends SearchDelegate<String> {
  final List<EmailMessage> allEmails;
  final Random _random = Random();
  EmailSearchDelegate(this.allEmails);
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