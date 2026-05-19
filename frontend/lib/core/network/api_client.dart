import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

/// Central API Client for CIRO backend.
/// Connects to local or remote backend and falls back to mock data if offline.
class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();

  // Configurable base URL
  String baseUrl = 'http://127.0.0.1:8000';

  final Dio _dio = Dio(BaseOptions(
    connectTimeout: const Duration(seconds: 4),
    receiveTimeout: const Duration(seconds: 8),
  ));

  /// Check health of backend
  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get('$baseUrl/health');
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Ingest raw signal data
  Future<Map<String, dynamic>> ingestSignal(Map<String, dynamic> payload) async {
    try {
      final response = await _dio.post('$baseUrl/api/v1/ingest', data: payload);
      return response.data;
    } catch (e) {
      debugPrint('Error ingesting signal: $e');
      return {'status': 'failed', 'reason': e.toString()};
    }
  }

  /// Get crises dashboard stats
  Future<Map<String, dynamic>> getStats() async {
    try {
      final response = await _dio.get('$baseUrl/api/v1/crises/stats');
      return response.data;
    } catch (e) {
      debugPrint('Error getting stats: $e');
      // Return offline simulation stats
      return _mockStats();
    }
  }

  /// List crises
  Future<Map<String, dynamic>> getCrises() async {
    try {
      final response = await _dio.get('$baseUrl/api/v1/crises/');
      return response.data;
    } catch (e) {
      debugPrint('Error getting crises: $e');
      return _mockCrises();
    }
  }

  /// List resources
  Future<Map<String, dynamic>> getResources() async {
    try {
      final response = await _dio.get('$baseUrl/api/v1/resources/');
      return response.data;
    } catch (e) {
      debugPrint('Error getting resources: $e');
      return _mockResources();
    }
  }

  /// List simulations
  Future<List<dynamic>> getSimulations() async {
    try {
      final response = await _dio.get('$baseUrl/api/v1/simulations/');
      final data = response.data;
      if (data is Map && data.containsKey('simulations')) {
        return data['simulations'];
      }
      return [];
    } catch (e) {
      debugPrint('Error getting simulations: $e');
      return _mockSimulations();
    }
  }

  /// Stream SSE trace entries natively from the backend
  Stream<Map<String, dynamic>> streamTraceEntries() {
    final controller = StreamController<Map<String, dynamic>>();
    bool isClosed = false;

    void startStream() async {
      while (!isClosed) {
        try {
          final client = await Dio().get<ResponseBody>(
            '$baseUrl/api/v1/traces/stream',
            options: Options(
              responseType: ResponseType.stream,
              headers: {'Accept': 'text/event-stream'},
            ),
          );

          await for (final chunk in client.data!.stream) {
            if (isClosed) break;
            final text = utf8.decode(chunk);
            final lines = text.split('\n');
            for (final line in lines) {
              if (line.startsWith('data: ')) {
                final jsonStr = line.substring(6).trim();
                if (jsonStr.isNotEmpty) {
                  try {
                    final data = json.decode(jsonStr);
                    if (!controller.isClosed) {
                      controller.add(data);
                    }
                  } catch (_) {
                    // Ignore keepalive comment or malformed json
                  }
                }
              }
            }
          }
        } catch (e) {
          debugPrint('Trace stream error: $e. Retrying in 5 seconds...');
          await Future.delayed(const Duration(seconds: 5));
        }
      }
    }

    startStream();

    controller.onCancel = () {
      isClosed = true;
      controller.close();
    };

    return controller.stream;
  }

  // ──────────────────────────────────────────────
  // Offline High-Fidelity Mock Data Fallbacks
  // ──────────────────────────────────────────────

  Map<String, dynamic> _mockStats() {
    return {
      'total_signals': 11,
      'active_crises': 2,
      'false_alarms': 1,
      'total_simulations': 2,
      'resources': {
        'total': 29,
        'available': 25,
        'deployed': 4,
        'summary': {
          'ambulance': {'available': 4, 'deployed': 2, 'total': 6},
          'police': {'available': 6, 'deployed': 2, 'total': 8},
          'rescue_team': {'available': 4, 'deployed': 0, 'total': 4},
          'fire_brigade': {'available': 3, 'deployed': 0, 'total': 3},
          'medical_staff': {'available': 5, 'deployed': 0, 'total': 5},
          'evacuation_bus': {'available': 3, 'deployed': 0, 'total': 3}
        }
      }
    };
  }

  Map<String, dynamic> _mockCrises() {
    return {
      'count': 2,
      'crises': [
        {
          'id': 'e605fa8a-6b45-4277-96a8-f7efdf7b4b1a',
          'crisis_type': 'urban_flood',
          'title': 'Urban Flooding — G-10 Islamabad',
          'description': 'Basements submerged, traffic grids locked near main market, 12,000 residents affected.',
          'severity': 4,
          'confidence': 0.87,
          'location': {'latitude': 33.6844, 'longitude': 73.0479, 'label': 'G-10/4, Islamabad'},
          'is_false_alarm': false
        },
        {
          'id': 'f882fa8a-92bc-4488-b39b-e7b8f8fa3b7b',
          'crisis_type': 'heatwave',
          'title': 'Extreme Heatwave — F-8 Islamabad',
          'description': 'Temperature 47°C, heat index 52°C. Medical pool is shared between F-8 and G-10.',
          'severity': 3,
          'confidence': 0.91,
          'location': {'latitude': 33.7060, 'longitude': 73.0551, 'label': 'F-8/3, Islamabad'},
          'is_false_alarm': false
        }
      ]
    };
  }

  Map<String, dynamic> _mockResources() {
    return {
      'total_units': 29,
      'summary': {
        'ambulance': {'available': 4, 'deployed': 2, 'total': 6},
        'police': {'available': 6, 'deployed': 2, 'total': 8},
        'rescue_team': {'available': 4, 'deployed': 0, 'total': 4},
        'fire_brigade': {'available': 3, 'deployed': 0, 'total': 3},
        'medical_staff': {'available': 5, 'deployed': 0, 'total': 5},
        'evacuation_bus': {'available': 3, 'deployed': 0, 'total': 3}
      }
    };
  }

  List<dynamic> _mockSimulations() {
    return [
      {
        'crisis_id': 'e605fa8a-6b45-4277-96a8-f7efdf7b4b1a',
        'response_action': 'Deploy 4 rescue teams + 3 ambulances to G-10. Evacuate low-lying blocks via 2 buses.',
        'overall_effectiveness': 0.73,
        'before_state': {
          'severity': 5,
          'affected_population': 15000,
          'infrastructure_damage_pct': 35.0,
          'casualties_estimate': 12,
          'economic_impact_usd': 2500000,
          'narrative': 'Structurally flooded basements and major health injuries'
        },
        'after_state': {
          'severity': 3,
          'affected_population': 8000,
          'infrastructure_damage_pct': 18.0,
          'casualties_estimate': 2,
          'economic_impact_usd': 900000,
          'narrative': 'Evacuation saves lives; pumps draining market squares'
        },
        'side_effects': [
          {'description': 'Khayaban closed for command vehicle staging', 'probability': 0.8}
        ],
        'recommendation': 'IMMEDIATE DISPATCH of G-10 elements. [PUBLIC ALERT] High flood waters in Sector G-10. Seek high ground. [HOSPITAL ALERT] PIMS ER trauma capacity alert.'
      }
    ];
  }
}
