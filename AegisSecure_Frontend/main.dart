import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'screens/AccountPage.dart';
import 'screens/EmailAccountManager.dart';
import 'screens/login_screen.dart';
import 'screens/main_navigation.dart';
import 'screens/privacyPolicy.dart';
import 'screens/register_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/termsOfService.dart';
import 'screens/verify_otp_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SharedPreferences prefs = await SharedPreferences.getInstance();
  String? token = prefs.getString('jwt_token');
  runApp(MyApp(initialToken: token));
}

class MyApp extends StatelessWidget {
  final String? initialToken;
  MyApp({required this.initialToken});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aegis Mail',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.indigo,
        visualDensity: VisualDensity.adaptivePlatformDensity,
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: {
            TargetPlatform.android: CupertinoPageTransitionsBuilder(),
            TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          },
        ),
      ),
      initialRoute: initialToken == null ? '/login' : '/home',
      routes: {
        '/emailAccountManager': (context) => const EmailAccountManager(),
        '/login': (c) => LoginScreen(),
        '/register': (context) => RegisterScreen(),
        '/account': (context) => AccountPage(),
        '/home': (context) => const MainNavigation(),
        '/otp': (context) => VerifyOtpScreen(email: ''),
        '/settings': (context) => SettingsScreen(),
        '/terms': (context) => const TermsOfServicePage(),
        '/privacy': (context) => const PrivacyPolicyPage(),
      },
    );
  }
}
