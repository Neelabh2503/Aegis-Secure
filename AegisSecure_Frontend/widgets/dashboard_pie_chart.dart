import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class DashboardPieChart extends StatelessWidget {
  final List<String> labels;
  final List<int> values;
  final double size; // width/height

  const DashboardPieChart({
    Key? key,
    required this.labels,
    required this.values,
    this.size = 240,
  }) : super(key: key);

  static const List<Color> _colors = [
    Color(0xFF22C55E), // Safe - green
    Color(0xFFFACC15), // Less Safe - yellow
    Color(0xFFFB923C), // Less Scam - orange
    Color(0xFFEF4444), // High Scam - red
  ];

  @override
  Widget build(BuildContext context) {
    final total = values.fold<int>(0, (a, b) => a + b);
    final sections = <PieChartSectionData>[];
    for (var i = 0; i < values.length; i++) {
      final value = values[i].toDouble();
      final percent = total == 0 ? 0.0 : (value / total) * 100;
      if (value <= 0) {
        sections.add(PieChartSectionData(
          color: _colors[i].withOpacity(0.12),
          value: 0.001,
          showTitle: false,
        ));
      } else {
        sections.add(PieChartSectionData(
          color: _colors[i],
          value: value,
          title: '${percent.toStringAsFixed(0)}%',
          radius: 56,
          titleStyle: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ));
      }
    }

    return Column(
      children: [
        SizedBox(
          width: size,
          height: size,
          child: PieChart(
            PieChartData(
              sections: sections,
              centerSpaceRadius: 36,
              sectionsSpace: 2,
              borderData: FlBorderData(show: false),
            ),
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 14,
          runSpacing: 8,
          alignment: WrapAlignment.center,
          children: List.generate(labels.length, (i) {
            final v = values[i];
            return Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(width: 12, height: 12, color: _colors[i]),
                const SizedBox(width: 6),
                Text('${labels[i]} — $v', style: const TextStyle(fontSize: 13)),
              ],
            );
          }),
        ),
      ],
    );
  }
}
