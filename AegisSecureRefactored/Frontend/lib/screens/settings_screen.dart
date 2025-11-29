import 'package:flutter/material.dart';
import 'package:gmailclone/services/sms_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

const Color primaryBlue = Color(0xFF1F2A6E);
const String autoFetchSmsKey = 'auto_fetch_sms_enabled';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  State<SettingsScreen> createState() => SettingsScreenState();
}

class SettingsScreenState extends State<SettingsScreen> {
  bool autoFetchSms = SmsService.allowSyncingSMS;

  Future<void> loadAutoFetchPreference() async {
    final prefs = await SharedPreferences.getInstance();
    final storedValue = prefs.getBool(autoFetchSmsKey);

    if (storedValue != null) {
      setState(() {
        autoFetchSms = storedValue;
        SmsService.allowSyncingSMS = storedValue;
      });
    }
  }

  @override
  void initState() {
    super.initState();
    loadAutoFetchPreference();
  }

  Future<void> _onToggle(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(autoFetchSmsKey, value);

    setState(() {
      SmsService.allowSyncingSMS = value;
      autoFetchSms = value;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        centerTitle: false,
        title: const Text(
          'Settings',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.black,
          ),
        ),
        backgroundColor: Colors.white,
        foregroundColor: primaryBlue,
        elevation: 1,
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
        children: [
          SwitchListTile(
            title: const Text(
              "Automatically fetch SMS messages",
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
            ),
            activeColor: primaryBlue,
            value: autoFetchSms,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16),
            onChanged: (value) {
              _onToggle(value);
            },
          ),
          const SizedBox(height: 16),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              "Enabling this will sync SMS messages automatically in the background.",
              style: TextStyle(color: Colors.black54, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}
