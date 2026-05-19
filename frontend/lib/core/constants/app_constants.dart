/// Application-wide constants.
class AppConstants {
  AppConstants._();

  static const String appName = 'CIRO';
  static const String appVersion = '0.1.0';

  // API
  static const String apiBaseUrl = 'http://localhost:8000/api/v1';
  static const String wsBaseUrl = 'ws://localhost:8000/ws';

  // Map defaults (Islamabad centre)
  static const double defaultLatitude = 33.6844;
  static const double defaultLongitude = 73.0479;
  static const double defaultZoom = 12.0;
}
