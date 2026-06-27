/// App configuration.
///
/// Set [backendBaseUrl] to where the Flask backend (backend/app.py) is running.
/// - Android emulator: use 10.0.2.2 (host loopback), e.g. http://10.0.2.2:5000
/// - iOS simulator:    http://127.0.0.1:5000
/// - Physical phone:   http://<your-computer-LAN-IP>:5000  (same Wi-Fi)
class AppConfig {
  static const String backendBaseUrl = "http://192.168.1.5:5000";

  /// How often to auto-capture a frame for inference, in milliseconds.
  static const int autoDetectIntervalMs = 1500;

  /// Declared zone reported to the backend (affects contextual features).
  static const String defaultZone = "bus_stop";
}
