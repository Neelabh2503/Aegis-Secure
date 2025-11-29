import 'dart:async';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/sms_message.dart';
import '../screens/sms_detailed_screen.dart';
import '../services/api_service.dart';
import '../services/sms_service.dart';
import '../widgets/sidebar.dart';

class SmsScreen extends StatefulWidget {
  const SmsScreen({Key? key}) : super(key: key);

  @override
  State<SmsScreen> createState() => SmsScreenState();
}

class SmsScreenState extends State<SmsScreen> {
  final SmsService smsService = SmsService();

  List<SmsMessageModel> messages = [];
  bool loading = true;
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  void initState() {
    super.initState();
    initSmsFlow();
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> initSmsFlow() async {
    try {
      await smsService.syncSmsToBackend();
      final fetched = await smsService.fetchAllFromBackend();
      setState(() {
        messages = fetched;
        loading = false;
      });
    } catch (e) {
      setState(() => loading = false);
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

  String getDisplayName(String address, String? contactName) {
    if (contactName != null && contactName.isNotEmpty) return contactName;
    final isBusinessSender = RegExp(r'[A-Za-z]').hasMatch(address);
    if (isBusinessSender) {
      return address.replaceAll(RegExp(r'^[A-Z]{2}-'), '');
    }
    return address;
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
                                  : "UNKNOWN";
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

  Widget buildMessageTile(SmsMessageModel msg) {
    final sender = getDisplayName(msg.address, null);
    final body = msg.body;
    // final scoreRaw = msg.spamScore?.toString() ?? '0.00';
    // final double score = double.tryParse(scoreRaw) ?? 0.00;
    // final double scoreNormalized = score.clamp(0.0, 100.0);
    final double scoreNormalized = (msg.spamScore ?? 0.0).clamp(0.0, 100.0);
    final time = DateTime.fromMillisecondsSinceEpoch(msg.dateMs).toLocal();

    Color getSpamColor(double score) {
      if (score < 25) {
        return Colors.green.shade100;
      } else if (score < 50) {
        return Colors.yellow.shade100;
      } else if (score < 75) {
        return Colors.orange.shade100;
      } else {
        return Colors.red.shade100;
      }
    }

    Color getSpamTextColor(double score) {
      if (score < 25) {
        return Colors.green.shade700;
      } else if (score < 50) {
        return Colors.amber.shade700;
      } else if (score < 75) {
        return Colors.deepOrange.shade700;
      } else {
        return Colors.red.shade700;
      }
    }

    final spamColor = getSpamColor(scoreNormalized);
    final spamTextColor = getSpamTextColor(scoreNormalized);

    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => SmsDetailedScreen(message: msg),
          ),
        );
      },
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 0, horizontal: 2),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(10),
          boxShadow: [
            BoxShadow(
              color: Colors.grey.shade300,
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
                      style: TextStyle(
                        color: Colors.grey.shade700,
                        fontSize: 13,
                      ),
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
                      border: Border.all(color: spamTextColor.withOpacity(0.3)),
                    ),
                    child: Text(
                      scoreNormalized.toStringAsFixed(2),
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: spamTextColor,
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        formatShortDate(time),
                        style: TextStyle(
                          color: Colors.grey.shade600,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(width: 9),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
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
                      backgroundColor: Color(0xFF1F2A6E),
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
          onPressed: () => _scaffoldKey.currentState?.openDrawer(),
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
            icon: const Icon(Icons.edit_note, color: Colors.black87),
            tooltip: "Manual text input",
            onPressed: handleManualInput,
          ),
          IconButton(
            icon: const Icon(Icons.search, color: Colors.black87),
            tooltip: "Search messages",
            onPressed: () {
              showSearch(
                context: context,
                delegate: SmsSearchDelegate(messages),
              );
            },
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: initSmsFlow,
              child: messages.isEmpty
                  ? ListView(
                      children: const [
                        SizedBox(height: 200),
                        Center(
                          child: Text(
                            "No messages found",
                            style: TextStyle(fontSize: 16),
                          ),
                        ),
                      ],
                    )
                  : ListView.separated(
                      itemCount: messages.length,
                      separatorBuilder: (_, __) => Divider(
                        height: 0.5,
                        thickness: 0.5,
                        color: Colors.grey,
                      ),
                      itemBuilder: (context, index) =>
                          buildMessageTile(messages[index]),
                    ),
            ),
    );
  }
}

class SmsSearchDelegate extends SearchDelegate<String> {
  final List<SmsMessageModel> allMessages;
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

