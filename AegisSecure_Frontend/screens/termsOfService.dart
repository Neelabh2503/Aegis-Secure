import 'package:flutter/material.dart';

class TermsOfServicePage extends StatelessWidget {
  const TermsOfServicePage({Key? key}) : super(key: key);

  static const Color primaryColor = Color(0xFF1F2A6E);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: primaryColor,
        title: const Text(
          'Terms of Service',
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
                  'AegisSecure — Terms of Service',
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
                        text: '1. Acceptance of Terms\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'By creating an account or using AegisSecure, you agree to these Terms. If you do not agree, do not use the app.\n\n',
                      ),
                      const TextSpan(
                        text: '2. Service Description\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'AegisSecure provides AI-based analysis to detect potential scam or phishing content in emails and SMS. The service delivers classifications (e.g., “Likely Scam”, “Likely Safe”), confidence scores, and highlighted sections of text the system flags as suspicious.\n\n',
                      ),
                      const TextSpan(
                        text: '3. User Responsibilities\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'You agree to use AegisSecure lawfully and not to attempt to reverse-engineer, tamper with, or misuse the service. Keep your account credentials secure. You are responsible for the content you provide for scanning.\n\n',
                      ),
                      const TextSpan(
                        text: '4. AI & API Processing\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'AegisSecure uses machine learning models to analyze content. Processing may occur locally or via secure backend API calls to our servers or third-party services we employ. Results and explanations are generated automatically. AI outputs are informational and may be imperfect.\n\n',
                      ),
                      const TextSpan(
                        text: '5. No Guarantee & Liability Limit\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'We aim for accuracy but do not guarantee detection of all scams. You agree that AegisSecure, its owners, employees, and partners are not liable for any direct or indirect losses arising from use of the service, including decisions or actions you take based on the app’s outputs.\n\n',
                      ),
                      const TextSpan(
                        text: '6. Account Security & Passwords\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      TextSpan(
                        text:
                            'You are responsible for maintaining the confidentiality of your password. We store user passwords in encrypted form in our database. If you suspect your account is compromised, contact us immediately at ',
                      ),
                      TextSpan(
                        text: 'aegissecure@gmail.com',
                        style: TextStyle(
                          color: primaryColor,
                          decoration: TextDecoration.underline,
                        ),
                      ),
                      const TextSpan(text: '.\n\n'),
                      const TextSpan(
                        text: '7. Intellectual Property\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'All intellectual property in the app (code, UI, logos, content) is owned by AegisSecure or its licensors. You may not copy or reuse items without our permission.\n\n',
                      ),
                      const TextSpan(
                        text: '8. Termination\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'We may suspend or terminate accounts for violations or abuse. Upon termination, your access to the service will end; how data is retained or deleted is governed by the Privacy Policy.\n\n',
                      ),
                      const TextSpan(
                        text: '9. Changes to Terms\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'We may update these Terms. We will post the new Terms and update the “Last updated” date. Continued use after changes constitutes acceptance.\n\n',
                      ),
                      const TextSpan(
                        text: '10. Governing Law\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      const TextSpan(
                        text:
                            'These Terms are governed by the laws applicable in the company’s jurisdiction. (If you need a specific jurisdiction clause, insert it here.)\n\n',
                      ),
                      const TextSpan(
                        text: '11. Contact\n',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: primaryColor,
                        ),
                      ),
                      TextSpan(text: 'Questions about these Terms: '),
                      TextSpan(
                        text: 'aegissecure@gmail.com',
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
