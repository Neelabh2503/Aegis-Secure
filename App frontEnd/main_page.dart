import 'package:flutter/material.dart';

import 'sign_in_page.dart';

class MainPage extends StatelessWidget {
  const MainPage({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Main Page", style: TextStyle(color: Colors.white)),
        backgroundColor: Color(0xFF1E3A8A),
        actions: [
          IconButton(
            icon: Icon(Icons.logout, color: Colors.white),
            onPressed: () {
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (_) => SignInPage()),
                (route) => false,
              );
            },
          ),
        ],
      ),
      body: Center(
        child: Text(
          "This is the Main Page of the Application",
          style: TextStyle(fontSize: 20, color: Color(0xFF212121)),
        ),
      ),
    );
  }
}