  SmsSearchDelegate(this.allMessages);

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
  Widget buildResults(BuildContext context) => _buildSmsList(context);

  @override
  Widget buildSuggestions(BuildContext context) => _buildSmsList(context);

  Widget _buildSmsList(BuildContext context) {
    final q = query.toLowerCase();
    final filtered = allMessages.where((msg) {
      return msg.address.toLowerCase().contains(q) ||
          msg.body.toLowerCase().contains(q);
    }).toList();

    if (filtered.isEmpty) {
      return const Center(
        child: Text(
          "No matching messages found",
          style: TextStyle(fontSize: 16, color: Colors.grey),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
      itemCount: filtered.length,
      separatorBuilder: (_, __) =>
          Divider(height: 0.5, thickness: 0.5, color: Colors.grey.shade300),
      itemBuilder: (context, index) {
        final msg = filtered[index];
        final sender = msg.address;
        // final scoreRaw = msg.spamScore?.toString() ?? '0.00';
        // final double score = double.tryParse(scoreRaw) ?? 0.00;
        // final double scoreNormalized = score.clamp(0.0, 100.0);
        final double scoreNormalized = (msg.spamScore ?? 0.0).clamp(0.0, 100.0);
        Color getSpamColor(double score) {
          if (score < 25) {
            return Colors.green.shade100;
          } else if (score < 50) {
            return Colors.yellow.shade100;
          } else if (score < 75) {
            return Colors.orange.shade100;
          } else {
            return Colors.red.shade100;
          }
        }

        Color getSpamTextColor(double score) {
          if (score < 25) {
            return Colors.green.shade700;
          } else if (score < 50) {
            return Colors.amber.shade700;
          } else if (score < 75) {
            return Colors.deepOrange.shade700;
          } else {
            return Colors.red.shade700;
          }
        }

        final spamColor = getSpamColor(scoreNormalized);
        final spamTextColor = getSpamTextColor(scoreNormalized);

        final time = DateTime.fromMillisecondsSinceEpoch(msg.dateMs).toLocal();
        final formattedTime =
            "${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}";

        return GestureDetector(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => SmsDetailedScreen(message: msg),
              ),
            );
          },
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border(bottom: BorderSide(color: Colors.grey.shade300)),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 20,
                  backgroundColor: Colors
                      .primaries[sender.hashCode % Colors.primaries.length],
                  child: Text(
                    sender.isNotEmpty ? sender[0].toUpperCase() : "?",
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
                        sender,
                        query,
                        const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                          color: Colors.black,
                        ),
                      ),
                      const SizedBox(height: 3),
                      _highlightMatch(
                        msg.body,
                        query,
                        TextStyle(color: Colors.grey.shade700, fontSize: 13),
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
                        scoreNormalized.toStringAsFixed(2),
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: spamTextColor,
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          formatShortDate(time),
                          style: TextStyle(
                            color: Colors.grey.shade600,
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(width: 9),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _highlightMatch(String text, String query, TextStyle baseStyle) {
    if (query.isEmpty) return Text(text, style: baseStyle);

    final lower = text.toLowerCase();
    final q = query.toLowerCase();

    final spans = <TextSpan>[];
    int start = 0;

    while (true) {
      final index = lower.indexOf(q, start);
      if (index == -1) {
        spans.add(TextSpan(text: text.substring(start)));
        break;
      }
      if (index > start) {
        spans.add(TextSpan(text: text.substring(start, index)));
      }
      spans.add(
        TextSpan(
          text: text.substring(index, index + q.length),
          style: const TextStyle(
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
      maxLines: 2,
    );
  }
}
