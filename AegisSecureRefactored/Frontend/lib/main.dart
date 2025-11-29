import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'config/app_constants.dart';
import 'screens/AccountPage.dart';
import 'screens/EmailAccountManager.dart';
import 'screens/login_screen.dart';
import 'screens/main_navigation.dart';
import 'screens/privacyPolicy.dart';
import 'screens/register_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/termsOfService.dart';
import 'screens/verify_otp_screen.dart';
import 'services/sms_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  await dotenv.load(fileName: "assets/env/env");
  
  final prefs = await SharedPreferences.getInstance();
  final token = prefs.getString('jwt_token');
  
  await SmsService.initAutoSyncFlag();
  
  runApp(MyApp(initialToken: token));
}

class MyApp extends StatelessWidget {
  final String? initialToken;
  
  const MyApp({Key? key, required this.initialToken}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConstants.appTitle,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.indigo,
        primaryColor: AppConstants.primaryColor,
        visualDensity: VisualDensity.adaptivePlatformDensity,
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: {
            TargetPlatform.android: CupertinoPageTransitionsBuilder(),
            TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          },
        ),
      ),
      initialRoute: initialToken == null 
          ? AppConstants.routeLogin 
          : AppConstants.routeHome,
      routes: {
        AppConstants.routeLogin: (context) => LoginScreen(),
        AppConstants.routeRegister: (context) => RegisterScreen(),
        AppConstants.routeHome: (context) => const MainNavigation(),
        AppConstants.routeOtp: (context) => VerifyOtpScreen(email: ''),
        AppConstants.routeAccount: (context) => AccountPage(),
        AppConstants.routeSettings: (context) => SettingsScreen(),
        AppConstants.routeTerms: (context) => const TermsOfServicePage(),
        AppConstants.routePrivacy: (context) => const PrivacyPolicyPage(),
        AppConstants.routeEmailAccountManager: (context) => const EmailAccountManager(),
      },
    );
  }
}
