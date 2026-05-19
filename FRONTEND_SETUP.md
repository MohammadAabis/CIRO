# CIRO Frontend Setup Guide

## Prerequisites

- **Flutter SDK** (>=3.5.0): https://flutter.dev/docs/get-started/install
- **VS Code** or **Android Studio** IDE
- **Backend running** on `http://127.0.0.1:8000` (see backend README)

## Installation & Run

### 1. Install Dependencies

```bash
cd frontend
flutter pub get
```

### 2. Code Generation (Optional)

The project uses `build_runner` for generated files (Freezed models, JSON serialization, Riverpod):

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### 3. Run on Chrome (Web)

```bash
flutter run -d chrome
```

**Note:** If Chrome is not detected, enable web:

```bash
flutter config --enable-web
```

### 4. Run on Android Emulator

```bash
# Start emulator first
flutter emulators
flutter run -d <emulator-id>
```

### 5. Run on iOS Simulator (macOS only)

```bash
flutter run -d "iPhone 15"
```

## Project Structure

```
frontend/
├── lib/
│   ├── main.dart                  # Entry point (ProviderScope + CiroApp)
│   ├── app.dart                   # MaterialApp.router config
│   ├── core/
│   │   ├── network/
│   │   │   └── api_client.dart    # Dio-based API client (auto-fallback to mock)
│   │   ├── router/
│   │   │   └── app_router.dart    # GoRouter navigation
│   │   ├── theme/
│   │   │   └── app_theme.dart     # Material Dark theme
│   │   └── constants/
│   │       └── app_constants.dart # API URLs, timeouts, etc.
│   └── features/
│       ├── dashboard/             # Home screen (stats cards, resource map)
│       ├── crises/                # Crisis list & detail screens
│       ├── resources/             # Resource fleet map
│       └── simulations/           # Outcome details & side-effects
├── pubspec.yaml                   # Dependencies & assets
├── analysis_options.yaml          # Linting config
└── assets/
    ├── images/
    ├── icons/
    ├── animations/
    └── fonts/
```

## Key Technologies

| Layer         | Tech                       |
| ------------- | -------------------------- |
| State Mgmt    | Flutter Riverpod 2.6       |
| Networking    | Dio 5.7 + WebSockets       |
| Routing       | GoRouter 14.8              |
| Maps          | Google Maps Flutter        |
| Charts        | FL Chart 0.70              |
| Serialization | Freezed + JSON annotations |

## Configuration

### Backend URL

Edit `lib/core/network/api_client.dart` if backend is not on `127.0.0.1:8000`:

```dart
String baseUrl = 'http://YOUR_BACKEND_URL:8000';
```

## Features

### Dashboard

- Real-time crisis statistics (active crises, false alarms, resources)
- Animated charts showing resource deployment status
- SSE stream of live agent reasoning traces
- One-click signal ingestion form

### Crises

- Filterable list of active & resolved crises
- Severity-color-coded cards
- Detailed crisis view with evolutionary path predictions
- Resource allocation summary

### Resources

- Google Maps integration showing fleet positions
- Real-time resource status (available/deployed/en-route)
- Unit detail popups with call-sign and capacity

### Simulations

- Before/after crisis state comparison
- Side-effects list with severity indicators
- Public/hospital/utility alerts
- Recommendation display

## Troubleshooting

### "flutter command not found"

- Ensure Flutter SDK is in PATH
- Run: `flutter doctor`

### "Failed to connect to backend"

- Check backend is running on `http://127.0.0.1:8000`
- App auto-falls back to mock data if backend is unreachable

### "Build failed on code generation"

- Run: `flutter pub run build_runner build --delete-conflicting-outputs`
- Then: `flutter clean && flutter pub get`

### "Google Maps key not found"

- Add `GOOGLE_MAPS_API_KEY` to backend `.env`
- Frontend fetches from backend `/api/v1/config` endpoint

## Demo Flow (3-5 min)

1. **Start backend** with mock scenario data
2. **Run frontend** on Chrome: `flutter run -d chrome`
3. **Dashboard screen** loads with pre-seeded crises
4. **Tap on a crisis** to view details & resource allocation
5. **View map** showing deployed ambulances/police/rescue teams
6. **Ingest signal** via the form to trigger multi-agent pipeline
7. **Watch trace logs** stream live on the dashboard (SSE)
8. **Observe** new crisis created and resources re-allocated

---

**Built for Anti Gravity Hackathon 🚀**
