import 'package:flutter/material.dart';
import 'package:pin_code_fields/pin_code_fields.dart';

import '../services/api_service.dart';

class VerifyOtpScreen extends StatefulWidget {
  final String email;
  const VerifyOtpScreen({required this.email});

  @override
  State<VerifyOtpScreen> createState() => _VerifyOtpScreenState();
}

class _VerifyOtpScreenState extends State<VerifyOtpScreen> {
  String otp = "";
  bool _loading = false;

  Future<void> verifyOtp() async {
    if (otp.isEmpty || otp.length < 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please enter the 6-digit OTP")),
      );
      return;
    }

    setState(() => _loading = true);

    final res = await ApiService.verifyOtp(widget.email, otp);
    if (res.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("OTP verified successfully!")),
      );
      Navigator.pushReplacementNamed(context, '/login');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Invalid or expired OTP. Please try again."),
        ),
      );
    }

    setState(() => _loading = false);
  }

  Future<void> resendOtp() async {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text("Resending OTP...")));
    try {
      final res = await ApiService.sendOtp(widget.email);
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("OTP resent successfully")),
        );
      } else {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text("Failed to resend OTP")));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Network error while resending OTP")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "Verification code",
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                  color: Colors.black,
                ),
              ),
              const SizedBox(height: 8),
              RichText(
                text: TextSpan(
                  text: "We have sent the code verification to ",
                  style: TextStyle(color: Colors.grey.shade700, fontSize: 15),
                  children: [
                    TextSpan(
                      text: widget.email,
                      style: const TextStyle(
                        color: Colors.black,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 40),

              // 6-digit OTP Boxes
              PinCodeTextField(
                appContext: context,
                length: 6,
                keyboardType: TextInputType.number,
                onChanged: (value) => otp = value,
                pinTheme: PinTheme(
                  shape: PinCodeFieldShape.box,
                  borderRadius: BorderRadius.circular(10),
                  fieldHeight: 55,
                  fieldWidth: 45,
                  activeColor: Colors.deepPurple,
                  selectedColor: Colors.deepPurpleAccent,
                  inactiveColor: Colors.grey.shade300,
                  activeFillColor: Colors.grey.shade100,
                  selectedFillColor: Colors.white,
                  inactiveFillColor: Colors.white,
                ),
                enableActiveFill: true,
              ),

              const SizedBox(height: 12),

              // Validity Text
              const Center(
                child: Text(
                  "This code is valid for 5 minutes.",
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ),

              const SizedBox(height: 35),

              // Buttons Row
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: resendOtp,
                      style: OutlinedButton.styleFrom(
                        side: BorderSide(color: Colors.grey.shade400),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: const Text(
                        "Resend",
                        style: TextStyle(
                          color: Colors.black87,
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: verifyOtp,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF6C63FF),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: _loading
                          ? const SizedBox(
                              height: 22,
                              width: 22,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2,
                              ),
                            )
                          : const Text(
                              "Confirm",
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}