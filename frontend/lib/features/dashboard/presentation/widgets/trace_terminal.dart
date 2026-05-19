import 'package:flutter/material.dart';
import 'package:ciro_app/core/theme/app_theme.dart';
import 'package:intl/intl.dart';

class TraceTerminal extends StatelessWidget {
  final List<Map<String, dynamic>> traceEntries;
  const TraceTerminal({super.key, required this.traceEntries});

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
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.terminal,
                        color: AppTheme.successGreen, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'ANTIGRAVITY AGENT THINKING TERMINAL (LIVE TRACE)',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            letterSpacing: 1.2,
                            fontWeight: FontWeight.bold,
                            fontFamily: 'Courier',
                          ),
                    ),
                  ],
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.successGreen.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: const BoxDecoration(
                          color: AppTheme.successGreen,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 6),
                      const Text(
                        'STREAM ACTIVE',
                        style: TextStyle(
                          fontSize: 10,
                          color: AppTheme.successGreen,
                          fontWeight: FontWeight.bold,
                          fontFamily: 'Courier',
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.85),
                  borderRadius: BorderRadius.circular(8),
                  border:
                      Border.all(color: AppTheme.successGreen.withValues(alpha: 0.3)),
                ),
                child: traceEntries.isEmpty
                    ? const Center(
                        child: Text(
                          '> SYSTEM READY. AWAITING PIPELINE SIGNAL TRIGGERS...\n> SSE LISTENER ATTACHED AT /api/v1/traces/stream',
                          style: TextStyle(
                            color: AppTheme.successGreen,
                            fontSize: 12,
                            fontFamily: 'Courier',
                            height: 1.5,
                          ),
                        ),
                      )
                    : ListView.builder(
                        reverse: false,
                        itemCount: traceEntries.length,
                        itemBuilder: (context, index) {
                          final entry = traceEntries[index];
                          final timeStr = _formatTimestamp(entry['timestamp']);
                          final String agent = entry['agent_name'] ?? 'System';
                          final String action = entry['action'] ?? 'dispatch';
                          final String inp = entry['input_summary'] ?? '';
                          final String out = entry['output_summary'] ?? '';
                          final int ms = entry['duration_ms'] ?? 0;
                          final bool isError =
                              entry['metadata']?['error'] ?? false;

                          Color agentColor = AppTheme.successGreen;
                          if (agent.contains('Fusion')) {
                            agentColor = AppTheme.accentCyan;
                          }
                          if (agent.contains('Classifier')) {
                            agentColor = AppTheme.warningAmber;
                          }
                          if (agent.contains('Allocator')) {
                            agentColor = AppTheme.primaryBlue;
                          }
                          if (agent.contains('Simulator') ||
                              agent.contains('Simulation')) {
                            agentColor = Colors.purpleAccent;
                          }

                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Text(
                                      '[$timeStr] ',
                                      style: const TextStyle(
                                        color: Colors.white24,
                                        fontSize: 11,
                                        fontFamily: 'Courier',
                                      ),
                                    ),
                                    Text(
                                      agent,
                                      style: TextStyle(
                                        color: agentColor,
                                        fontSize: 11,
                                        fontWeight: FontWeight.bold,
                                        fontFamily: 'Courier',
                                      ),
                                    ),
                                    const Text(
                                      ' :: ',
                                      style: TextStyle(
                                        color: Colors.white24,
                                        fontFamily: 'Courier',
                                      ),
                                    ),
                                    Text(
                                      action,
                                      style: TextStyle(
                                        color: isError
                                            ? Colors.redAccent
                                            : Colors.white70,
                                        fontSize: 11,
                                        fontFamily: 'Courier',
                                      ),
                                    ),
                                    const Spacer(),
                                    Text(
                                      '${ms}ms',
                                      style: const TextStyle(
                                        color: Colors.white24,
                                        fontSize: 10,
                                        fontFamily: 'Courier',
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Padding(
                                  padding: const EdgeInsets.only(left: 16.0),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '>> IN : $inp',
                                        style: TextStyle(
                                          color: Colors.white.withValues(alpha: 0.4),
                                          fontSize: 11,
                                          fontFamily: 'Courier',
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        '<< OUT: $out',
                                        style: TextStyle(
                                          color: isError
                                              ? Colors.redAccent
                                              : AppTheme.successGreen
                                                  .withValues(alpha: 0.95),
                                          fontSize: 11,
                                          fontFamily: 'Courier',
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Divider(
                                    color: Colors.white.withValues(alpha: 0.05),
                                    height: 1),
                              ],
                            ),
                          );
                        },
                      ),
              ),
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
      return DateFormat('HH:mm:ss.SSS').format(parsed);
    } catch (_) {
      return timestamp.toString();
    }
  }
}
