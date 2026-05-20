import 'package:flutter/material.dart';
import 'package:ciro_app/features/dashboard/presentation/widgets/real_map_widget.dart';

/// IncidentMap: Crisis location visualization widget
/// Delegates to RealMapWidget for Google Maps integration
class IncidentMap extends StatelessWidget {
  final List<dynamic> crises;
  
  const IncidentMap({super.key, required this.crises});

  @override
  Widget build(BuildContext context) {
    return RealMapWidget(crises: crises);
  }
}
