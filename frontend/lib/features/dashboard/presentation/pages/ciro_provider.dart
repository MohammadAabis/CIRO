import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ciro_app/core/network/api_client.dart';

class CiroState {
  final bool isBackendOnline;
  final Map<String, dynamic> stats;
  final List<dynamic> crises;
  final List<dynamic> resources;
  final List<dynamic> simulations;
  final List<Map<String, dynamic>> traceEntries;
  final List<Map<String, dynamic>> rawSignals;
  final bool isLoading;

  CiroState({
    required this.isBackendOnline,
    required this.stats,
    required this.crises,
    required this.resources,
    required this.simulations,
    required this.traceEntries,
    required this.rawSignals,
    required this.isLoading,
  });

  CiroState copyWith({
    bool? isBackendOnline,
    Map<String, dynamic>? stats,
    List<dynamic>? crises,
    List<dynamic>? resources,
    List<dynamic>? simulations,
    List<Map<String, dynamic>>? traceEntries,
    List<Map<String, dynamic>>? rawSignals,
    bool? isLoading,
  }) {
    return CiroState(
      isBackendOnline: isBackendOnline ?? this.isBackendOnline,
      stats: stats ?? this.stats,
      crises: crises ?? this.crises,
      resources: resources ?? this.resources,
      simulations: simulations ?? this.simulations,
      traceEntries: traceEntries ?? this.traceEntries,
      rawSignals: rawSignals ?? this.rawSignals,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}

class CiroNotifier extends StateNotifier<CiroState> {
  final ApiClient _api = ApiClient.instance;
  StreamSubscription? _traceSubscription;
  Timer? _refreshTimer;

  CiroNotifier()
      : super(CiroState(
          isBackendOnline: false,
          stats: {},
          crises: [],
          resources: [],
          simulations: [],
          traceEntries: [],
          rawSignals: [],
          isLoading: true,
        )) {
    init();
  }

  Future<void> init() async {
    await refreshData();
    _startPeriodicRefresh();
    _startTraceStreaming();
  }

  Future<void> refreshData() async {
    final online = await _api.checkHealth();

    // Fetch stats
    final statsData = await _api.getStats();

    // Fetch crises list
    final crisesResponse = await _api.getCrises();
    final crisesList = crisesResponse['crises'] ?? [];

    // Fetch resources inventory
    final resourcesResponse = await _api.getResources();
    final resourcesList = resourcesResponse['summary'] != null
        ? [resourcesResponse['summary']]
        : [];

    // Fetch simulations
    final simsList = await _api.getSimulations();

    // Pull mock signals to feed the dashboard signal ticker
    final signalsList = _getInitialSignals();

    state = state.copyWith(
      isBackendOnline: online,
      stats: statsData,
      crises: crisesList,
      resources: resourcesList,
      simulations: simsList,
      rawSignals: signalsList,
      isLoading: false,
    );
  }

  void _startPeriodicRefresh() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      refreshData();
    });
  }

  void _startTraceStreaming() {
    _traceSubscription?.cancel();
    _traceSubscription = _api.streamTraceEntries().listen((entry) {
      final updatedTraces = List<Map<String, dynamic>>.from(state.traceEntries)
        ..insert(0, entry);

      // If we see a live signal processing entry, we append to our signal ticker feed!
      List<Map<String, dynamic>> updatedSignals =
          List<Map<String, dynamic>>.from(state.rawSignals);
      if (entry['action'] == 'fuse_multisource_signals') {
        updatedSignals.insert(0, {
          'timestamp': DateTime.now().toIsoformatString(),
          'source': 'signal_fusion',
          'raw_text': 'FUSING PIPELINE EVENT: ${entry['output_summary']}',
          'reliability_score': 0.95
        });
      }

      state = state.copyWith(
        traceEntries: updatedTraces,
        rawSignals: updatedSignals,
      );
    });
  }

  Future<void> triggerIngestSignal(String sector, String report) async {
    final payload = {
      'source': 'citizen_report',
      'raw_text': 'FIELD UPDATE: $report',
      'location': {
        'latitude': sector == 'G-10' ? 33.6840 : 33.7060,
        'longitude': sector == 'G-10' ? 73.0490 : 73.0551,
        'label': sector == 'G-10' ? '7th Ave / G-10 junction' : 'F-8 Markaz'
      },
      'reliability_score': 0.95
    };

    // Add local optimistic signal to ticker feed
    final localSig = {
      'timestamp': DateTime.now().toIsoformatString(),
      'source': 'citizen_report',
      'raw_text': report,
      'reliability_score': 0.95
    };

    state = state.copyWith(
      rawSignals: [localSig, ...state.rawSignals],
    );

    await _api.ingestSignal(payload);
    await refreshData();
  }

  List<Map<String, dynamic>> _getInitialSignals() {
    return [
      {
        'timestamp': DateTime.now()
            .subtract(const Duration(minutes: 5))
            .toIsoformatString(),
        'source': 'weather_api',
        'raw_text':
            'ALERT: Severe flash flood threat over Sector G-10. Drains active.',
        'reliability_score': 0.95
      },
      {
        'timestamp': DateTime.now()
            .subtract(const Duration(minutes: 12))
            .toIsoformatString(),
        'source': 'citizen_report',
        'raw_text': 'Water levels rising inside F-8 Markaz basements.',
        'reliability_score': 0.70
      },
      {
        'timestamp': DateTime.now()
            .subtract(const Duration(minutes: 18))
            .toIsoformatString(),
        'source': 'iot_device',
        'raw_text': 'Sector G-10 Line Water Pressure Drop: 12 PSI detected.',
        'reliability_score': 0.90
      }
    ];
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _traceSubscription?.cancel();
    super.dispose();
  }
}

extension on DateTime {
  String toIsoformatString() => toUtc().toIso8601String();
}

final ciroProvider = StateNotifierProvider<CiroNotifier, CiroState>((ref) {
  return CiroNotifier();
});
