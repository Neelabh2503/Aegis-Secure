import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:gmailclone/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Signup Flow Test', (WidgetTester tester) async {


    final String uniqueEmail = "pvadsmiya@gmail.com";
    const String testName = "Pransu Vadsmiya";
    const String testPassword = "Vagabond123";

    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(app.MyApp(initialToken: null));
    await tester.pumpAndSettle();


    FocusManager.instance.primaryFocus?.unfocus();
    await tester.pumpAndSettle();

    debugPrint("Tapping SIGN UP on Login Screen...");


    final loginSignUp = find.byKey(const Key('login_bottom_signup_link'));

    await tester.ensureVisible(loginSignUp);
    await tester.tap(loginSignUp);
    await tester.pumpAndSettle();

    debugPrint("Navigated to Register Screen.");


    expect(find.text("Create your account"), findsOneWidget);


    await tester.enterText(find.byKey(const Key('register_name_field')), testName);
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('register_email_field')), uniqueEmail);
    await tester.pumpAndSettle();

    final passField = find.byKey(const Key('register_password_field'));
    await tester.ensureVisible(passField);
    await tester.enterText(passField, testPassword);
    await tester.pumpAndSettle();

    final confirmField = find.byKey(const Key('register_confirm_password_field'));
    await tester.ensureVisible(confirmField);
    await tester.enterText(confirmField, testPassword);
    await tester.pumpAndSettle();


    final termsCheck = find.byKey(const Key('register_terms_checkbox'));
    await tester.ensureVisible(termsCheck);
    await tester.tap(termsCheck);
    await tester.pumpAndSettle();


    final signupBtn = find.byKey(const Key('sign_up'));
    await tester.ensureVisible(signupBtn);
    await tester.tap(signupBtn);

    debugPrint("Waiting for signup response...");


    bool success = false;
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(seconds: 1));

      if (find.text("Sign in your account").evaluate().isNotEmpty) {
        debugPrint(" SUCCESS: Returned to Login Screen.");
        success = true;
        break;
      }

      if (find.text("Verification code").evaluate().isNotEmpty) {
        debugPrint("SUCCESS: Navigated to OTP Screen.");
        success = true;
        break;
      }
    }

    if (!success) {
      fail("Signup failed or timed out.");
    }
  });
}
