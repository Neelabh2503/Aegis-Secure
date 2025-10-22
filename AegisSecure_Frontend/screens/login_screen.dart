import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
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

  void login() async {
    final email = emailController.text.trim();
    final password = passwordController.text.trim();

    setState(() {
      emailError = email.isEmpty ? "Please enter your email" : null;
      passwordError = password.isEmpty ? "Please enter your password" : null;
    });

    if (emailError != null || passwordError != null) return;

    setState(() => _loading = true);

    try {
      final res = await ApiService.loginUser(email, password);
      if (res.statusCode == 200) {
        final token = jsonDecode(res.body)['token'];
        SharedPreferences prefs = await SharedPreferences.getInstance();
        await prefs.setString('jwt_token', token);

        Navigator.pushReplacementNamed(context, '/home');
      } else {
        setState(() {
          passwordError = "Invalid email or password";
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Error connecting to server")));
    } finally {
      setState(() => _loading = false);
    }
  }

//building the page
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
                // Placehilder for Logo currently
                Container(
                  width: 70,
                  height: 70,
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.blue.shade900, width: 2),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Center(
                    child: Text(
                      "A",
                      style: TextStyle(
                        color: Colors.blue.shade900,
                        fontSize: 36,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),

                SizedBox(height: 24),
                RichText(
                  textAlign: TextAlign.center,
                  text: TextSpan(
                    text: "Aegis ",
                    style: TextStyle(
                      color: Colors.blue.shade900,
                      fontSize: 32,
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
                  "Sign in your account",
                  style: TextStyle(
                    fontSize: 18,
                    color: Colors.black87,
                    fontWeight: FontWeight.w600,
                  ),
                ),

                SizedBox(height: 32),

                // Input for Email 
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

                // Input for Password with check for 8 character long currrntly, check is applied in backend
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

                // Button for Signing in
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
                
                //log in with Saved Ids
                Text(
                  "or sign in with",
                  style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
                ),

                SizedBox(height: 12),

                // Mail and PhoneNumber Social Icons
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _socialButton(Icons.mail_outline),
                    SizedBox(width: 25),
                    _socialButton(Icons.phone_outlined),
                  ],
                ),

                SizedBox(height: 24),

                // Option to SignUp takes to Register_screen.dart where SignUp process can be done
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