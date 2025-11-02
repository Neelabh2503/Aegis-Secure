import 'package:flutter/material.dart';
import 'package:gmailclone/screens/gmail_screen.dart';
import 'package:gmailclone/screens/home_screen.dart';
import 'package:gmailclone/screens/sms_screen.dart';

class MainNavigation extends StatefulWidget {
  const MainNavigation({Key? key}) : super(key: key);

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int _currentIndex = 1; //for home screen we chose 1

  final List<Widget> _pages = const [SmsScreen(), HomeScreen(), GmailScreen()];

  void _onTabTapped(int index) {
    setState(() => _currentIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    const activeColor = Colors.blueAccent;
    final inactiveColor = Colors.grey.shade600;

    return Scaffold(
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 300),
        transitionBuilder: (child, animation) =>
            FadeTransition(opacity: animation, child: child),
        child: _pages[_currentIndex],
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.grey.shade300,
              blurRadius: 6,
              offset: const Offset(0, -2),
            ),
          ],
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(10),
            topRight: Radius.circular(10),
          ),
        ),
        child: SafeArea(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              GestureDetector(
                onTap: () => _onTabTapped(0),
                child: Icon(
                  Icons.chat_bubble_outline,
                  size: 28,
                  color: _currentIndex == 0 ? activeColor : inactiveColor,
                ),
              ),
              GestureDetector(
                onTap: () => _onTabTapped(1),
                child: Icon(
                  Icons.home_outlined,
                  size: 28,
                  color: _currentIndex == 1 ? activeColor : inactiveColor,
                ),
              ),
              GestureDetector(
                onTap: () => _onTabTapped(2),
                child: Icon(
                  Icons.mail_outline,
                  size: 28,
                  color: _currentIndex == 2 ? activeColor : inactiveColor,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
