/// Application-wide constants.
class AppConstants {
  AppConstants._();

  static const String appName = 'CIRO';
  static const String appVersion = '0.1.0';

  // API
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    // defaultValue: 'http://10.0.2.2:8000/api/v1',
    defaultValue: 'https://ciro-7wzz.onrender.com/api/v1',
  );
  static const String wsBaseUrl = String.fromEnvironment(
    'WS_BASE_URL',
    // defaultValue: 'ws://10.0.2.2:8000/ws',
    defaultValue: 'wss://ciro-7wzz.onrender.com/ws',
  );

  // Map defaults (Islamabad centre)
  static const double defaultLatitude = 33.6844;
  static const double defaultLongitude = 73.0479;
  static const double defaultZoom = 12.0;

  // Google Maps API Key - Replace with your key from https://console.cloud.google.com
  // Get key: https://developers.google.com/maps/documentation/android-sdk/get-api-key
  static const String googleMapsApiKey = 'AIzaSyB3Yjt4vr-b-6ZCmJiDP0fZl2Co8BmRPLQ';
}
