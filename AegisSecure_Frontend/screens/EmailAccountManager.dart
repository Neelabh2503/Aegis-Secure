import 'dart:async';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';

class EmailAccountManager extends StatefulWidget {
  const EmailAccountManager({Key? key}) : super(key: key);

  @override
  State<EmailAccountManager> createState() => _EmailAccountManagerState();
}

class _EmailAccountManagerState extends State<EmailAccountManager> {
  String? currentUserName;
  String? currentUserEmail;
  Timer? _refreshTimer;
  List<Map<String, String>> connectedAccounts = [];
  bool _loading = true;
  OverlayEntry? _overlayEntry;

  String? activeAccountEmail; 
  @override
  @override
  void initState() {
    super.initState();
    _loadAccounts();
    _refreshTimer = Timer.periodic(const Duration(seconds: 5), (timer) {
      _loadAccounts();
    });
  }

  Future<void> _loadAccounts() async {
    try {
      final user = await ApiService.fetchCurrentUser();
      final accounts = await ApiService.fetchConnectedAccounts();

      final name =
          (user['name'] ?? user['username'] ?? user['gmail_name'] ?? 'User')
              .toString();
      final email = (user['email'] ?? user['gmail_email'] ?? '').toString();

      final List<Map<String, String>> normalizedAccounts =
          (accounts['accounts'] ?? accounts ?? []).map<Map<String, String>>((
            a,
          ) {
            return {
              'name':
                  (a['name'] ?? a['gmail_name'] ?? a['gmail_email'] ?? 'User')
                      .toString(),
              'email': (a['email'] ?? a['gmail_email'] ?? '').toString(),
            };
          }).toList();

      final prefs = await SharedPreferences.getInstance();
      final savedActive = prefs.getString('active_linked_email');

      setState(() {
        currentUserName = name;
        currentUserEmail = email;
        connectedAccounts = normalizedAccounts;
        activeAccountEmail = savedActive;
        _loading = false;
      });
    } catch (e) {
      print("Failed to load accounts: $e");
      setState(() => _loading = false);
    }
  }

