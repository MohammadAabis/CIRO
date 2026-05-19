import 'dart:math';
import 'package:flutter/material.dart';
import 'package:ciro_app/core/theme/app_theme.dart';

class IncidentMap extends StatefulWidget {
  final List<dynamic> crises;
  const IncidentMap({super.key, required this.crises});

  @override
  State<IncidentMap> createState() => _IncidentMapState();
}

class _IncidentMapState extends State<IncidentMap> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      color: AppTheme.cardDark,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      width: 10,
                      height: 10,
                      decoration: const BoxDecoration(
                        color: AppTheme.accentCyan,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'TACTICAL METROPOLITAN GRID',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            letterSpacing: 1.5,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceDark,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppTheme.primaryBlue.withValues(alpha: 0.3)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.gps_fixed, size: 12, color: AppTheme.accentCyan),
                      SizedBox(width: 4),
                      Text(
                        'ISLAMABAD METRO G-10 / F-8',
                        style: TextStyle(fontSize: 10, color: AppTheme.accentCyan, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              decoration: BoxDecoration(
                color: AppTheme.surfaceDark,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.withValues(alpha: 0.1)),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) {
                    return CustomPaint(
                      painter: TacticalMapPainter(
                        crises: widget.crises,
                        pulseValue: _pulseController.value,
                      ),
                      child: Stack(
                        children: _buildCrisisLabels(),
                      ),
                    );
                  },
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildCrisisLabels() {
    return widget.crises.map<Widget>((crisis) {
      final String title = crisis['title'] ?? 'Crisis';
      final bool isFlood = title.toLowerCase().contains('flood');
      final bool isFalseAlarm = crisis['is_false_alarm'] ?? false;
      final int severity = crisis['severity'] ?? 3;

      // Sector positions mapped to absolute canvas ratios
      double left = isFlood ? 0.25 : 0.68;
      double top = isFlood ? 0.65 : 0.30;

      return Positioned(
        left: left * 320, // Approximate width scale
        top: top * 260,  // Approximate height scale
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: AppTheme.surfaceDark.withValues(alpha: 0.85),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(
              color: isFalseAlarm
                  ? AppTheme.successGreen
                  : AppTheme.severityColors[min(4, severity - 1)],
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                isFlood ? 'SECTOR G-10' : 'SECTOR F-8',
                style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.white70),
              ),
              Text(
                isFalseAlarm ? 'WATER MAIN burst' : (isFlood ? 'URBAN FLOOD' : 'HEATWAVE'),
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w900,
                  color: isFalseAlarm
                      ? AppTheme.successGreen
                      : AppTheme.severityColors[min(4, severity - 1)],
                ),
              ),
            ],
          ),
        ),
      );
    }).toList();
  }
}

class TacticalMapPainter extends CustomPainter {
  final List<dynamic> crises;
  final double pulseValue;

  TacticalMapPainter({required this.crises, required this.pulseValue});

  @override
  void paint(Canvas canvas, Size size) {
    final gridPaint = Paint()
      ..color = Colors.blue.withValues(alpha: 0.04)
      ..strokeWidth = 1.0;

    // Draw Tactical Grid lines
    const int gridSpacing = 20;
    for (double x = 0; x < size.width; x += gridSpacing) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), gridPaint);
    }
    for (double y = 0; y < size.height; y += gridSpacing) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    // Draw concentric telemetry radar lines
    final radarPaint = Paint()
      ..color = Colors.blue.withValues(alpha: 0.08)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    
    final center = Offset(size.width / 2, size.height / 2);
    canvas.drawCircle(center, size.width * 0.2, radarPaint);
    canvas.drawCircle(center, size.width * 0.35, radarPaint);
    
    // Draw Islamabad sector division boundaries (G-10, G-9, F-8, F-7)
    final boundaryPaint = Paint()
      ..color = Colors.cyan.withValues(alpha: 0.12)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    
    final path = Path()
      ..moveTo(size.width * 0.5, 0)
      ..lineTo(size.width * 0.5, size.height)
      ..moveTo(0, size.height * 0.5)
      ..lineTo(size.width, size.height * 0.5);
    canvas.drawPath(path, boundaryPaint);

    // Draw active crisis sectors
    for (final crisis in crises) {
      final String title = crisis['title'] ?? 'Crisis';
      final bool isFlood = title.toLowerCase().contains('flood');
      final bool isFalseAlarm = crisis['is_false_alarm'] ?? false;
      final int severity = crisis['severity'] ?? 3;

      Color mainColor = isFalseAlarm
          ? AppTheme.successGreen
          : AppTheme.severityColors[min(4, severity - 1)];

      // Grid location coordinates mapping
      double rx = isFlood ? 0.32 : 0.75;
      double ry = isFlood ? 0.72 : 0.38;

      final crisisCenter = Offset(size.width * rx, size.height * ry);

      // Blinking expanding pulse ring
      final pulsePaint = Paint()
        ..color = mainColor.withValues(alpha: 1.0 - pulseValue)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.0;
      canvas.drawCircle(crisisCenter, 15 + (pulseValue * 30), pulsePaint);

      // Inner solid warning hub
      final hubPaint = Paint()
        ..color = mainColor.withValues(alpha: 0.4)
        ..style = PaintingStyle.fill;
      canvas.drawCircle(crisisCenter, 12, hubPaint);

      final corePaint = Paint()
        ..color = mainColor
        ..style = PaintingStyle.fill;
      canvas.drawCircle(crisisCenter, 4, corePaint);
    }
  }

  @override
  bool shouldRepaint(covariant TacticalMapPainter oldDelegate) {
    return oldDelegate.pulseValue != pulseValue || oldDelegate.crises != crises;
  }
}
