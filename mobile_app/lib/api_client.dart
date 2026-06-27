import "dart:convert";
import "dart:io";

import "package:http/http.dart" as http;

import "config.dart";
import "models.dart";

/// Thin client for the Flask backend.
class ApiClient {
  /// True if the backend is reachable and its pipeline is fully ready.
  static Future<Map<String, dynamic>> health() async {
    final r = await http
        .get(Uri.parse("${AppConfig.backendBaseUrl}/health"))
        .timeout(const Duration(seconds: 5));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// Send a captured image file to /infer and parse the hazard results.
  ///
  /// Throws [InferNotReady] (HTTP 503) when the models are not trained yet, so
  /// the UI can show a helpful message instead of a generic error.
  static Future<List<HazardResult>> infer(File image,
      {String zone = AppConfig.defaultZone}) async {
    final uri = Uri.parse("${AppConfig.backendBaseUrl}/infer");
    final req = http.MultipartRequest("POST", uri)
      ..fields["zone"] = zone
      ..files.add(await http.MultipartFile.fromPath("file", image.path));

    final streamed = await req.send().timeout(const Duration(seconds: 45));
    final resp = await http.Response.fromStream(streamed);

    if (resp.statusCode == 503) {
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      throw InferNotReady(body["error"] as String? ?? "Pipeline not ready");
    }
    if (resp.statusCode != 200) {
      throw Exception("Inference failed (${resp.statusCode}): ${resp.body}");
    }

    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    final list = (body["results"] as List).cast<Map<String, dynamic>>();
    return list.map(HazardResult.fromJson).toList();
  }
}

/// Raised when the backend pipeline is reachable but models aren't trained yet.
class InferNotReady implements Exception {
  final String message;
  InferNotReady(this.message);
  @override
  String toString() => message;
}
