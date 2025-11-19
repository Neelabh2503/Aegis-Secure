import 'dart:convert';

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../services/dashboard_api.dart';
import '../widgets/sidebar.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => HomeScreenState();
}

class UserAvatar extends StatelessWidget {
  final String? avatarBase64;
  final String? userName;
  final Color backgroundColor;
  final VoidCallback onTap;
  const UserAvatar({
    Key? key,
    required this.avatarBase64,
    required this.userName,
    required this.backgroundColor,
    required this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final String initial = (userName != null && userName!.isNotEmpty)
        ? userName![0].toUpperCase()
        : '?';
    return GestureDetector(
      onTap: onTap,
      child: CircleAvatar(
        radius: 20,
        backgroundColor: backgroundColor,
        backgroundImage: avatarBase64 != null && avatarBase64!.isNotEmpty
            ? MemoryImage(base64Decode(avatarBase64!))
            : null,
        child: avatarBase64 == null || avatarBase64!.isEmpty
            ? Text(
                initial,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              )
            : null,
      ),
    );
  }
}

class DashboardAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String? avatarBase64;
  final String? userName;
  final bool userLoading;
  final VoidCallback onMenuTap;
  final VoidCallback onAvatarTap;

  const DashboardAppBar({
    Key? key,
    required this.avatarBase64,
    required this.userName,
    required this.userLoading,
    required this.onMenuTap,
    required this.onAvatarTap,
  }) : super(key: key);

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      backgroundColor: Colors.white,
      elevation: 1,
      leading: IconButton(
        icon: const Icon(Icons.menu, color: Colors.black87),
        onPressed: onMenuTap,
      ),
      title: const Text(
        "AegisSecure Home",
        style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
      ),
      actions: [
        Padding(
          padding: const EdgeInsets.only(right: 14.0),
          child: userLoading
              ? const CircleAvatar(
                  backgroundColor: Colors.grey,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : UserAvatar(
                  avatarBase64: avatarBase64,
                  userName: userName,
                  backgroundColor: const Color(0xFF1F2A6E),
                  onTap: onAvatarTap,
                ),
        ),
      ],
    );
  }
}

class HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  String? currentUserName;
  String? currentUserAvatar;
  bool userLoading = true;

  String _dashboardMode = 'both';
  bool dashboardLoading = false;

  List<String> _dashLabels = [];
  List<int> _dashValues = [];
  int _dashTotal = 0;
  String dashInsights = "";

  static const Color primaryColor = Color(0xFF1F2A6E);

  static const Color mailColor = Color(0xFF4A90E2);
  static const Color smsColor = Color(0xFF556B9D);
  static const Color bothColor = Color(0xFF7B8DB5);

  late final AnimationController _animController;
  final GlobalKey<DashboardPieChartState> pieChartKey =
      GlobalKey<DashboardPieChartState>();

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );

    Future.wait([loadCurrentUser(), _loadDashboard(mode: _dashboardMode)]);
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  Future<void> loadCurrentUser() async {
    try {
      final user = await ApiService.fetchCurrentUser();
      if (mounted) {
        setState(() {
          currentUserName = user['name'] ?? 'U';
          currentUserAvatar = user['avatar_base64'];
          userLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => userLoading = false);
    }
  }

  Future<void> _loadDashboard({required String mode}) async {
    setState(() => dashboardLoading = true);
    try {
      final res = await DashboardApi.fetchDashboard(mode: mode);
      if (res != null && mounted) {
        final labels = List<String>.from(res['labels'] ?? []);
        final values =
            (res['values'] as List<dynamic>?)
                ?.map((e) => (e as num).toInt())
                .toList() ??
            List<int>.filled(labels.isNotEmpty ? labels.length : 4, 0);
        final total =
            (res['total'] ?? values.fold<int>(0, (a, b) => a + b)) as int;

        final insightsData = res['insights'];
        String fact1 = "";
        String fact2 = "";
        if (insightsData is Map<String, dynamic>) {
          fact1 = insightsData['fact1'] ?? "";
          fact2 = insightsData['fact2'] ?? "";
        }
        print(fact1);
        print(fact2);
        setState(() {
          _dashboardMode = mode;
          _dashLabels = labels.isNotEmpty
              ? labels
              : ["Secure", "Suspicious", "Threat", "Critical"];
          _dashValues = values.isNotEmpty ? values : [0, 0, 0, 0];
          _dashTotal = total;
          dashInsights = jsonEncode({"fact1": fact1, "fact2": fact2});
        });

        pieChartKey.currentState?.updateData(
          _dashValues,
          _dashLabels,
          _dashTotal,
        );
        _animController.forward(from: 0);
      }
    } catch (e) {
      debugPrint("Failed to load dashboard: $e");
    } finally {
      if (mounted) setState(() => dashboardLoading = false);
    }
  }

  Future<void> _handleLogout() async {
    _scaffoldKey.currentState?.closeDrawer();
    await Future.delayed(const Duration(milliseconds: 150));

    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          elevation: 15,
          title: Row(
            children: [
              Icon(Icons.logout, color: primaryColor),
              const SizedBox(width: 12),
              const Text(
                "Confirm Sign Out",
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
              ),
            ],
          ),
          content: const Text(
            "Are you sure you want to sign out from your account?",
            style: TextStyle(fontSize: 16, color: Colors.black87),
          ),
          actionsPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 10,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              style: TextButton.styleFrom(
                foregroundColor: Colors.grey.shade700,
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 10,
                ),
              ),
              child: const Text("Cancel"),
            ),
            ElevatedButton.icon(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(
                backgroundColor: primaryColor,
                foregroundColor: Colors.white,
                elevation: 0,
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              icon: const Icon(Icons.exit_to_app, size: 20),
              label: const Text(
                "Sign Out",
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
            ),
          ],
        );
      },
    );

    if (confirmed == true) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('jwt_token');
      Navigator.of(
        context,
        rootNavigator: true,
      ).pushNamedAndRemoveUntil('/login', (route) => false);
    }
  }

  Widget buildModeButton(String label, String mode, Color color) {
    final bool selected = _dashboardMode == mode;
    return ChoiceChip(
      label: Text(
        label,
        style: TextStyle(
          color: selected ? Colors.white : color,
          fontWeight: FontWeight.w600,
          fontSize: 13,
        ),
      ),
      selected: selected,
      selectedColor: color,
      backgroundColor: color.withOpacity(0.25),
      elevation: 2,
      shadowColor: Colors.black12,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      onSelected: (v) {
        if (v && _dashboardMode != mode) _loadDashboard(mode: mode);
      },
    );
  }

  Widget _buildCyberFacts(Map<String, dynamic> facts) {
    final List<String> points = [
      facts['fact1']?.toString() ?? '',
      facts['fact2']?.toString() ?? '',
    ].where((f) => f.isNotEmpty).toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: points.map((point) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "• ",
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  height: 1.6,
                  color: Colors.black87,
                  fontFamily: 'Inter',
                ),
              ),
              Expanded(
                child: Text(
                  point,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    height: 1.6,
                    color: Colors.black87,
                    fontFamily: 'Inter',
                  ),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: Colors.grey.shade50,
      drawer: Sidebar(
        onClose: () => _scaffoldKey.currentState?.closeDrawer(),
        onLogoutTap: _handleLogout,
      ),
      appBar: DashboardAppBar(
        avatarBase64: currentUserAvatar,
        userName: currentUserName,
        userLoading: userLoading,
        onMenuTap: () => _scaffoldKey.currentState?.openDrawer(),
        onAvatarTap: () {
          Navigator.of(
            context,
          ).pushNamed('/account', arguments: currentUserName);
        },
      ),
      body: dashboardLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () async {
                await _loadDashboard(mode: _dashboardMode);
              },
              child: ListView(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 30,
                ).copyWith(bottom: 120),
                children: [
                  DashboardPieChart(
                    key: pieChartKey,
                    values: _dashValues,
                    labels: _dashLabels,
                    total: _dashTotal,
                  ),
                  const SizedBox(height: 24),

                  // Mode buttons
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      buildModeButton("Mail", "mail", mailColor),
                      const SizedBox(width: 12),
                      buildModeButton("SMS", "sms", smsColor),
                      const SizedBox(width: 12),
                      buildModeButton("Both", "both", bothColor),
                    ],
                  ),

                  const SizedBox(height: 24),

                  // Legend items
                  Wrap(
                    spacing: 18,
                    runSpacing: 12,
                    children: List.generate(_dashLabels.length, (i) {
                      return SizedBox(
                        width: (MediaQuery.of(context).size.width / 2) - 36,
                        child: Row(
                          children: [
                            Container(
                              width: 14,
                              height: 14,
                              decoration: BoxDecoration(
                                color:
                                    DashboardPieChart.brightChartColors[i %
                                        DashboardPieChart
                                            .brightChartColors
                                            .length],
                                borderRadius: BorderRadius.circular(6),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                _dashLabels[i],
                                style: const TextStyle(fontSize: 15),
                              ),
                            ),
                            Text(
                              "${_dashValues[i]}",
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                  ),

                  const SizedBox(height: 32),

                  Text(
                    "💡Cyber Insights",
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: primaryColor,
                    ),
                  ),
                  const SizedBox(height: 12),

                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 20,
                      vertical: 22,
                    ),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFFABE3FF), Color(0xFFFFFFFF)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: primaryColor.withOpacity(0.15),
                          blurRadius: 10,
                          offset: const Offset(0, 7),
                        ),
                      ],
                      border: Border.all(
                        color: primaryColor.withOpacity(0.3),
                        width: 0.7,
                      ),
                    ),
                    child: dashInsights.isNotEmpty
                        ? _buildCyberFacts(jsonDecode(dashInsights))
                        : const Text(
                            "No insights available yet.",
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              height: 1.6,
                              color: Colors.black87,
                              fontFamily: 'Inter',
                            ),
                          ),
                  ),
                ],
              ),
            ),
    );
  }
}

