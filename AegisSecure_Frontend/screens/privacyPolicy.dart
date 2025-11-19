import 'package:flutter/material.dart';

class PrivacyPolicyPage extends StatelessWidget {
  const PrivacyPolicyPage({Key? key}) : super(key: key);
  static const Color primaryColor = Color(0xFF1F2A6E);
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: primaryColor,
        title: const Text(
          'Privacy Policy',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        elevation: 1,
        centerTitle: false,
      ),
      body: Container(
        color: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
        child: SingleChildScrollView(
          child: DefaultTextStyle(
            style: const TextStyle(
              color: Colors.black87,
              fontSize: 16,
              height: 1.5,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'AegisSecure — Privacy Policy',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: primaryColor,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Last updated: November 8, 2025',
                  style: TextStyle(fontSize: 14, fontStyle: FontStyle.italic),
                ),
                const SizedBox(height: 16),
                RichText(
                  text: TextSpan(
                    style: const TextStyle(color: Colors.black87),
                    children: [
                      const TextSpan(
                        text: '1. Overview\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'AegisSecure values your privacy. This Policy explains what we collect, how we use it, and your rights.\n\n',
                      ),
                      const TextSpan(
                        text: '2. Data We Collect\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'Account Data: Name, email address, device identifiers (if provided during signup).\n\nCredentials: Passwords (stored encrypted). We never store plaintext passwords.\n\nMessage Data: Email and SMS content you elect to scan. These messages are analyzed to detect scams.\n\nUsage & Diagnostics: App usage metrics, error logs, crash reports, and performance data to improve the service.\n\n',
                      ),
                      const TextSpan(
                        text: '3. How Message Data Is Processed\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'When you request a scan, message content is processed either locally on-device or transmitted to our secure backend via encrypted API calls to run ML models.\n\nWe may use third-party processing services; any external service used will be contractually bound to maintain confidentiality and security.\n\nWe do not sell your messages or personal content to third parties.\n\n',
                      ),
                      const TextSpan(
                        text: '4. Storage & Retention\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'Transient Processing: Scanned message content is analyzed to produce results. Unless you explicitly permit storage, message content is deleted after processing.\n\nOptional Storage: If your app settings or features require saving scan history (e.g., to show past scans), we will store that data only with your explicit consent.\n\nAccount Data: Basic account data may be retained until you delete your account or as required by law.\n\n',
                      ),
                      const TextSpan(
                        text: '5. Passwords & Security\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'Passwords are stored encrypted in our database using recommended cryptographic hashing + salt.\n\nWe protect data in transit using TLS/HTTPS for all API calls.\n\nWe implement industry-standard practices for data security, access controls, and vulnerability management.\n\n',
                      ),
                      const TextSpan(
                        text: '6. Third-Party Services & APIs\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'Our ML model may be hosted or served through internal or third-party APIs. Any third-party provider we use will be required to protect data and will access only the data necessary to provide the service.\n\nWe may share data to comply with legal obligations or to investigate abuse or security incidents.\n\n',
                      ),
                      const TextSpan(
                        text: '7. Analytics & Improvements\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'We collect anonymized/aggregated usage statistics to improve models and the app. Where possible, we aggregate or de-identify data to protect privacy.\n\n',
                      ),
                      const TextSpan(
                        text: '8. Your Choices & Rights\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'Access / Deletion: You may request access to or deletion of your account and stored data by contacting ',
                      ),
                      TextSpan(
                        text: 'aegissecure25@gmail.com',
                        style: TextStyle(
                          color: primaryColor,
                          decoration: TextDecoration.underline,
                        ),
                      ),
                      const TextSpan(
                        text:
                            '.\n\nOpt-out: You can opt out of optional data collection features (e.g., analytics, saving scan history).\n\nChildren: Our service is not intended for users under 13. If you are a parent and believe we hold data for a child, contact us.\n\n',
                      ),
                      const TextSpan(
                        text: '9. International Transfers\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'If data is transferred internationally for processing, we will take steps to ensure it is protected according to applicable laws.\n\n',
                      ),
                      const TextSpan(
                        text: '10. Changes to Policy\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'We may update this Policy. Updates will be posted in the app and this page with the new “Last updated” date.\n\n',
                      ),
                      const TextSpan(
                        text: '11. Contact\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      TextSpan(
                        text:
                            'Privacy questions, data requests, or security concerns: ',
                      ),
                      TextSpan(
                        text: 'aegissecure25@gmail.com',
                        style: TextStyle(
                          color: primaryColor,
                          decoration: TextDecoration.underline,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}