import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../screens/verify_otp_screen.dart';
import '../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  bool _loading = false;
  String? emailError;
  String? passwordError;

  void _showErrorDialog(BuildContext context, String message) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text(
            "Error",
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("OK"),
            ),
          ],
        );
      },
    );
  }

  void login() async {
    final email = emailController.text.trim();
    final password = passwordController.text.trim();

    // Basic validation
    setState(() {
      emailError = email.isEmpty ? "Please enter your email" : null;
      passwordError = password.isEmpty ? "Please enter your password" : null;
    });

    if (emailError != null || passwordError != null) return;

    setState(() => _loading = true);

    try {
      final res = await ApiService.loginUser(email, password);

      print("DEBUG: Response status = ${res.statusCode}");
      print("DEBUG: Response body = ${res.body}");

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);

        final token = data['token'];
        final verifiedRaw = data['verified'];
        final isVerified =
            verifiedRaw == true || verifiedRaw == "true" || verifiedRaw == 1;

        print("DEBUG: Raw verified value = $verifiedRaw");
        print("DEBUG: Parsed isVerified = $isVerified");
        print("DEBUG: Token = $token");

        if (!isVerified) {
          setState(() {
            passwordError = "Please verify your email before logging in.";
          });
          return; 
        }

        if (token == null || token.isEmpty) {
          setState(() {
            passwordError = "Failed to get authentication token.";
          });
          return;
        }

      
        SharedPreferences prefs = await SharedPreferences.getInstance();
        await prefs.setString('jwt_token', token);

       
        try {
          final userRes = await ApiService.fetchCurrentUser();
          print("DEBUG: Current user = $userRes");
        } catch (e) {
          print("DEBUG: Could not fetch current user: $e");
          
        }

       
        Navigator.pushReplacementNamed(context, '/home');
      } else if (res.statusCode == 401 || res.statusCode == 400) {
        setState(() {
          passwordError = "Invalid email or password";
        });
      } else {
        setState(() {
          passwordError = "Unexpected error: ${res.statusCode}";
        });
      }
    } catch (e) {
      print("DEBUG: Exception caught during login: $e");
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Error connecting to server: $e")));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: EdgeInsets.symmetric(horizontal: 28, vertical: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // Logo
                SizedBox(
                  height: MediaQuery.of(context).size.width * 0.70,
                  width: MediaQuery.of(context).size.width * 0.70,
                  child: Image.asset(
                    'assets/images/logo.png',
                    fit: BoxFit.contain,
                  ),
                ),
               
                RichText(
                  textAlign: TextAlign.center,
                  text: TextSpan(
                    text: "Aegis ",
                    style: TextStyle(
                      fontFamily: 'Jersey20',
                      color: Colors.blue.shade900,
                      fontSize: 40,
                      fontWeight: FontWeight.w800,
                    ),
                    children: [
                      TextSpan(
                        text: "Secure",
                        style: TextStyle(
                          fontFamily: 'Jersey20',
                          color: Colors.grey.shade600,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),

                SizedBox(height: 16),
                Text(
                  "Sign in your account",
                  style: TextStyle(
                    fontSize: 18,
                    color: Colors.black87,
                    fontWeight: FontWeight.w600,
                  ),
                ),

                SizedBox(height: 32),

               
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

                // Password Field
                TextField(
                  controller: passwordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: "Password",
                    errorText: passwordError,
                    labelStyle: TextStyle(color: Colors.grey.shade700),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),

                SizedBox(height: 28),

                
                _loading
                    ? CircularProgressIndicator()
                    : ElevatedButton(
                        onPressed: login,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1F2A6E),
                          minimumSize: Size(double.infinity, 50),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                        child: Text(
                          "SIGN IN",
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                            letterSpacing: 0.5,
                            color: Colors.white,
                          ),
                        ),
                      ),

                SizedBox(height: 20),

                Text(
                  "or sign in with",
                  style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
                ),

                SizedBox(height: 12),

                // Social Icons
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _socialButton(Icons.mail_outline),
                    SizedBox(width: 25),
                    _socialButton(Icons.phone_outlined),
                  ],
                ),

                SizedBox(height: 24),

                // Sign Up Link
                GestureDetector(
                  onTap: () => Navigator.pushNamed(context, '/register'),
                  child: RichText(
                    text: TextSpan(
                      text: "Don’t have an account? ",
                      style: TextStyle(color: Colors.black54),
                      children: [
                        TextSpan(
                          text: "SIGN UP",
                          style: TextStyle(
                            color: Colors.green.shade700,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                
                const SizedBox(height: 24), 
                Align(
                  alignment: Alignment.center,
                  child: TextButton(
                    onPressed: _loading
                        ? null
                        : () async {
                            final outerContext =
                                context; 
                            final emailControllerDialog =
                                TextEditingController();

                            await showDialog(
                              context: context,
                              builder: (dialogContext) {
                                return AlertDialog(
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                  title: const Text(
                                    "Verify Your Email",
                                    style: TextStyle(
                                      fontWeight: FontWeight.w700,
                                      fontSize: 18,
                                    ),
                                  ),
                                  content: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      const Text(
                                        "Enter your registered email address to receive a verification code.",
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: Colors.black87,
                                        ),
                                      ),
                                      const SizedBox(height: 16),
                                      TextField(
                                        controller: emailControllerDialog,
                                        keyboardType:
                                            TextInputType.emailAddress,
                                        decoration: InputDecoration(
                                          hintText: "ex: user@aegissecure.com",
                                          border: OutlineInputBorder(
                                            borderRadius: BorderRadius.circular(
                                              10,
                                            ),
                                          ),
                                          contentPadding:
                                              const EdgeInsets.symmetric(
                                                horizontal: 12,
                                                vertical: 10,
                                              ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  actions: [
                                    TextButton(
                                      onPressed: () =>
                                          Navigator.pop(dialogContext),
                                      child: const Text(
                                        "Cancel",
                                        style: TextStyle(color: Colors.grey),
                                      ),
                                    ),
                                    ElevatedButton(
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: const Color(
                                          0xFF1F2A6E,
                                        ),
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(
                                            10,
                                          ),
                                        ),
                                      ),
                                      onPressed: () {
                                        final email = emailControllerDialog.text
                                            .trim();
                                        if (email.isEmpty) return;

                                        Navigator.pop(
                                          dialogContext,
                                        ); 
                                        Future.microtask(() async {
                                          setState(() => _loading = true);
                                          try {
                                            final resCheck =
                                                await ApiService.checkEmailVerification(
                                                  email,
                                                );

                                            if (resCheck.statusCode == 200) {
                                              final data = jsonDecode(
                                                resCheck.body,
                                              );
                                              final isVerified =
                                                  data['verified'] ?? false;

                                              if (isVerified) {
                                                _showErrorDialog(
                                                  outerContext,
                                                  "This email is already verified. Please login instead.",
                                                );
                                              } else {
                                                final resOtp =
                                                    await ApiService.sendOtp(
                                                      email,
                                                    );
                                                if (resOtp.statusCode == 200) {
                                                  Navigator.push(
                                                    outerContext,
                                                    MaterialPageRoute(
                                                      builder: (_) =>
                                                          VerifyOtpScreen(
                                                            email: email,
                                                          ),
                                                    ),
                                                  );
                                                } else {
                                                  _showErrorDialog(
                                                    outerContext,
                                                    "Failed to send verification email. Please try again.",
                                                  );
                                                }
                                              }
                                            } else if (resCheck.statusCode ==
                                                404) {
                                              final resOtp =
                                                  await ApiService.sendOtp(
                                                    email,
                                                  );
                                              if (resOtp.statusCode == 200) {
                                                Navigator.push(
                                                  outerContext,
                                                  MaterialPageRoute(
                                                    builder: (_) =>
                                                        VerifyOtpScreen(
                                                          email: email,
                                                        ),
                                                  ),
                                                );
                                              } else {
                                                _showErrorDialog(
                                                  outerContext,
                                                  "Failed to send verification email. Please try again.",
                                                );
                                              }
                                            } else if (resCheck.statusCode ==
                                                400) {
                                              _showErrorDialog(
                                                outerContext,
                                                "Email not registered. Please sign up first.",
                                              );
                                            } else {
                                              _showErrorDialog(
                                                outerContext,
                                                "Something went wrong. Please try again.",
                                              );
                                            }
                                          } catch (e) {
                                            _showErrorDialog(
                                              outerContext,
                                              "Error connecting to server. Please check your network.",
                                            );
                                          } finally {
                                            setState(() => _loading = false);
                                          }
                                        });
                                      },
                                      child: const Text(
                                        "Send Code",
                                        style: TextStyle(color: Colors.white),
                                      ),
                                    ),
                                  ],
                                );
                              },
                            );
                          },
                    child: Text(
                      "Verify your email",
                      style: TextStyle(
                        color: Colors.blue.shade800,
                        fontWeight: FontWeight.w600,
                        decoration: TextDecoration.underline,
                      ),
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

  Widget _socialButton(IconData icon) {
    return Container(
      width: 58,
      height: 50,
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Icon(icon, color: Colors.grey.shade700, size: 26),
    );
  }
}
