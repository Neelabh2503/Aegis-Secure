import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shared_preferences/shared_preferences.dart';


import 'package:gmailclone/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Login Success Test', (WidgetTester tester) async {


    const String realEmail = "pvadsmiya@gmail.com";
    const String realPassword = "Vagabond@123";



    SharedPreferences.setMockInitialValues({});


    await tester.pumpWidget(app.MyApp(initialToken: null));
    await tester.pumpAndSettle();


    final emailField = find.byKey(const Key('login_email_field'));
    final passwordField = find.byKey(const Key('login_password_field'));
    final loginButton = find.byKey(const Key('login_button'));

    debugPrint("Typing Email...");
    await tester.ensureVisible(emailField);
    await tester.tap(emailField);
    await tester.enterText(emailField, realEmail);
    await tester.pumpAndSettle();

    debugPrint("Typing Password...");
    await tester.ensureVisible(passwordField);
    await tester.tap(passwordField);
    await tester.enterText(passwordField, realPassword);
    await tester.pumpAndSettle();


    FocusManager.instance.primaryFocus?.unfocus();
    await tester.pumpAndSettle();

    debugPrint("Tapping Login...");
    await tester.ensureVisible(loginButton);
    await tester.tap(loginButton);


    debugPrint("Waiting for Home Screen...");
    bool foundHome = false;


    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(seconds: 1));

      if (find.text('AegisSecure Home').evaluate().isNotEmpty ||
          find.text('Cyber Insights').evaluate().isNotEmpty ||
          find.byIcon(Icons.home_outlined).evaluate().isNotEmpty) {
        foundHome = true;
        break;
      }
    }


    if (foundHome) {
      debugPrint("Test Passed: Successfully landed on Home Screen.");

      expect(find.byType(Scaffold), findsOneWidget);
    } else {
      debugPrint("Test Failed: Timed out waiting for Home Screen.");
      fail("Login failed or timed out.");
    }
  });
}