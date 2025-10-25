// This is the main file the theflutter app.
// It will start the app, checks if the user is logged in and shows the right screen accordingly.

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'screens/gmail_screen.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';

void main() async {
  // this will make sure that the flutter is ready before doing anything async.
  WidgetsFlutterBinding.ensureInitialized();

  // this opens the local storage to check if a login token is saved.
  SharedPreferences prefs = await SharedPreferences.getInstance();
  
  // get the saved tokens if it exists, it would be null if not logged in.
  String? token = prefs.getString('jwt_token');

  // start the app and then send the token to MyApp.
  runApp(MyApp(initialToken: token));
}

// it decides which screen to show first.
class MyApp extends StatelessWidget {
  final String? initialToken; // store the login token.
  
  // we need the token when creating MyApp
  MyApp({required this.initialToken});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aegis Mail',
      debugShowCheckedModeBanner: false, // to hide the debug banner, it is set to false.
      theme: ThemeData(
        primarySwatch: Colors.indigo,
        visualDensity: VisualDensity.adaptivePlatformDensity,
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: {
            // this make the page transition smooth.
            TargetPlatform.android: CupertinoPageTransitionsBuilder(),
            TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          },
        ),
      ),

      // show the login screen if there's no token, else show the home screen.
      initialRoute: initialToken == null ? '/login' : '/home',
      routes: {
        '/login': (context) => LoginScreen(),
        '/register': (context) => RegisterScreen(),
        '/home': (context) => HomeScreen(),
        '/gmail': (context) => GmailScreen(),
      },
    );
  }
}
