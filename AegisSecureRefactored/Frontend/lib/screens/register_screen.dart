import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';

import '../screens/verify_otp_screen.dart';
import '../services/api_service.dart';

class RegisterScreen extends StatefulWidget {
  @override
  RegisterScreenState createState() => RegisterScreenState();
}

class RegisterScreenState extends State<RegisterScreen> {
  final nameController = TextEditingController();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  final confirmPasswordController = TextEditingController();

  bool showPassword = false;
  bool showconfirmPassword = false;
  bool loading = false;
  bool _agree = false;

  bool showPasswordInfo = false;
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

  void _validatePassword(String password) {
    setState(() {
      hasUppercase = password.contains(RegExp(r'[A-Z]'));
      hasLowercase = password.contains(RegExp(r'[a-z]'));
      hasNumber = password.contains(RegExp(r'[0-9]'));
      hasSpecialChar = password.contains(RegExp(r'[!@#\$%^&*(),.?":{}|<>]'));
      hasMinLength = password.length >= 8;
    });
  }

  String? nameError;
  String? emailError;
  String? passwordError;
  String? confirmError;

  void register() async {
    final name = nameController.text.trim();
    final email = emailController.text.trim();
    final password = passwordController.text.trim();
    final confirm = confirmPasswordController.text.trim();

    setState(() {
      nameError = name.isEmpty ? "Please enter your name" : null;
      emailError = email.isEmpty ? "Please enter your email" : null;
      passwordError = password.isEmpty ? "Please enter your password" : null;
      confirmError = confirm.isEmpty
          ? "Please confirm your password"
          : confirm != password
          ? "Passwords do not match"
          : null;
    });

    if (!_agree) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Please agree to the terms & conditions")),
      );
      return;
    }

    if (!hasMinLength ||
        !hasUppercase ||
        !hasLowercase ||
        !hasNumber ||
        !hasSpecialChar) {
      setState(() {
        passwordError = "Password does not meet all requirements";
      });
      setState(() {
        passwordError = "Password does not meet all requirements";
      });
      return;
    }

    if (nameError != null ||
        emailError != null ||
        passwordError != null ||
        confirmError != null)
      return;

    setState(() => loading = true);

    try {
      final res = await ApiService.registerUser(name, email, password);

      if (res.statusCode == 200) {
        // print('✅' + email);
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => VerifyOtpScreen(email: email)),
        );
      } else {
        setState(() {
          print(res.statusCode);
          emailError = "This Email is Already Registered!";
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Error connecting to server")));
    } finally {
      setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                SizedBox(height: 24),
                RichText(
                  textAlign: TextAlign.center,
                  text: TextSpan(
                    text: "Aegis ",
                    style: TextStyle(
                      fontFamily: 'Jersey20',
                      color: Color(0xFF1F2A6E),
                      fontSize: 60,
                      fontWeight: FontWeight.w800,
                    ),
                    children: [
                      TextSpan(
                        text: "Secure",
                        style: TextStyle(
                          color: Colors.grey.shade600,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),

                SizedBox(height: 16),

                Text(
                  "Create your account",
                  style: TextStyle(
                    fontSize: 18,
                    color: Colors.black87,
                    fontWeight: FontWeight.w600,
                  ),
                ),

                SizedBox(height: 32),
                TextField(
                  controller: nameController,
                  maxLength: 50,
                  decoration: InputDecoration(
                    labelText: "Full Name",
                    errorText: nameError,
                    labelStyle: TextStyle(color: Colors.grey.shade700),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),

                SizedBox(height: 16),
                TextField(
                  controller: emailController,
                  decoration: InputDecoration(
                    labelText: "Email",
                    hintText: "ex: user@aegissecure.com",
                    errorText: emailError,
                    labelStyle: TextStyle(color: Colors.grey.shade700),
                    hintStyle: TextStyle(color: Colors.grey.shade400),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),

                SizedBox(height: 16),

                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: passwordController,
                            obscureText: !showPassword,
                            maxLength: 64,
                            onChanged: _validatePassword,
                            decoration: InputDecoration(
                              labelText: "Password",
                              errorText: passwordError,
                              labelStyle: TextStyle(
                                color: Colors.grey.shade700,
                              ),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              suffixIcon: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  IconButton(
                                    icon: const Icon(Icons.info_outline),
                                    color: Colors.blueGrey,
                                    onPressed: () {
                                      setState(() {
                                        showPasswordInfo = !showPasswordInfo;
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
                        ),
                      ],
                    ),
                    if (showPasswordInfo)
                      Padding(
                        padding: const EdgeInsets.only(top: 8, left: 8),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildPasswordRule(
                              "At least 8 characters",
                              hasMinLength,
                            ),
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
                            _buildPasswordRule(
                              "At least one number",
                              hasNumber,
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
                SizedBox(height: 16),
                TextField(
                  controller: confirmPasswordController,
                  obscureText: !showconfirmPassword,
                  decoration: InputDecoration(
                    labelText: "Confirm Password",
                    errorText: confirmError,
                    labelStyle: TextStyle(color: Colors.grey.shade700),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    suffixIcon: IconButton(
                      icon: Icon(
                        showconfirmPassword
                            ? Icons.visibility
                            : Icons.visibility_off_outlined,
                        color: Colors.grey.shade600,
                      ),
                      onPressed: () {
                        setState(() {
                          showconfirmPassword = !showconfirmPassword;
                        });
                      },
                    ),
                  ),
                ),
                SizedBox(height: 16),
                Row(
                  children: [
                    Checkbox(
                      value: _agree,
                      activeColor: const Color(0xFF1F2A6E),
                      onChanged: (val) {
                        setState(() => _agree = val ?? false);
                      },
                    ),
                    Expanded(
                      child: RichText(
                        text: TextSpan(
                          style: TextStyle(
                            color: Colors.grey.shade700,
                            fontSize: 14,
                          ),
                          children: [
                            const TextSpan(text: "I agree to the "),
                            TextSpan(
                              text: "Terms",
                              style: const TextStyle(
                                decoration: TextDecoration.underline,
                                color: Color(0xFF1F2A6E),
                                fontWeight: FontWeight.bold,
                              ),
                              recognizer: TapGestureRecognizer()
                                ..onTap = () {
                                  Navigator.of(context).pushNamed('/terms');
                                },
                            ),
                            const TextSpan(text: " and "),
                            TextSpan(
                              text: "Privacy Policy",
                              style: const TextStyle(
                                decoration: TextDecoration.underline,
                                color: Color(0xFF1F2A6E),
                                fontWeight: FontWeight.bold,
                              ),
                              recognizer: TapGestureRecognizer()
                                ..onTap = () {
                                  Navigator.of(context).pushNamed('/privacy');
                                },
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),

                SizedBox(height: 20),
                loading
                    ? CircularProgressIndicator()
                    : ElevatedButton(
                        onPressed: register,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1F2A6E),
                          minimumSize: Size(double.infinity, 50),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                        child: Text(
                          "SIGN UP",
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                            letterSpacing: 0.5,
                            color: Colors.white,
                          ),
                        ),
                      ),
                SizedBox(height: 24),
                GestureDetector(
                  onTap: () => Navigator.pushNamed(context, '/login'),
                  child: RichText(
                    text: TextSpan(
                      text: "Already have an account? ",
                      style: TextStyle(color: Colors.black54),
                      children: [
                        TextSpan(
                          text: "SIGN IN",
                          style: TextStyle(
                            color: Colors.green.shade700,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
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