  Future<void> _setActiveAccount(String email) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('active_linked_email', email);
    setState(() => activeAccountEmail = email);
  }

  Future<void> _deleteAccount(String gmailEmail) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          "Remove Account",
          style: TextStyle(fontWeight: FontWeight.w600),
        ),
        content: Text("Are you sure you want to unlink $gmailEmail?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text("Cancel"),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text("Remove", style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    try {
      await ApiService.deleteConnectedAccount(gmailEmail);
      if (activeAccountEmail == gmailEmail) {
        final remaining = connectedAccounts
            .where((a) => a['email'] != gmailEmail)
            .toList();
        final newActive = remaining.isNotEmpty
            ? remaining.first['email']
            : null;

        final prefs = await SharedPreferences.getInstance();
        if (newActive == null) {
          await prefs.remove('active_linked_email');
        } else {
          await prefs.setString('active_linked_email', newActive);
        }

        setState(() => activeAccountEmail = newActive);
      }

      _showCapsuleMessage("Account removed");
      _loadAccounts();
    } catch (e) {
      print("Failed to delete account: $e");
      _showCapsuleMessage("Failed to remove account", error: true);
    }
  }

  void _showCapsuleMessage(String message, {bool error = false}) {
    _overlayEntry?.remove();

    _overlayEntry = OverlayEntry(
      builder: (context) => Positioned(
        bottom: 80,
        left: MediaQuery.of(context).size.width * 0.1,
        right: MediaQuery.of(context).size.width * 0.1,
        child: Material(
          color: Colors.transparent,
          child: AnimatedOpacity(
            opacity: 1,
            duration: const Duration(milliseconds: 250),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: error ? Colors.red.shade400 : Colors.black87,
                borderRadius: BorderRadius.circular(50),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black26,
                    blurRadius: 8,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: Center(
                child: Text(
                  message,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );

    Overlay.of(context).insert(_overlayEntry!);
    Future.delayed(const Duration(seconds: 2), () {
      _overlayEntry?.remove();
      _overlayEntry = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final String avatarLetter = (currentUserName?.isNotEmpty ?? false)
        ? currentUserName![0].toUpperCase()
        : '?';

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0.4,
        automaticallyImplyLeading: false,
        title: const Text(
          "Mail Inbox Information",
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.close, color: Colors.black),
            onPressed: () => Navigator.pop(context),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  if (currentUserEmail != null && currentUserEmail!.isNotEmpty)
                    Text(
                      currentUserEmail!,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w500,
                        color: Colors.black87,
                      ),
                    ),
                  const SizedBox(height: 12),
                  CircleAvatar(
                    radius: 38,
                    backgroundColor: Colors.purple.shade400,
                    child: Text(
                      avatarLetter,
                      style: const TextStyle(
                        fontSize: 32,
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    "Hi, ${currentUserName ?? 'there'}!",
                    style: const TextStyle(fontSize: 16, color: Colors.black87),
                  ),
                  const SizedBox(height: 20),
                  OutlinedButton(
                    onPressed: () {},
                    style: OutlinedButton.styleFrom(
                      shape: const StadiumBorder(),
                      side: BorderSide(color: Colors.grey.shade400),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 10,
                      ),
                    ),
                    child: const Text("Manage your Accounts"),
                  ),
                  const SizedBox(height: 30),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      "Switch account",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey.shade800,
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  Expanded(
                    child: SingleChildScrollView(
                      child: Container(
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey.shade300),
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.grey.shade200,
                              blurRadius: 6,
                              offset: const Offset(0, 3),
                            ),
                          ],
                        ),
                        child: Column(
                          children: [
                            if (connectedAccounts.isEmpty)
                              Container(
                                padding: const EdgeInsets.all(20),
                                child: const Center(
                                  child: Text(
                                    "No connected accounts yet.",
                                    style: TextStyle(color: Colors.grey),
                                  ),
                                ),
                              )
                            else
                              for (
                                int i = 0;
                                i < connectedAccounts.length;
                                i++
                              ) ...[
                                Container(
                                  color:
                                      connectedAccounts[i]['email'] ==
                                          activeAccountEmail
                                      ? Colors.blue.shade50
                                      : Colors.transparent,
                                  child: ListTile(
                                    leading: CircleAvatar(
                                      backgroundColor: _getColorForLetter(
                                        connectedAccounts[i]['name'] ??
                                            connectedAccounts[i]['email'] ??
                                            '',
                                      ),
                                      child: Text(
                                        (connectedAccounts[i]['name'] ??
                                                connectedAccounts[i]['email'] ??
                                                '?')[0]
                                            .toUpperCase(),
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                    title: Row(
                                      children: [
                                        Expanded(
                                          child: Text(
                                            connectedAccounts[i]['name'] ?? '',
                                            style: const TextStyle(
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                    subtitle: Text(
                                      connectedAccounts[i]['email'] ?? '',
                                      style: const TextStyle(
                                        color: Colors.black54,
                                      ),
                                    ),
                                    trailing: IconButton(
                                      icon: const Icon(
                                        Icons.delete_outline,
                                        color: Colors.redAccent,
                                      ),
                                      onPressed: () => _deleteAccount(
                                        connectedAccounts[i]['email'] ?? '',
                                      ),
                                    ),
                                    onTap: () async {
                                      final email =
                                          connectedAccounts[i]['email'] ?? '';
                                      await _setActiveAccount(email);
                                      Navigator.pop(context, email);
                                    },
                                  ),
                                ),
                                if (i != connectedAccounts.length - 1)
                                  Divider(
                                    height: 1,
                                    color: Colors.grey.shade300,
                                  ),
                              ],
                            const Divider(height: 1),
                            ListTile(
                              leading: const CircleAvatar(
                                backgroundColor: Colors.transparent,
                                child: Icon(Icons.add, color: Colors.black54),
                              ),
                              title: const Text(
                                "Add another account",
                                style: TextStyle(fontWeight: FontWeight.w500),
                              ),
                              onTap: () async {
                                await ApiService.launchGoogleLogin();
                                await Future.delayed(
                                  const Duration(seconds: 10),
                                );
                                await _loadAccounts();
                                _showCapsuleMessage(
                                  "Account added successfully",
                                );
                              },
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),
                  const Text(
                    "Privacy Policy • Terms of Service",
                    style: TextStyle(color: Colors.grey, fontSize: 13),
                  ),
                ],
              ),
            ),
    );
  }

  Color _getColorForLetter(String text) {
    final colors = [
      Colors.blue,
      Colors.green,
      Colors.red,
      Colors.orange,
      Colors.purple,
      Colors.teal,
      Colors.amber,
      Colors.indigo,
      Colors.pink,
      Colors.brown,
    ];
    return colors[text.codeUnitAt(0) % colors.length];
  }
}
