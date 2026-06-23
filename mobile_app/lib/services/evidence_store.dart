import "dart:convert";
import "dart:io";

import "package:intl/intl.dart";
import "package:path_provider/path_provider.dart";

import "../models.dart";

/// Saves detection evidence (assignment §10: "Save screenshot, timestamp and
/// detection record"). Stores the captured image plus a JSON record appended to
/// a local log file under the app documents directory.
class EvidenceStore {
  static Future<Directory> _evidenceDir() async {
    final base = await getApplicationDocumentsDirectory();
    final dir = Directory("${base.path}/evidence");
    if (!await dir.exists()) await dir.create(recursive: true);
    return dir;
  }

  /// Persist one detection event. Returns the saved image path.
  static Future<String> save(File capturedImage, List<HazardResult> results,
      {String zone = "bus_stop"}) async {
    final dir = await _evidenceDir();
    final ts = DateTime.now();
    final stamp = DateFormat("yyyyMMdd_HHmmss").format(ts);

    // copy the screenshot
    final imgPath = "${dir.path}/hazard_$stamp.jpg";
    await capturedImage.copy(imgPath);

    // append a JSON record
    final record = {
      "timestamp": ts.toIso8601String(),
      "zone": zone,
      "image": imgPath,
      "results": results
          .map((r) => {
                "hazard_class": r.hazardClass,
                "severity": r.severity,
                "confidence": r.confidence,
                "models_agree": r.numModelsAgree,
                "action": r.recommendedAction,
              })
          .toList(),
    };
    final log = File("${dir.path}/evidence_log.jsonl");
    await log.writeAsString("${jsonEncode(record)}\n",
        mode: FileMode.append, flush: true);
    return imgPath;
  }
}