class DashboardPieChart extends StatefulWidget {
  final List<int> values;
  final List<String> labels;
  final int total;

  const DashboardPieChart({
    super.key,
    required this.values,
    required this.labels,
    required this.total,
  });

  static const List<Color> brightChartColors = [
    Color(0xFF2B3E7F),
    Color(0xFF556B9D),
    Color(0xFF7B8DB5),
    Color(0xFFA5B3D4),
  ];

  static const Color primaryColor = Color(0xFF1F2A6E);

  @override
  State<DashboardPieChart> createState() => DashboardPieChartState();
}

class DashboardPieChartState extends State<DashboardPieChart> {
  int? hoverIndex;
  late List<int> values;
  late List<String> labels;
  late int total;

  @override
  void initState() {
    super.initState();
    values = widget.values;
    labels = widget.labels;
    total = widget.total;
  }
  void updateData(List<int> newValues, List<String> newLabels, int newTotal) {
    setState(() {
      values = newValues;
      labels = newLabels;
      total = newTotal;
      hoverIndex = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            height: 280,
            width: 280,
            child: PieChart(
              PieChartData(
                sectionsSpace: 2,
                centerSpaceRadius: 90,
                pieTouchData: PieTouchData(
                  touchCallback: (event, response) {
                    if (!event.isInterestedForInteractions) return;
                    setState(() {
                      if (response?.touchedSection?.touchedSectionIndex !=
                          null) {
                        hoverIndex =
                            response!.touchedSection!.touchedSectionIndex;
                      } else {
                        hoverIndex = null;
                      }
                    });
                  },
                ),
                sections: List.generate(values.length, (i) {
                  final isTouched = hoverIndex == i;
                  return PieChartSectionData(
                    color:
                        DashboardPieChart.brightChartColors[i %
                            DashboardPieChart.brightChartColors.length],
                    value: values[i].toDouble(),
                    title: "",
                    radius: isTouched ? 70 : 60,
                  );
                }),
              ),
            ),
          ),
          GestureDetector(
            onTap: () => setState(() => hoverIndex = null),
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 250),
              child:
                  (hoverIndex != null &&
                      hoverIndex! >= 0 &&
                      hoverIndex! < values.length)
                  ? Column(
                      key: ValueKey(hoverIndex),
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          "${values[hoverIndex!]}",
                          style: TextStyle(
                            fontSize: 34,
                            fontWeight: FontWeight.bold,
                            color: DashboardPieChart
                                .brightChartColors[hoverIndex!],
                          ),
                        ),
                        Text(
                          labels[hoverIndex!],
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.black87,
                          ),
                        ),
                      ],
                    )
                  : Column(
                      key: const ValueKey("total"),
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '$total',
                          style: const TextStyle(
                            fontSize: 38,
                            fontWeight: FontWeight.bold,
                            color: DashboardPieChart.primaryColor,
                          ),
                        ),
                        const Text(
                          "Messages Analyzed",
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                            color: Colors.black54,
                          ),
                        ),
                      ],
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
