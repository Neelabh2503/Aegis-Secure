import 'package:flutter/material.dart';

class AppConstants {
  AppConstants._();

  static const String appName = 'AegisSecure';
  static const String appTitle = 'Aegis Secure';
  
  static const String routeLogin = '/login';
  static const String routeLogin = '/login';
  static const String routeRegister = '/register';
  static const String routeHome = '/home';
  static const String routeOtp = '/otp';
  static const String routeAccount = '/account';
  static const String routeSettings = '/settings';
  static const String routeTerms = '/terms';
  static const String routePrivacy = '/privacy';
  static const String routeEmailAccountManager = '/emailAccountManager';
  
  // Colors
  static const Color primaryColor = Color(0xFF1F2A6E);
  static const Color accentColor = Color(0xFF1F2A6E);
  static const Color defaultAvatarColor = Color(0xFF90A4AE);
  
  // Validation
  static const int minPasswordLength = 6;
  static const int maxPasswordLength = 128;
  
  // UI Constants
  static const double defaultBorderRadius = 12.0;
  static const double defaultPadding = 16.0;
  static const double defaultElevation = 2.0;
  
  // Date Format Patterns
  static const List<String> monthNames = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
  ];
  
  // Error Messages
  static const String errorNetwork = "Network error occurred";
  static const String errorAuth = "Authentication failed";
  static const String errorUnknown = "An unknown error occurred";
  static const String errorEmailRequired = "Please enter your email";
  static const String errorPasswordRequired = "Please enter your password";
  static const String errorInvalidCredentials = "Invalid email or password";
  static const String errorEmailNotVerified = "Please verify your email before logging in.";
  static const String errorTokenMissing = "Failed to get authentication token.";
  
  static const String successLogin = "Login successful";
  static const String successLogin = "Login successful";
  static const String successRegister = "Registration successful";
  static const String successLogout = "Logged out successfully";
  
  // Asset Paths
  static const String logoAssetPath = 'assets/images/logo.png';
  static const String googleLogoAssetPath = 'assets/images/google_logo.png';
  
  // Font Families
  static const String fontFamilyJersey = 'Jersey20';
}
