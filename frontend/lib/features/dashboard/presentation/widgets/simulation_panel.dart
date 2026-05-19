import 'package:flutter/material.dart';
import 'package:ciro_app/core/theme/app_theme.dart';

class SimulationPanel extends StatelessWidget {
  final List<dynamic> simulations;
  const SimulationPanel({super.key, required this.simulations});

  @override
  Widget build(BuildContext context) {
    if (simulations.isEmpty) {
      return const Card(
        color: AppTheme.cardDark,
        child: Center(
          child: Padding(
            padding: EdgeInsets.all(32.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.query_stats, size: 48, color: AppTheme.textSecondary),
                SizedBox(height: 12),
                Text(
                  'No active simulations running',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 4),
                Text(
                  'Ingest new signals to trigger agent simulation workflows.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                ),
              ],
            ),
          ),
        ),
      );
    }

    // Render the latest simulation run
    final latest = simulations.first;
    final double effectiveness = latest['overall_effectiveness'] ?? 0.0;
    final Map<String, dynamic> before = latest['before_state'] ?? {};
    final Map<String, dynamic> after = latest['after_state'] ?? {};
    final String responseAction = latest['response_action'] ?? 'None';
    final String recommendation = latest['recommendation'] ?? '';

    // Extract notifications from recommendation (retrieved from backend)
    String publicAlert = _extractSection(recommendation, '[PUBLIC ALERT]');
    String hospitalAlert = _extractSection(recommendation, '[HOSPITAL ALERT]');
    String utilityAlert = _extractSection(recommendation, '[UTILITY ALERT]');

    return Card(
      elevation: 0,
      color: AppTheme.cardDark,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.psychology, color: AppTheme.accentCyan, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'AI RESPONSE SIMULATION & PIVOT PANEL',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            letterSpacing: 1.2,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.accentCyan.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    'EFFECTIVENESS: ${(effectiveness * 100).toStringAsFixed(0)}%',
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppTheme.accentCyan,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              'ALLOCATION ACTIONS',
              style: TextStyle(fontSize: 10, letterSpacing: 1.0, color: Colors.blue.shade200, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppTheme.surfaceDark,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppTheme.primaryBlue.withValues(alpha: 0.2)),
              ),
              child: Text(
                responseAction,
                style: const TextStyle(fontSize: 12, height: 1.4, color: AppTheme.textPrimary),
              ),
            ),
            const SizedBox(height: 16),

            // Before vs. After comparison
            Row(
              children: [
                Expanded(
                  child: _buildStateSummary(
                    title: 'BASELINE (NO INTERVENTION)',
                    color: AppTheme.criticalRed,
                    affected: before['affected_population']?.toString() ?? '12,000',
                    severity: before['severity'] ?? 'CATASTROPHIC',
                    casualties: before['casualties_estimate']?.toString() ?? '8',
                    damage: '${before['infrastructure_damage_pct']?.toString() ?? '35'}%',
                    narrative: before['narrative'] ?? '',
                  ),
                ),
                const SizedBox(width: 12),
                const Icon(Icons.arrow_forward, color: AppTheme.accentCyan),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildStateSummary(
                    title: 'MITIGATED (AGENT PROJECTION)',
                    color: AppTheme.successGreen,
                    affected: after['affected_population']?.toString() ?? '5,000',
                    severity: after['severity'] ?? 'MODERATE',
                    casualties: after['casualties_estimate']?.toString() ?? '1',
                    damage: '${after['infrastructure_damage_pct']?.toString() ?? '15'}%',
                    narrative: after['narrative'] ?? '',
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Stakeholder Notifications
            Text(
              'AUTOMATED BROADCAST ALERTS',
              style: TextStyle(fontSize: 10, letterSpacing: 1.0, color: Colors.cyan.shade200, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            _buildNotificationCard(
              title: 'CIVIC BROADCAST (CELL CELLULAR)',
              icon: Icons.cell_tower,
              color: AppTheme.warningAmber,
              message: publicAlert.isNotEmpty 
                  ? publicAlert 
                  : 'Heatwave warning active in Sector F-8. Hydrate frequently.',
            ),
            const SizedBox(height: 8),
            _buildNotificationCard(
              title: 'HEALTH FACILITIES (PIMS EMERGENCY)',
              icon: Icons.local_hospital,
              color: AppTheme.criticalRed,
              message: hospitalAlert.isNotEmpty 
                  ? hospitalAlert 
                  : 'Coordinate medical rotation units for shared casualty surge.',
            ),
            const SizedBox(height: 8),
            _buildNotificationCard(
              title: 'UTILITIES (CDA SERVICE CREWS)',
              icon: Icons.engineering,
              color: AppTheme.primaryBlue,
              message: utilityAlert.isNotEmpty 
                  ? utilityAlert 
                  : 'Power transformers offline in sector F-8 to manage grid surge.',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStateSummary({
    required String title,
    required Color color,
    required String affected,
    required dynamic severity,
    required String casualties,
    required String damage,
    required String narrative,
  }) {
    String severityStr = severity.toString();
    if (severity is int) {
      severityStr = ['Minor', 'Moderate', 'Significant', 'Severe', 'Catastrophic'][severity - 1];
    }
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceDark,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.15)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: color),
          ),
          const SizedBox(height: 8),
          _buildMetricRow('Severity:', severityStr, color),
          const SizedBox(height: 4),
          _buildMetricRow('Exposure:', '$affected citizens', AppTheme.textPrimary),
          const SizedBox(height: 4),
          _buildMetricRow('Est. Casualties:', casualties, AppTheme.textPrimary),
          const SizedBox(height: 4),
          _buildMetricRow('Infra Damage:', damage, AppTheme.textPrimary),
          const SizedBox(height: 8),
          Text(
            narrative,
            style: const TextStyle(fontSize: 10, fontStyle: FontStyle.italic, color: AppTheme.textSecondary),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricRow(String label, String value, Color valueColor) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary)),
        Text(value, style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: valueColor)),
      ],
    );
  }

  Widget _buildNotificationCard({
    required String title,
    required IconData icon,
    required Color color,
    required String message,
  }) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppTheme.surfaceDark,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: color),
                ),
                const SizedBox(height: 4),
                Text(
                  message,
                  style: const TextStyle(fontSize: 11, color: AppTheme.textPrimary, height: 1.3),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _extractSection(String text, String marker) {
    final idx = text.indexOf(marker);
    if (idx == -1) return '';
    final sub = text.substring(idx + marker.length).trim();
    // Stop at the next marker
    final nextIdx = sub.indexOf('[');
    if (nextIdx == -1) return sub;
    return sub.substring(0, nextIdx).trim();
  }
}
