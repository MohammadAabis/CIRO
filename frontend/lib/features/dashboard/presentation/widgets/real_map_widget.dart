// ═══════════════════════════════════════════════════════════════
// CLEAN REAL MAP WIDGET - Copy this entire content
// Replace: frontend/lib/features/dashboard/presentation/widgets/real_map_widget.dart
// ═══════════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:ciro_app/core/theme/app_theme.dart';

class RealMapWidget extends StatefulWidget {
  final List<dynamic> crises;
  const RealMapWidget({super.key, required this.crises});

  @override
  State<RealMapWidget> createState() => _RealMapWidgetState();
}

class _RealMapWidgetState extends State<RealMapWidget>
    with SingleTickerProviderStateMixin {
  late GoogleMapController _mapController;
  late AnimationController _pulseController;
  final Set<Marker> _markers = {};
  final Set<Polyline> _polylines = {};
  bool _mapLoaded = false;

  // Islamabad coordinates
  static const LatLng _islamabadCenter = LatLng(33.6844, 73.0479);
  static const LatLng _g10Sector = LatLng(33.7, 73.0);
  static const LatLng _f8Sector = LatLng(33.67, 73.18);

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
    _buildMarkers();
    _mapLoaded = true;
  }

  @override
  void didUpdateWidget(RealMapWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.crises != widget.crises) {
      _buildMarkers();
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  void _buildMarkers() {
    _markers.clear();
    _polylines.clear();

    // Add crisis markers
    for (int i = 0; i < widget.crises.length; i++) {
      final crisis = widget.crises[i];
      final String title = crisis['title'] ?? 'Crisis';
      // Severity is now a string ("1"-"5"), convert to int
      final String severityStr = crisis['severity']?.toString() ?? '3';
      final int severity = int.tryParse(severityStr) ?? 3;
      final bool isFlood = title.toLowerCase().contains('flood');

      final LatLng position = isFlood ? _g10Sector : _f8Sector;

      BitmapDescriptor icon;
      if (severity >= 4) {
        icon = BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed);
      } else if (severity >= 3) {
        icon =
            BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueOrange);
      } else {
        icon =
            BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueOrange);
      }

      _markers.add(
        Marker(
          markerId: MarkerId('crisis_$i'),
          position: position,
          infoWindow: InfoWindow(
            title: title,
            snippet: 'Severity: $severity/5',
          ),
          icon: icon,
        ),
      );
    }

    // Add resource markers
    _addResourceMarkers();
    setState(() {});
  }

  void _addResourceMarkers() {
    // Hospitals
    final hospitals = [
      {'name': 'Polyclinic', 'lat': 33.68, 'lon': 73.19},
      {'name': 'Federal Medical', 'lat': 33.67, 'lon': 73.17},
    ];
    for (final h in hospitals) {
      _markers.add(
        Marker(
          markerId: MarkerId('hospital_${h['name']}'),
          position: LatLng(h['lat'] as double, h['lon'] as double),
          infoWindow: InfoWindow(
            title: h['name'] as String,
            snippet: 'Hospital',
          ),
          icon:
              BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        ),
      );
    }

    // Fire Stations
    final fireStations = [
      {'name': 'Sector G-10', 'lat': 33.71, 'lon': 73.00},
      {'name': 'Sector F-8', 'lat': 33.67, 'lon': 73.18},
    ];
    for (final f in fireStations) {
      _markers.add(
        Marker(
          markerId: MarkerId('fire_${f['name']}'),
          position: LatLng(f['lat'] as double, f['lon'] as double),
          infoWindow: InfoWindow(
            title: f['name'] as String,
            snippet: 'Fire Station',
          ),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
        ),
      );
    }

    // Police
    final police = [
      {'name': 'Aabpara', 'lat': 33.72, 'lon': 73.02},
      {'name': 'Federal Complex', 'lat': 33.68, 'lon': 73.19},
    ];
    for (final p in police) {
      _markers.add(
        Marker(
          markerId: MarkerId('police_${p['name']}'),
          position: LatLng(p['lat'] as double, p['lon'] as double),
          infoWindow: InfoWindow(
            title: p['name'] as String,
            snippet: 'Police Station',
          ),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
        ),
      );
    }
  }

  void _onMapCreated(GoogleMapController controller) {
    _mapController = controller;
    setState(() => _mapLoaded = true);

    // Simple camera animation with timeout
    Future.delayed(const Duration(milliseconds: 500), () {
      if (mounted) {
        try {
          _mapController.animateCamera(
            CameraUpdate.newCameraPosition(
              const CameraPosition(
                target: _islamabadCenter,
                zoom: 13.5,
              ),
            ),
          );
        } catch (e) {
          debugPrint('Camera animation error: $e');
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      color: AppTheme.cardDark,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
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
                  'REAL-TIME CRISIS MAP',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        letterSpacing: 1.5,
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ],
            ),
          ),
          // Map - Google Maps iframe for web
          Expanded(
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.withValues(alpha: 0.1)),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: _buildMapView(),
              ),
            ),
          ),
          // Legend
          Container(
            padding: const EdgeInsets.all(12),
            margin:
                const EdgeInsets.only(left: 16, right: 16, bottom: 16, top: 12),
            decoration: BoxDecoration(
              color: AppTheme.surfaceDark,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                  color: AppTheme.primaryBlue.withValues(alpha: 0.2)),
            ),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildLegendItem('🔴', 'Crisis (Severe)'),
                  const SizedBox(width: 16),
                  _buildLegendItem('🟠', 'Crisis (Low)'),
                  const SizedBox(width: 16),
                  _buildLegendItem('🔵', 'Hospital'),
                  const SizedBox(width: 16),
                  _buildLegendItem('🔴', 'Fire Station'),
                  const SizedBox(width: 16),
                  _buildLegendItem('🟢', 'Police'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLegendItem(String icon, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(icon, style: const TextStyle(fontSize: 14)),
        const SizedBox(width: 6),
        Text(
          label,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                fontSize: 11,
              ),
        ),
      ],
    );
  }

  Widget _buildMapView() {
    // Platform detection
    if (kIsWeb) {
      // Web: Show crisis list (Google Maps plugin doesn't work on web)
      return _buildCrisisListView();
    } else {
      // Mobile (Android/iOS): Show real Google Map
      return GoogleMap(
        onMapCreated: _onMapCreated,
        initialCameraPosition: const CameraPosition(
          target: _islamabadCenter,
          zoom: 13,
        ),
        markers: _markers,
        polylines: _polylines,
        compassEnabled: true,
        myLocationEnabled: false,
        myLocationButtonEnabled: false,
        mapType: MapType.normal,
        trafficEnabled: false,
        buildingsEnabled: true,
      );
    }
  }

  Widget _buildCrisisListView() {
    // Build crisis markers for web display
    _buildMarkers();
    
    // If no crises, show empty state
    if (_markers.isEmpty) {
      return Container(
        color: AppTheme.surfaceDark,
        child: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.location_on, size: 48, color: AppTheme.textSecondary),
              SizedBox(height: 16),
              Text(
                'No active crises detected',
                style: TextStyle(color: AppTheme.textSecondary),
              ),
            ],
          ),
        ),
      );
    }

    // Show crisis cards
    return Container(
      color: AppTheme.surfaceDark,
      child: SingleChildScrollView(
        child: Column(
          children: _markers
              .where((m) => m.markerId.value.contains('crisis'))
              .map((marker) => Container(
                    margin: const EdgeInsets.all(8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.cardDark,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                          color: AppTheme.primaryBlue.withValues(alpha: 0.3)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 12,
                              height: 12,
                              decoration: const BoxDecoration(
                                color: Colors.red,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    marker.infoWindow.title ?? 'Crisis',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: Colors.white,
                                    ),
                                  ),
                                  Text(
                                    marker.infoWindow.snippet ?? '',
                                    style: const TextStyle(
                                      fontSize: 10,
                                      color: AppTheme.textSecondary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Location: ${marker.position.latitude.toStringAsFixed(4)}, ${marker.position.longitude.toStringAsFixed(4)}',
                          style: const TextStyle(
                            fontSize: 9,
                            color: AppTheme.accentCyan,
                          ),
                        ),
                      ],
                    ),
                  ))
              .toList(),
        ),
      ),
    );
  }
}
