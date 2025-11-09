import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../services/dashboard_api.dart';
import '../widgets/sidebar.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  String? currentUserName;
  bool _userLoading = true;

  String _dashboardMode = 'both';
  bool _dashboardLoading = false;
  List<String> _dashLabels = [];
  List<int> _dashValues = [];
  int _dashTotal = 0;
  String _dashSummary = "";
  List<String> _dashTrends = [];

  int? _hoverIndex;

  static const List<Color> _colors = [
    Color(0xFF27AE60),
    Color(0xFFF39C12),
    Color(0xFFE67E22),
    Color(0xFFE74C3C),
  ];

  late final AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..addListener(() => setState(() {}));

    loadCurrentUser();
    WidgetsBinding.instance.addPostFrameCallback(
      (_) => _loadDashboard(mode: _dashboardMode),
    );
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  Future<void> loadCurrentUser() async {
    try {
      final user = await ApiService.fetchCurrentUser();
      setState(() {
        currentUserName = user['name'] ?? 'U';
        _userLoading = false;
      });
    } catch (e) {
      setState(() => _userLoading = false);
    }
  }

  Future<void> _logout(BuildContext context) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('jwt_token');
    Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
  }

  Future<void> _loadDashboard({String mode = 'both'}) async {
    setState(() {
      _dashboardLoading = true;
      _dashboardMode = mode;
    });

    try {
      final res = await DashboardApi.fetchDashboard(mode: mode);
      if (res != null) {
        final labels = List<String>.from(res['labels'] ?? []);
        final values =
            (res['values'] as List<dynamic>?)
                ?.map((e) => (e as num).toInt())
                .toList() ??
            List<int>.filled(labels.isNotEmpty ? labels.length : 4, 0);
        final total =
            (res['total'] ?? values.fold<int>(0, (a, b) => a + b)) as int;
        final summary = (res['summary'] ?? '') as String;
        final trends = List<String>.from(res['trends'] ?? []);

        setState(() {
          _dashLabels = labels.isNotEmpty
              ? labels
              : ["Secure", "Suspicious", "Threat", "Critical"];
          _dashValues = values.isNotEmpty ? values : [0, 0, 0, 0];
          _dashTotal = total;
          _dashSummary = summary;
          _dashTrends = trends;
        });

        await Future.delayed(const Duration(milliseconds: 50));
        if (mounted) _animController.forward(from: 0);
      }
    } catch (e) {
      debugPrint("Failed to load dashboard: $e");
    } finally {
      setState(() => _dashboardLoading = false);
    }
  }

  // --- Drawer Key
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  Widget build(BuildContext context) {
    final firstLetter = (currentUserName != null && currentUserName!.isNotEmpty)
        ? currentUserName![0].toUpperCase()
        : '?';

    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: Colors.grey.shade100,

      // ✅ Replace dialog with Drawer-style Sidebar
      drawer: Sidebar(
        onClose: () => Navigator.of(context).pop(),
        onLogoutTap: () => _logout(context),
      ),

      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.menu, color: Colors.black87),
          onPressed: () {
            _scaffoldKey.currentState?.openDrawer();
          },
        ),
        title: const Text(
          "Dashboard",
          style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12.0),
            child: _userLoading
                ? const CircleAvatar(
                    backgroundColor: Colors.grey,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : CircleAvatar(
                    backgroundColor: Colors.deepPurple,
                    child: Text(
                      firstLetter,
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
          ),
        ],
      ),

      // === BODY ===
      body: _dashboardLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.symmetric(
                horizontal: 20,
                vertical: 24,
              ).copyWith(bottom: 120),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // --- Mode Selector ---
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      _buildModeButton("Mail", "mail", Colors.deepPurple),
                      const SizedBox(width: 8),
                      _buildModeButton("SMS", "sms", Colors.orange),
                      const SizedBox(width: 8),
                      _buildModeButton("Both", "both", Colors.green),
                    ],
                  ),
                  const SizedBox(height: 28),

                  // --- Chart Section ---
                  Center(
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        SizedBox(
                          height: 260,
                          child: PieChart(
                            PieChartData(
                              sectionsSpace: 1,
                              centerSpaceRadius: 95,
                              pieTouchData: PieTouchData(
                                touchCallback: (event, response) {
                                  if (!event.isInterestedForInteractions)
                                    return;
                                  if (response != null &&
                                      response.touchedSection != null &&
                                      response
                                              .touchedSection!
                                              .touchedSectionIndex >=
                                          0) {
                                    setState(() {
                                      _hoverIndex = response
                                          .touchedSection!
                                          .touchedSectionIndex;
                                    });
                                  } else {
                                    setState(() => _hoverIndex = null);
                                  }
                                },
                              ),
                              sections: List.generate(_dashValues.length, (i) {
                                final isTouched = _hoverIndex == i;
                                final double percentage = _dashTotal == 0
                                    ? 0
                                    : (_dashValues[i] / _dashTotal) * 100;
                                return PieChartSectionData(
                                  color: _colors[i % _colors.length],
                                  value: _dashValues[i].toDouble(),
                                  title: "",
                                  radius: isTouched ? 70 : 60,
                                  badgeWidget: isTouched
                                      ? AnimatedContainer(
                                          duration: const Duration(
                                            milliseconds: 200,
                                          ),
                                          padding: const EdgeInsets.all(6),
                                          decoration: BoxDecoration(
                                            color: Colors.white,
                                            borderRadius: BorderRadius.circular(
                                              8,
                                            ),
                                            boxShadow: const [
                                              BoxShadow(
                                                color: Colors.black12,
                                                blurRadius: 4,
                                              ),
                                            ],
                                          ),
                                          child: Text(
                                            "${percentage.toStringAsFixed(1)}%",
                                            style: const TextStyle(
                                              fontWeight: FontWeight.bold,
                                              fontSize: 12,
                                            ),
                                          ),
                                        )
                                      : null,
                                  badgePositionPercentageOffset: 1.3,
                                );
                              }),
                            ),
                          ),
                        ),
                        GestureDetector(
                          onTap: () => setState(() => _hoverIndex = null),
                          child: AnimatedSwitcher(
                            duration: const Duration(milliseconds: 250),
                            child: _hoverIndex == null
                                ? Column(
                                    key: const ValueKey("total"),
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text(
                                        '$_dashTotal',
                                        style: const TextStyle(
                                          fontSize: 34,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.deepPurple,
                                        ),
                                      ),
                                      const Text(
                                        "Messages Analyzed",
                                        style: TextStyle(
                                          fontSize: 13,
                                          color: Colors.black54,
                                        ),
                                      ),
                                    ],
                                  )
                                : Column(
                                    key: ValueKey(_hoverIndex),
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text(
                                        "${_dashValues[_hoverIndex!]}",
                                        style: TextStyle(
                                          fontSize: 30,
                                          fontWeight: FontWeight.bold,
                                          color: _colors[_hoverIndex!],
                                        ),
                                      ),
                                      Text(
                                        _dashLabels[_hoverIndex!],
                                        style: const TextStyle(
                                          fontSize: 14,
                                          fontWeight: FontWeight.w600,
                                          color: Colors.black87,
                                        ),
                                      ),
                                    ],
                                  ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 28),

                  // --- Legend ---
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 12,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(14),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black12,
                          blurRadius: 10,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    child: Column(
                      children: List.generate(_dashLabels.length, (i) {
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            children: [
                              Container(
                                width: 12,
                                height: 12,
                                decoration: BoxDecoration(
                                  color: _colors[i % _colors.length],
                                  borderRadius: BorderRadius.circular(4),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  _dashLabels[i],
                                  style: const TextStyle(fontSize: 14.5),
                                ),
                              ),
                              Text(
                                "${_dashValues[i]}",
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                    ),
                  ),

                  const SizedBox(height: 28),

                  const Text(
                    "Security Summary",
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Colors.deepPurple.withOpacity(0.06),
                      border: Border.all(
                        color: Colors.deepPurpleAccent.withOpacity(0.4),
                        width: 0.7,
                      ),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Text(
                      _dashSummary.isNotEmpty
                          ? _dashSummary
                          : "No summary available yet.",
                      style: const TextStyle(
                        fontSize: 14.5,
                        height: 1.5,
                        color: Colors.black87,
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildModeButton(String label, String mode, Color color) {
    final bool selected = _dashboardMode == mode;
    return ChoiceChip(
      label: Text(
        label,
        style: TextStyle(
          color: selected ? Colors.white : Colors.black87,
          fontWeight: FontWeight.w600,
        ),
      ),
      selected: selected,
      selectedColor: color,
      backgroundColor: Colors.grey.shade200,
      onSelected: (v) {
        if (v && _dashboardMode != mode) _loadDashboard(mode: mode);
      },
    );
  }
}