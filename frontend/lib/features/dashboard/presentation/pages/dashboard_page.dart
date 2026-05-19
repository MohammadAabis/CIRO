import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ciro_app/core/theme/app_theme.dart';
import 'package:ciro_app/features/dashboard/presentation/pages/ciro_provider.dart';
import 'package:ciro_app/features/dashboard/presentation/widgets/incident_map.dart';
import 'package:ciro_app/features/dashboard/presentation/widgets/simulation_panel.dart';
import 'package:ciro_app/features/dashboard/presentation/widgets/trace_terminal.dart';
import 'package:ciro_app/features/dashboard/presentation/widgets/signal_feed.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(ciroProvider);

    return Scaffold(
      backgroundColor: AppTheme.surfaceDark,
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: AppTheme.primaryBlue),
              ),
              child: const Text(
                'CIRO CORE',
                style: TextStyle(
                  fontSize: 12,
                  fontFamily: 'Courier',
                  fontWeight: FontWeight.w900,
                  color: AppTheme.accentCyan,
                ),
              ),
            ),
            const SizedBox(width: 12),
            const Text(
              'Crisis Intelligence & Response Orchestrator',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        actions: [
          // Backend connectivity indicator badge
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: state.isBackendOnline
                  ? AppTheme.successGreen.withValues(alpha: 0.1)
                  : AppTheme.criticalRed.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: state.isBackendOnline ? AppTheme.successGreen : AppTheme.criticalRed,
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: state.isBackendOnline ? AppTheme.successGreen : AppTheme.criticalRed,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  state.isBackendOnline ? 'BACKEND ONLINE' : 'LOCAL SIMULATOR ACTIVE',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: state.isBackendOnline ? AppTheme.successGreen : AppTheme.criticalRed,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh, color: AppTheme.accentCyan),
            onPressed: () => ref.read(ciroProvider.notifier).refreshData(),
          ),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isLargeScreen = constraints.maxWidth > 1024;
          
          if (isLargeScreen) {
            // High-end Desktop Grid Layout
            return Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Left panel: Grid Map + Signal Feed
                  Expanded(
                    flex: 4,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Expanded(
                          flex: 5,
                          child: IncidentMap(crises: state.crises),
                        ),
                        const SizedBox(height: 16),
                        Expanded(
                          flex: 4,
                          child: SignalFeed(
                            signals: state.rawSignals,
                            onIngest: (sector, report) => ref
                                .read(ciroProvider.notifier)
                                .triggerIngestSignal(sector, report),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 16),
                  
                  // Right panel: Simulation Dashboard + Trace Log Monospace Terminal
                  Expanded(
                    flex: 5,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Expanded(
                          flex: 5,
                          child: SimulationPanel(simulations: state.simulations),
                        ),
                        const SizedBox(height: 16),
                        Expanded(
                          flex: 4,
                          child: TraceTerminal(traceEntries: state.traceEntries),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          } else {
            // Adaptive Mobile scrolling layout
            return SingleChildScrollView(
              padding: const EdgeInsets.all(12.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  SizedBox(
                    height: 280,
                    child: IncidentMap(crises: state.crises),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    height: 260,
                    child: SignalFeed(
                      signals: state.rawSignals,
                      onIngest: (sector, report) => ref
                          .read(ciroProvider.notifier)
                          .triggerIngestSignal(sector, report),
                    ),
                  ),
                  const SizedBox(height: 12),
                  SimulationPanel(simulations: state.simulations),
                  const SizedBox(height: 12),
                  SizedBox(
                    height: 300,
                    child: TraceTerminal(traceEntries: state.traceEntries),
                  ),
                ],
              ),
            );
          }
        },
      ),
    );
  }
}
