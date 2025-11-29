import 'package:flutter/material.dart';

class Sidebar extends StatelessWidget {
  final VoidCallback onClose;

  final VoidCallback? onHomeTap;
  final VoidCallback? onAccountTap;
  final VoidCallback? onLogoutTap;
  final VoidCallback? onSettingsTap;
  final VoidCallback? onHelpTap;

  const Sidebar({
    Key? key,
    required this.onClose,
    this.onHomeTap,
    this.onAccountTap,
    this.onLogoutTap,
    this.onSettingsTap,
    this.onHelpTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final accentColor = const Color(0xFF1F2A6E);

    return Material(
      color: Colors.white,
      borderRadius: const BorderRadius.only(
        topRight: Radius.circular(20),
        bottomRight: Radius.circular(20),
      ),
      elevation: 10,
      child: SafeArea(
        child: Container(
          width: MediaQuery.of(context).size.width * 0.75,
          decoration: const BoxDecoration(
            borderRadius: BorderRadius.only(
              topRight: Radius.circular(20),
              bottomRight: Radius.circular(20),
            ),
            color: Colors.white,
          ),
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 20, 8, 12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    RichText(
                      text: TextSpan(
                        children: [
                          TextSpan(
                            text: 'Aegis ',
                            style: TextStyle(
                              fontFamily: 'Jersey20',
                              color: accentColor,
                              fontSize: 26,
                              letterSpacing: 1,
                            ),
                          ),
                          const TextSpan(
                            text: 'Secure',
                            style: TextStyle(
                              fontFamily: 'Jersey20',
                              color: Colors.black87,
                              fontSize: 26,
                              letterSpacing: 1,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: Icon(
                        Icons.arrow_back_ios_new,
                        size: 20,
                        color: Colors.grey.shade800,
                      ),
                      onPressed: onClose,
                    ),
                  ],
                ),
              ),

              const Divider(height: 1, thickness: 0.5),
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    children: [
                      const SizedBox(height: 8),

                      _buildMenuItem(
                        Icons.home_outlined,
                        'Home',
                        onHomeTap ??
                            () {
                              Navigator.pop(context);
                              Navigator.pushNamed(context, '/home');
                            },
                      ),
                      _buildMenuItem(
                        Icons.person_outline,
                        'Account',
                        onAccountTap ??
                            () {
                              Navigator.pop(context);
                              Navigator.pushNamed(context, '/account');
                            },
                      ),
                      _buildLogoutItem(context),
                    ],
                  ),
                ),
              ),

              const Divider(height: 1, thickness: 0.5),
              Padding(
                padding: const EdgeInsets.only(bottom: 16, top: 8),
                child: Column(
                  children: [
                    _buildMenuItem(Icons.settings_outlined, 'Settings', () {
                      Navigator.pop(context);
                      Navigator.pushNamed(context, '/settings');
                    }),
                    _buildMenuItem(
                      Icons.info_outline,
                      'Help & Feedback',
                      onHelpTap,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLogoutItem(BuildContext context) {
    return InkWell(
      onTap: () {
        Navigator.pop(context); // close sidebar
        if (onLogoutTap != null) {
          onLogoutTap!(); // directly call your logout callback
        }
      },
      borderRadius: BorderRadius.circular(8),
      splashColor: const Color(0xFF1F2A6E).withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12),
        child: Row(
          children: const [
            Icon(Icons.logout, color: Colors.black87, size: 22),
            SizedBox(width: 18),
            Text(
              "Sign Out",
              style: TextStyle(
                fontSize: 16,
                color: Colors.black87,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuItem(IconData icon, String title, VoidCallback? onTap) {
    return InkWell(
      onTap: onTap ?? () {},
      borderRadius: BorderRadius.circular(8),
      splashColor: const Color(0xFF1F2A6E).withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12),
        child: Row(
          children: [
            Icon(icon, color: Colors.black87, size: 22),
            const SizedBox(width: 18),
            Text(
              title,
              style: const TextStyle(
                fontSize: 16,
                color: Colors.black87,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
