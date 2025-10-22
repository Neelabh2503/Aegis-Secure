import 'package:flutter/material.dart';
import '../services/api_service.dart';



class RegisterScreen extends StatefulWidget {
  @override
  _RegisterScreenState createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final nameController = TextEditingController();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  final confirmPasswordController = TextEditingController();

  bool _loading = false;
  bool _agree = false;

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

    if (nameError != null ||
        emailError != null ||
        passwordError != null ||
        confirmError != null)
      return;

    setState(() => _loading = true);

    try {
      final res = await ApiService.registerUser(name, email, password);

      if (res.statusCode == 200) {
        //When registeration is completed, ask user to login or take to OTP verification(OTP not implemented right now)
        Navigator.pushReplacementNamed(
          context,
          '/login',
        );
      } else {
        setState(() {
          emailError = "Registration failed, please try again";
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

  //builfing the page
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white, 
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // Placeholder for Logo
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
                  decoration: InputDecoration(
                    labelText: "Full Name",
                    errorText: nameError,
                    labelStyle: TextStyle(color: Colors.grey.shade700),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),

                SizedBox(height: 16),//SizedBox are used for spacing between fields
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

                SizedBox(height: 16),
                TextField(
                  controller: confirmPasswordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: "Confirm Password",
                    errorText: confirmError,
                    labelStyle: TextStyle(color: Colors.grey.shade700),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),

                SizedBox(height: 16),

                //Checkbox for temrs and conditions, we will add the Terms Later on
                Row(
                  children: [
                    Checkbox(
                      value: _agree,
                      onChanged: (val) {
                        setState(() => _agree = val ?? false);
                      },
                    ),
                    Expanded(
                      child: Text(
                        "I agree to the Terms and Privacy Policy",
                        style: TextStyle(color: Colors.grey.shade700),
                      ),
                    ),
                  ],
                ),

                SizedBox(height: 20),

                //Button for ciompleting the registeration
                _loading
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

                SizedBox(height: 20),

                Text(
                  "or sign up with",
                  style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
                ),

                SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _socialButton(Icons.mail_outline),
                    SizedBox(width: 25),
                    _socialButton(Icons.phone_outlined),
                  ],
                ),

                SizedBox(height: 24),

                // Option to go to login Page
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
