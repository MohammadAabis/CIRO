import 'package:flutter/material.dart';
import 'package:ciro_app/core/theme/app_theme.dart';
import 'package:intl/intl.dart';

class SignalFeed extends StatefulWidget {
  final List<Map<String, dynamic>> signals;
  final Function(String sector, String report) onIngest;
  const SignalFeed({super.key, required this.signals, required this.onIngest});

  @override
  State<SignalFeed> createState() => _SignalFeedState();
}

class _SignalFeedState extends State<SignalFeed> {
  final TextEditingController _customReportController = TextEditingController();
  final String _selectedSector = 'G-10';

  @override
  void dispose() {
    _customReportController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      color: AppTheme.cardDark,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.sensors, color: AppTheme.accentCyan, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'MULTI-SOURCE SIGNAL INGESTION & STRESS HUB',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          letterSpacing: 1.2,
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Scenario quick-trigger grid
            Text(
              'INJECT TELEMETRY / FIELD REPORT SCENARIO',
              style: TextStyle(
                  fontSize: 10,
                  letterSpacing: 1.0,
                  color: Colors.blue.shade200,
                  fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  SizedBox(
                    width: 140,
                    child: _buildScenarioButton(
                      title: 'Inject Flood Telemetry',
                      subtitle: 'G-10 Sector Flood Warning',
                      icon: Icons.thunderstorm,
                      color: AppTheme.primaryBlue,
                      onTap: () => widget.onIngest(
                        'G-10',
                        'CRITICAL STORM REPORT: G-10 drains overflowed, 82mm rain. Water height +50cm. Commencing basement flooding alerts.',
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  SizedBox(
                    width: 140,
                    child: _buildScenarioButton(
                      title: 'Inject Field Correction',
                      subtitle: 'Water Main Burst (False Alarm)',
                      icon: Icons.build,
                      color: AppTheme.successGreen,
                      onTap: () => widget.onIngest(
                        'G-10',
                        'FIELD UPDATE: Burst water main on 7th Avenue confirmed (12 PSI). Flash flood warning retracted. Locals report pipe leak.',
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  SizedBox(
                    width: 140,
                    child: _buildScenarioButton(
                      title: 'Inject Heatwave Telemetry',
                      subtitle: 'F-8 Extreme Thermal Surge',
                      icon: Icons.light_mode,
                      color: AppTheme.warningAmber,
                      onTap: () => widget.onIngest(
                        'F-8',
                        'MET THERMAL SURGE: 47°C recorded in F-8 Markaz. 3 hyperthermia collapses. Requesting urgent cooling dispatch.',
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Live signal list ticker
            Text(
              'LIVE INGESTED RAW SIGNALS FEED',
              style: TextStyle(
                  fontSize: 10,
                  letterSpacing: 1.0,
                  color: Colors.cyan.shade200,
                  fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: widget.signals.isEmpty
                  ? const Center(
                      child: Text(
                        'Awaiting signal ingestion...',
                        style: TextStyle(color: AppTheme.textSecondary),
                      ),
                    )
                  : ListView.builder(
                      itemCount: widget.signals.length,
                      itemBuilder: (context, index) {
                        final sig = widget.signals[index];
                        final timeStr = _formatTimestamp(sig['timestamp']);
                        final String source = sig['source'] ?? 'api';
                        final String text = sig['raw_text'] ?? '';
                        final double credibility =
                            sig['reliability_score'] ?? 0.5;

                        IconData sourceIcon = Icons.feed;
                        Color sourceColor = AppTheme.primaryBlue;

                        if (source.contains('weather')) {
                          sourceIcon = Icons.cloud;
                          sourceColor = Colors.lightBlueAccent;
                        } else if (source.contains('social')) {
                          sourceIcon = Icons.chat_bubble;
                          sourceColor = Colors.purpleAccent;
                        } else if (source.contains('traffic')) {
                          sourceIcon = Icons.traffic;
                          sourceColor = AppTheme.warningAmber;
                        } else if (source.contains('iot')) {
                          sourceIcon = Icons.settings_remote;
                          sourceColor = AppTheme.accentCyan;
                        } else if (source.contains('citizen')) {
                          sourceIcon = Icons.person;
                          sourceColor = AppTheme.successGreen;
                        }

                        return Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: AppTheme.surfaceDark,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                                color: Colors.white.withValues(alpha: 0.04)),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(sourceIcon, color: sourceColor, size: 18),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.spaceBetween,
                                      children: [
                                        Text(
                                          source
                                              .toUpperCase()
                                              .replaceAll('_', ' '),
                                          style: TextStyle(
                                            fontSize: 9,
                                            fontWeight: FontWeight.bold,
                                            color: sourceColor,
                                          ),
                                        ),
                                        Text(
                                          'CREDIBILITY: ${(credibility * 100).toStringAsFixed(0)}%',
                                          style: const TextStyle(
                                            fontSize: 8,
                                            color: AppTheme.textSecondary,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      text,
                                      style: const TextStyle(
                                          fontSize: 11,
                                          color: AppTheme.textPrimary,
                                          height: 1.3),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      'INGESTED AT $timeStr',
                                      style: const TextStyle(
                                          fontSize: 8,
                                          color: Colors.white24,
                                          fontWeight: FontWeight.bold),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildScenarioButton({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: AppTheme.surfaceDark,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withValues(alpha: 0.3)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 8),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: Colors.white70),
            ),
            const SizedBox(height: 2),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style:
                  const TextStyle(fontSize: 8, color: AppTheme.textSecondary),
            ),
          ],
        ),
      ),
    );
  }

  String _formatTimestamp(dynamic timestamp) {
    if (timestamp == null) return '';
    try {
      final parsed = DateTime.parse(timestamp.toString()).toLocal();
      return DateFormat('HH:mm:ss').format(parsed);
    } catch (_) {
      return timestamp.toString();
    }
  }
}
