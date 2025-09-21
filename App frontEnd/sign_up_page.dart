import 'package:flutter/material.dart';

import 'main_page.dart';

class SignUpPage extends StatelessWidget {
  const SignUpPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),

        actions: [
          Container(
            margin: const EdgeInsets.only(right: 12, bottom: 12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.blue),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              "A",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ),
        ],
        backgroundColor: Colors.white,
        elevation: 0,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Container(height: 10, width: 100),
                Container(height: 20, width: 100),
                Text(
                  "Create your account",
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w600,
                    fontFamily: "Roboto",
                  ),
                ),
                Container(height: 30, width: 100),

                // Input area for Name
                TextField(
                  decoration: InputDecoration(
                    labelText: "Name",
                    hintText: "ex: Abcd Xyz",
                    border: OutlineInputBorder(
                      borderSide: BorderSide(color: Color(0xFF212121)),
                    ),
                  ),
                ),
                Container(height: 20, width: 100),

                // Input are for Mobile or Email
                TextField(
                  decoration: InputDecoration(
                    labelText: "Email or Mobile Number",
                    hintText: "ex: abc@xyz.com",
                    border: OutlineInputBorder(
                      borderSide: BorderSide(color: Color(0xFF212121)),
                    ),
                  ),
                ),
                Container(height: 20, width: 100),
                //Input Area for Password
                TextField(
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: "Password",
                    border: OutlineInputBorder(
                      borderSide: BorderSide(color: Color(0xFF212121)),
                    ),
                  ),
                ),
                Container(height: 20, width: 100),

                // Area for confirming Password
                TextField(
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: "Confirm Password",
                    border: OutlineInputBorder(),
                  ),
                ),
                Container(height: 20, width: 100),
                // Terms & policy
                Row(
                  children: [
                    Checkbox(value: false, onChanged: (value) {}),
                    Expanded(
                      child: Text.rich(
                        TextSpan(
                          text: "I understood the ",
                          style: TextStyle(color: Color(0xFF212121)),
                          children: [
                            TextSpan(
                              text: "terms & policy",
                              style: TextStyle(
                                color: Color(0xFF1E3A8A),
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            TextSpan(
                              text: ".",
                              style: TextStyle(color: Color(0xFF212121)),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                Container(height: 10, width: 1000),
                // Sign Up Button
                Container(
                  width: MediaQuery.of(context).size.width * (1.0),
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Color(0xFF1E3A8A),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      padding: EdgeInsets.symmetric(vertical: 14),
                    ),
                    onPressed: () {
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(builder: (_) => MainPage()),
                      );
                    },
                    child: Text(
                      "SIGN IN",
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontFamily: "Roboto",
                      ),
                    ),
                  ),
                ),
                Container(height: 20, width: 100),
                Text(
                  "or sign up with",
                  style: TextStyle(
                    color: Color(0xFF212121),
                    fontFamily: "Roboto",
                    fontSize: 14,
                  ),
                ),
                Container(height: 15, width: 100),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    IconButton(
                      icon: Icon(Icons.email_outlined, size: 30),
                      onPressed: () {},
                    ),
                    Container(height: 20, width: 20),
                    IconButton(
                      icon: Icon(Icons.phone, size: 30),
                      onPressed: () {},
                    ),
                  ],
                ),

                Container(height: 40, width: 100),

                // go back to SignIn page
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text("Have an account? "),
                    GestureDetector(
                      onTap: () {
                        Navigator.pop(context);
                      },
                      child: Text(
                        "SIGN IN",
                        style: TextStyle(
                          color: Color(0xFF01B041),
                          fontWeight: FontWeight.bold,
                          fontFamily: "Roboto",
                        ),
                      ),
                    ),
                  ],
                ),
                Container(height: 30, width: 100),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
