import 'dart:async';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/gmail_model.dart';
import '../screens/Email_detail_screen.dart';
import '../services/api_service.dart';
import '../widgets/sidebar.dart';

class GmailScreen extends StatefulWidget {
  const GmailScreen({Key? key}) : super(key: key);

  @override
  GmailScreenState createState() => GmailScreenState();
}

class GmailScreenState extends State<GmailScreen> {
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await loadConnectedAccounts();
      if (mounted && selectedGmailAccount != null) {
        await loadEmails(initial: true);
      }
    });
  }

  Color parseColor(String? hexColor) {
    if (hexColor == null || hexColor.isEmpty) return Colors.grey.shade400;
    try {
      hexColor = hexColor.replaceAll("#", "");
      if (hexColor.length == 6) hexColor = "FF$hexColor";
      return Color(int.parse(hexColor, radix: 16));
    } catch (_) {
      return Colors.grey.shade400;
    }
  }

  String formatShortDate(DateTime date) {
    const months = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];

    return "${months[date.month - 1]} ${date.day}";
  }

  String formatTime(DateTime dt) {
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
  bool loading = false;
  bool refreshing = false;
  bool userLoading = false;
  Timer? _pollingTimer;

  Future<void> loadConnectedAccounts() async {
    try {
      final res = await ApiService.fetchConnectedAccounts();
      final accounts = List<String>.from(
        res['accounts'].map((a) => a['gmail_email']),
      );
      final prefs = await SharedPreferences.getInstance();
      String? savedAccount = prefs.getString('selectedGmailAccount');

      String? accountToSelect;

      if (savedAccount != null && accounts.contains(savedAccount)) {
        accountToSelect = savedAccount;
      } else if (ApiService.selectedEmailAccount != null &&
          accounts.contains(ApiService.selectedEmailAccount)) {
        accountToSelect = ApiService.selectedEmailAccount;
      } else {
        accountToSelect = accounts.isNotEmpty ? accounts.last : null;
      }
      setState(() {
        connectedAccounts = accounts;
        selectedGmailAccount = accountToSelect;
        ApiService.selectedEmailAccount = accountToSelect;
      });
    } catch (e) {
      print("**** Failed to load connected Gmail accounts: $e");
    }
  }

  @override
  void initState() {
    super.initState();
    // loadCurrentUser();
    loadConnectedAccounts().then((_) async {
      if (mounted && selectedGmailAccount != null) {
        ApiService.selectedEmailAccount = selectedGmailAccount;
      }
    });
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    // channel?.sink.close();
    super.dispose();
  }

  Future<void> loadCurrentUser() async {
    try {
      final user = await ApiService.fetchCurrentUser();
      setState(() {
        currentUserName = user['name'] ?? 'U';
        userLoading = false;
      });
    } catch (e) {
      print("***** Failed to load user: $e");
      setState(() => userLoading = false);
    }
  }

  // Future<void> loadEmails({bool initial = false}) async {
  //   setState(() => loading = true);
  //
  //   if (selectedGmailAccount == null) {
  //     setState(() {
  //       emails = allEmails;
  //       loading = false;
  //     });
  //     return;
  //   }
  //   if (initial) {
  //     setState(() => loading = true);
  //   } else {
  //     setState(() => refreshing = true);
  //   }
  //
  //   try {
  //     final data = await ApiService.fetchEmailsForAccount(
  //       selectedGmailAccount!,
  //     );
  //     final loadedEmails = data.map((e) => EmailMessage.fromJson(e)).toList();
  //
  //     setState(() {
  //       allEmails = loadedEmails;
  //       emails = loadedEmails;
  //     });
  //   } catch (e) {
  //     print("Failed to load emails: $e");
  //   } finally {
  //     setState(() => loading = false);
  //   }
  // }

  Future<void> loadEmails({bool initial = false}) async {
    if (selectedGmailAccount == null) {
      setState(() {
        emails = allEmails;
        loading = false;
        refreshing = false;
      });
      return;
    }

    if (initial) {
      setState(() => loading = true);
    } else {
      setState(() => refreshing = true);
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
      setState(() {
        loading = false;
        refreshing = false;
      });
    }
  }

  Future<void> handleManualInput() async {
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
                        color:
                            double.tryParse(confidence) != null &&
                                double.parse(confidence) > 50.0
                            ? Colors.red.shade50
                            : Colors.green.shade50,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                          color:
                              double.tryParse(confidence) != null &&
                                  double.parse(confidence) > 50.0
                              ? Colors.red.shade50
                              : Colors.green.shade50,
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
                              color:
                                  double.tryParse(confidence) != null &&
                                      double.parse(confidence) > 50.0
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
                                color:
                                    double.tryParse(confidence) != null &&
                                        double.parse(confidence) > 50.0
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
                            final rawScore =
                                result['spam_prediction'] ??
                                result['prediction'] ??
                                0;
                            final conf = (result['confidence'] is num)
                                ? (result['confidence'] as num).toDouble()
                                : double.tryParse(
                                        result['confidence']?.toString() ?? '',
                                      ) ??
                                      0.0;

                            final decision = (result['final_decision'] ?? '')
                                .toString()
                                .toUpperCase();

                            setStateDialog(() {
                              prediction = decision.isNotEmpty
                                  ? decision
                                  : "--";
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

  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  @override
  Widget build(BuildContext context) {
    final firstLetter = (currentUserName != null && currentUserName!.isNotEmpty)
        ? currentUserName![0].toUpperCase()
        : 'A';

    return Scaffold(
      key: _scaffoldKey,
      drawer: Sidebar(
        onClose: () => _scaffoldKey.currentState?.closeDrawer(),
        onLogoutTap: () async {
          _scaffoldKey.currentState?.closeDrawer();
          await Future.delayed(const Duration(milliseconds: 150));

          final confirmed = await showDialog<bool>(
            context: context,
            barrierDismissible: false,
            builder: (context) {
              return AlertDialog(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                elevation: 10,
                title: Row(
                  children: const [
                    Icon(Icons.logout, color: Color(0xFF1F2A6E)),
                    SizedBox(width: 10),
                    Text(
                      "Confirm Sign Out",
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                content: const Text(
                  "Are you sure you want to sign out from your account?",
                  style: TextStyle(fontSize: 16, color: Colors.black87),
                ),
                actionsPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 10,
                ),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    style: TextButton.styleFrom(
                      foregroundColor: Colors.grey.shade700,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 10,
                      ),
                    ),
                    child: const Text("Cancel"),
                  ),
                  ElevatedButton.icon(
                    onPressed: () => Navigator.pop(context, true),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1F2A6E),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 18,
                        vertical: 10,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    icon: const Icon(Icons.exit_to_app, size: 18),
                    label: const Text(
                      "Sign Out",
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              );
            },
          );

          if (confirmed == true) {
            final prefs = await SharedPreferences.getInstance();
            await prefs.remove('jwt_token');
            Navigator.of(
              context,
              rootNavigator: true,
            ).pushNamedAndRemoveUntil('/login', (route) => false);
          }
        },
      ),
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.menu, color: Colors.black87),
          onPressed: () {
            _scaffoldKey.currentState?.openDrawer();
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
            icon: const Icon(Icons.edit_note, color: Colors.black87),
            tooltip: "Manual text input",
            onPressed: handleManualInput,
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
                  await loadEmails(initial: true);
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
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : Stack(
              children: [
                RefreshIndicator(
                  onRefresh: () => loadEmails(initial: false),
                  child: emails.isEmpty
                      ? ListView(
                          physics: const AlwaysScrollableScrollPhysics(),
                          children: const [
                            SizedBox(height: 200),
                            Center(child: Text("No emails found")),
                          ],
                        )
                      : ListView.separated(
                          physics: const AlwaysScrollableScrollPhysics(),
                          itemCount: emails.length,
                          separatorBuilder: (_, __) => Divider(
                            height: 0.5,
                            thickness: 1.0,
                            color: Colors.grey.shade300,
                          ),
                          itemBuilder: (context, index) {
                            final email = emails[index];
                            final rawPred =
                                (email.spamPrediction?.toUpperCase() ?? "--") ==
                                    "UNKNOWN"
                                ? "0.00"
                                : (email.spamPrediction?.toUpperCase() ?? "--");
                            final predValue = double.tryParse(rawPred);

                            Color getColorForScore(double? score) {
                              if (score == null) return Colors.grey.shade300;
                              if (score < 25) return Colors.green.shade100;
                              if (score < 50) return Colors.yellow.shade100;
                              if (score < 75) return Colors.orange.shade100;
                              return Colors.red.shade100;
                            }

                            Color getTextColorForScore(double? score) {
                              if (score == null) return Colors.grey.shade600;
                              if (score < 25) return Colors.green.shade700;
                              if (score < 50) return Colors.amber.shade700;
                              if (score < 75) return Colors.deepOrange.shade700;
                              return Colors.red.shade700;
                            }

                            final spamColor = getColorForScore(predValue);
                            final spamTextColor = getTextColorForScore(
                              predValue,
                            );

                            return InkWell(
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) =>
                                        EmailDetailScreen(email: email),
                                  ),
                                );
                              },
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
                                      backgroundColor: parseColor(
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
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
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
                                      crossAxisAlignment:
                                          CrossAxisAlignment.end,
                                      children: [
                                        Container(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 10,
                                            vertical: 4,
                                          ),
                                          decoration: BoxDecoration(
                                            color: spamColor,
                                            borderRadius: BorderRadius.circular(
                                              10,
                                            ),
                                            border: Border.all(
                                              color: spamTextColor.withOpacity(
                                                0.3,
                                              ),
                                            ),
                                          ),
                                          child: Text(
                                            predValue != null
                                                ? predValue.toStringAsFixed(2)
                                                : "--",
                                            style: TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.bold,
                                              color: spamTextColor,
                                            ),
                                          ),
                                        ),
                                        const SizedBox(height: 6),
                                        Align(
                                          child: Text(
                                            formatShortDate(email.timestamp),
                                            style: TextStyle(
                                              fontSize: 12,
                                              color: Colors.grey.shade600,
                                            ),
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
                ),
              ],
            ),
    );
  }
}

class EmailSearchDelegate extends SearchDelegate<String> {
  final List<EmailMessage> allEmails;
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
  Widget buildResults(BuildContext context) => buildEmailList(context);
  @override
  Widget buildSuggestions(BuildContext context) => buildEmailList(context);
  Widget buildEmailList(BuildContext context) {
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

    String formatShortDate(DateTime date) {
      const months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
      ];

      return "${months[date.month - 1]} ${date.day}";
    }

    String formatTime(DateTime dt) {
      final now = DateTime.now();
      if (now.difference(dt).inDays == 0) {
        return "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
      } else {
        return "${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}";
      }
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
          final rawPred =
              (email.spamPrediction?.toUpperCase() ?? "--") == "UNKNOWN"
              ? "--"
              : (email.spamPrediction?.toUpperCase() ?? "--");
          final predValue = double.tryParse(rawPred);

          Color spamColor;
          Color spamTextColor;

          Color getColorForScore(double? score) {
            if (score == null) return Colors.grey.shade300;
            if (score < 25) return Colors.green.shade100;
            if (score < 50) return Colors.yellow.shade100;
            if (score < 75) return Colors.orange.shade100;
            return Colors.red.shade100;
          }

          Color getTextColorForScore(double? score) {
            if (score == null) return Colors.grey.shade600;
            if (score < 25) return Colors.green.shade700;
            if (score < 50) return Colors.amber.shade700;
            if (score < 75) return Colors.deepOrange.shade700;
            return Colors.red.shade700;
          }

          spamColor = getColorForScore(predValue);
          spamTextColor = getTextColorForScore(predValue);
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
                    backgroundColor: parseColor(email.charColor ?? "#9E9E9E"),
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
                        highlightMatch(
                          email.sender,
                          query,
                          const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                            color: Colors.black,
                          ),
                        ),
                        const SizedBox(height: 2),
                        highlightMatch(
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
                        highlightMatch(
                          email.snippet,
                          query,
                          TextStyle(color: Colors.grey[600], fontSize: 13),
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
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
                          predValue != null
                              ? predValue.toStringAsFixed(2)
                              : "0.00",
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: spamTextColor,
                          ),
                        ),
                      ),

                      const SizedBox(height: 6),

                      Align(
                        child: Text(
                          formatShortDate(email.timestamp),
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade600,
                          ),
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

  Widget highlightMatch(String? text, String query, TextStyle baseStyle) {
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

  Color parseColor(String? hexColor) {
    if (hexColor == null || hexColor.isEmpty) return Colors.grey.shade400;
    try {
      hexColor = hexColor.replaceAll("#", "");
      if (hexColor.length == 6) hexColor = "FF$hexColor";
      return Color(int.parse(hexColor, radix: 16));
    } catch (_) {
      return Colors.grey.shade400;
    }
  }
}
