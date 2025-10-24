import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';

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

  void _goToChat() {
    Navigator.pushNamedAndRemoveUntil(context, '/chat', (route) => false);
  }

  @override
  Widget build(BuildContext context) {
    final firstLetter = (currentUserName != null && currentUserName!.isNotEmpty)
        ? currentUserName![0].toUpperCase()
        : '?';

    /// Manual text scoring input
    Future<void> _handleManualInput() async {
    final controller = TextEditingController();
    String prediction = ""; 

    await showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setStateDialog) => AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          title: const Text("Manual Text Analysis"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: controller,
                maxLines: 3,
                decoration: const InputDecoration(
                  hintText: "Enter text to get prediction",
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              if (prediction.isNotEmpty)
                Builder(
                  builder: (_) {
                    print("DEBUG: prediction value = '$prediction'");

                    return Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: prediction == "SPAM"
                            ? Colors.red.shade100
                            : prediction == "HAM"
                            ? Colors.green.shade100
                            : Colors.grey.shade200,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        prediction,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: prediction == "SPAM"
                              ? Colors.red
                              : prediction == "HAM"
                              ? Colors.green
                              : Colors.black87,
                        ),
                      ),
                    );
                  },
                ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Cancel"),
            ),
            ElevatedButton(
              onPressed: () async {
                final inputText = controller.text.trim();
                if (inputText.isEmpty) return;

                setStateDialog(() {
                  prediction = "Analyzing...";
                });

                try {
                  final result = await ApiService.analyzeText(inputText);
                  final predValue = result['prediction'] ?? "UNKNOWN";
                  setStateDialog(() {
                    prediction = predValue
                        .trim()
                        .toUpperCase(); 
                    print("DEBUG: prediction after extraction = '$prediction'");
                  });
                } catch (e) {
                  setStateDialog(() {
                    prediction = "ERROR";
                    print("DEBUG: Error fetching prediction = $e");
                  });
                }
              },
              child: const Text("Submit"),
            ),
          ],
        ),
      ),
    );
  }

    return Scaffold(
      backgroundColor: Colors.white,

      /// --- APP BAR ---
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.menu, color: Colors.black87),
          onPressed: () {},
        ),
        title: const Text(
          "Analytics",
          style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
        ),
        actions: [
          /// ➕ Manual Text Input (same as GmailScreen)
          IconButton(
            icon: const Icon(Icons.add, color: Colors.black87),
            tooltip: "Manual text input",
            onPressed: _handleManualInput,
          ),

          /// 🔍 Search
          IconButton(
            icon: const Icon(Icons.search, color: Colors.black87),
            onPressed: () {},
          ),

          /// 👤 User Avatar or Loading Spinner
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

      /// --- BODY
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

          /// LOGOUT BUTTON
          Positioned(
            right: 20,
            bottom: 80, // slightly above bottom nav bar
            child: FloatingActionButton(
              onPressed: () => _logout(context),
              backgroundColor: Colors.redAccent,
              tooltip: "Logout",
              child: const Icon(Icons.logout, color: Colors.white),
            ),
          ),
        ],
      ),

      /// NAVIGATION BAR
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

              GestureDetector(
                onTap: _goToGmail,
                child: const Icon(
                  Icons.mail_outline,
                  color: Colors.grey,
                  size: 28,
                ),
              ),

              ///HOME
              const Icon(
                Icons.home_outlined,
                color: Colors.blue, // Active here
                size: 28,
              ),

              /// CHAT
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
