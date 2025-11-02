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
                            if (confidence.isNotEmpty)
                              const SizedBox(height: 6),
                            if (confidence.isNotEmpty)
                              Text(
                                "Confidence: $confidence",
                                style: TextStyle(
                                  color: textColor,
                                  fontSize: 14,
                                ),
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
