import 'package:flutter/material.dart';

import 'main_page.dart';
import 'sign_up_page.dart';

class SignInPage extends StatelessWidget {
  const SignInPage({super.key});

  @override
  Widget build(BuildContext context) {
    //Scafflod is the base structure of any dart page.
    return Scaffold(
      //SafeArea is the area which is safe that is if the size of devie changes than also the page will maitain its strucutre withotu collapsing or something else
      body: SafeArea(
        child: SingleChildScrollView(
          //singleChildScrollview allows the scrolling feature if the app overflows,
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const SizedBox(height: 60),
                // Logo
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.blue),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    "AS",
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                  ),
                ),
                Container(height: 10, width: 100),
                //here we have used Text.eich so that we can apply diff. style to diff. text parts without keep defining new text spans
                Text.rich(
                  TextSpan(
                    children: [
                      TextSpan(
                        text: "Aegis ",
                        style: TextStyle(
                          fontSize: 42,
                          fontFamily: "Jersey20",
                          color: Color(0xFF1E3A8A),
                        ),
                      ),
                      TextSpan(
                        text: "Secure",
                        style: TextStyle(
                          fontSize: 42,
                          fontFamily: "Jersey20",
                          color: Color(0xFF737373),
                        ),
                      ),
                    ],
                  ),
                ),
                Container(height: 25, width: 100),
                Text(
                  "Sign in your account",
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                ),
                Container(height: 35, width: 100),

                // Input area for email or Mobile no.
                TextField(
                  decoration: InputDecoration(
                    labelText: "Email or Mobile Number",
                    hintText: "abc@xyz.com",
                    border: OutlineInputBorder(
                      borderSide: BorderSide(color: Color(0xFF212121)),
                    ),
                  ),
                ),

                Container(height: 30, width: 100),
                // input area for password
                TextField(
                  obscureText:
                      true, //make the text no directly visible like password field
                  decoration: InputDecoration(
                    labelText: "Password",
                    border: OutlineInputBorder(
                      borderSide: BorderSide(color: Color(0xFF212121)),
                    ),
                  ),
                ),
                Container(height: 30, width: 100),

                // SignIn button
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
                      style: TextStyle(color: Colors.white, fontSize: 18),
                    ),
                  ),
                ),
                Container(height: 20, width: 100),
                Text(
                  "or sign in with",
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
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      "Don’t have an account? ",
                      style: TextStyle(
                        fontFamily: "Roboto",
                        color: Color((0xFF212121)),
                      ),
                    ),
                    GestureDetector(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => SignUpPage()),
                        );
                      },
                      child: Text(
                        "SIGN UP",
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
