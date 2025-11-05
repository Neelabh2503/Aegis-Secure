import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../widgets/sidebar.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String? currentUserName;
  bool _userLoading = true;

  @override
  void initState() {
    super.initState();
    loadCurrentUser();
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

  Future<void> _logout(BuildContext context) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('jwt_token');
    Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
  }

  void _goToGmail() {
    Navigator.pushNamedAndRemoveUntil(context, '/gmail', (route) => false);
  }

  void _goToSms() {
    Navigator.pushNamedAndRemoveUntil(context, '/sms', (route) => false);
  }

  @override
  Widget build(BuildContext context) {
    final firstLetter = (currentUserName != null && currentUserName!.isNotEmpty)
        ? currentUserName![0].toUpperCase()
        : '?';
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
                            if (confidence.isNotEmpty)
                              const SizedBox(height: 6),
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
                    onHomeTap: () {
                      Navigator.of(context).pop();
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text("You are already on Home!"),
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
          "Analytics",
          style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.add, color: Colors.black87),
            tooltip: "Manual text input",
            onPressed: _handleManualInput,
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
                backgroundColor: Colors.purpleAccent,
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
      body: Stack(
        children: [
          const Center(
            child: Text(
              "Analytics",
              style: TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
          ),
          Positioned(
            right: 20,
            bottom: 80,
            child: FloatingActionButton(
              onPressed: () => _logout(context),
              backgroundColor: Colors.redAccent,
              tooltip: "Logout",
              child: const Icon(Icons.logout, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }
}
