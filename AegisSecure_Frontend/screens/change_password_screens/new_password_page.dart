import 'package:flutter/material.dart';
import 'package:gmailclone/services/api_service.dart';

class NewPasswordPage extends StatefulWidget {
  final String email;
  final String otp;

  const NewPasswordPage({required this.email, required this.otp, super.key});

  @override
  State<NewPasswordPage> createState() => _NewPasswordPageState();
}

class _NewPasswordPageState extends State<NewPasswordPage> {
  final newPasswordController = TextEditingController();
  final confirmPasswordController = TextEditingController();
  bool showPassword = false;
  bool showConfirmPassword = false;
  bool loading = false;
  String? confirmPasswordError;
  String? newPasswordError;
  bool _showPasswordInfo = false;
  bool hasSpecialChar = false;
  bool hasUppercase = false;
  bool hasLowercase = false;
  bool hasNumber = false;
  bool hasMinLength = false;

  Widget _buildPasswordRule(String text, bool satisfied) {
    return Row(
      children: [
        Icon(
          satisfied ? Icons.check_circle : Icons.cancel,
          color: satisfied ? Colors.green : Colors.red,
          size: 18,
        ),
        const SizedBox(width: 6),
        Text(
          text,
          style: TextStyle(
            color: satisfied ? Colors.green : Colors.red,
            fontSize: 13,
          ),
        ),
      ],
    );
  }

  void validatePassword(String password) {
    setState(() {
      hasUppercase = password.contains(RegExp(r'[A-Z]'));
      hasLowercase = password.contains(RegExp(r'[a-z]'));
      hasNumber = password.contains(RegExp(r'[0-9]'));
      hasSpecialChar = password.contains(RegExp(r'[!@#\$%^&*(),.?":{}|<>]'));
      hasMinLength = password.length >= 8;
    });
  }

  // Future<void> resetPassword() async {
  //   final newPassword = newPasswordController.text.trim();
  //   final confirmPassword = confirmPasswordController.text.trim();
  //
  //   if (newPassword.isEmpty || confirmPassword.isEmpty) {
  //     ScaffoldMessenger.of(context).showSnackBar(
  //       const SnackBar(content: Text("Please fill in all fields.")),
  //     );
  //     return;
  //   }
  //
  //   if (newPassword != confirmPassword) {
  //     setState(() {
  //       confirmPasswordError = "Passwords do not match";
  //     });
  //     return;
  //   } else {
  //     setState(() {
  //       confirmPasswordError = null;
  //     });
  //   }
  //
  //   setState(() => loading = true);
  //   final res = await ApiService.resetPassword(
  //     widget.email,
  //     widget.otp,
  //     newPassword,
  //   );
  //   setState(() => loading = false);
  //
  //   if (res.statusCode == 200) {
  //     ScaffoldMessenger.of(context).showSnackBar(
  //       const SnackBar(content: Text("Password changed successfully.")),
  //     );
  //     Navigator.pushReplacementNamed(context, '/login');
  //   } else {
  //     ScaffoldMessenger.of(
  //       context,
  //     ).showSnackBar(SnackBar(content: Text("Failed: ${res.body}")));
  //   }
  // }

  Future<void> resetPassword() async {
    final newPassword = newPasswordController.text.trim();
    final confirmPassword = confirmPasswordController.text.trim();

    // 1. Empty fields
    if (newPassword.isEmpty || confirmPassword.isEmpty) {
      setState(() {
        newPasswordError = "Password cannot be empty";
      });
      return;
    }

    // 2. Strength rules
    if (!hasMinLength ||
        !hasUppercase ||
        !hasLowercase ||
        !hasNumber ||
        !hasSpecialChar) {
      setState(() {
        newPasswordError = "Password does not meet all requirements";
      });
      return;
    } else {
      setState(() {
        newPasswordError = null;
      });
    }

    // 3. Match check
    if (newPassword != confirmPassword) {
      setState(() {
        confirmPasswordError = "Passwords do not match";
      });
      return;
    } else {
      setState(() {
        confirmPasswordError = null;
      });
    }

    // 4. Call API
    setState(() => loading = true);
    final res = await ApiService.resetPassword(
      widget.email,
      widget.otp,
      newPassword,
    );
    setState(() => loading = false);

    if (res.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Password changed successfully.")),
      );
      Navigator.pushReplacementNamed(context, '/login');
    } else {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Failed: ${res.body}")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          "Change Password",
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.w600),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Enter your new password below",
              style: TextStyle(
                fontSize: 16,
                color: Colors.black87,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: newPasswordController,
              obscureText: !showPassword,
              onChanged: validatePassword,
              decoration: InputDecoration(
                labelText: "New Password",
                errorText: newPasswordError,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                prefixIcon: const Icon(Icons.lock_outline),
                suffixIcon: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.info_outline),
                      color: Colors.blueGrey,
                      onPressed: () {
                        setState(() {
                          _showPasswordInfo = !_showPasswordInfo;
                        });
                      },
                    ),
                    IconButton(
                      icon: Icon(
                        showPassword
                            ? Icons.visibility
                            : Icons.visibility_off_outlined,
                        color: Colors.grey.shade600,
                      ),
                      onPressed: () {
                        setState(() {
                          showPassword = !showPassword;
                        });
                      },
                    ),
                  ],
                ),
              ),
            ),
            if (_showPasswordInfo)
              Padding(
                padding: const EdgeInsets.only(top: 8, left: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildPasswordRule("At least 8 characters", hasMinLength),
                    _buildPasswordRule(
                      "At least one uppercase letter",
                      hasUppercase,
                    ),
                    _buildPasswordRule(
                      "At least one lowercase letter",
                      hasLowercase,
                    ),
                    _buildPasswordRule(
                      "At least one special character",
                      hasSpecialChar,
                    ),
                    _buildPasswordRule("At least one number", hasNumber),
                  ],
                ),
              ),
            const SizedBox(height: 16),
            TextField(
              controller: confirmPasswordController,
              obscureText: !showConfirmPassword,
              decoration: InputDecoration(
                labelText: "Confirm Password",
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                prefixIcon: const Icon(Icons.lock),
                errorText: confirmPasswordError,
                suffixIcon: IconButton(
                  icon: Icon(
                    showConfirmPassword
                        ? Icons.visibility
                        : Icons.visibility_off_outlined,
                    color: Colors.grey.shade600,
                  ),
                  onPressed: () => setState(
                    () => showConfirmPassword = !showConfirmPassword,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 32),

            Center(
              child: loading
                  ? const CircularProgressIndicator(color: Color(0xFF1F2A6E))
                  : ElevatedButton(
                      onPressed: resetPassword,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF1F2A6E),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        minimumSize: const Size(double.infinity, 48),
                      ),
                      child: const Text(
                        "Update Password",
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
      ),
    );
  }
}
