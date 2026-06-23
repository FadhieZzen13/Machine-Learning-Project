/// Data model for a single final hazard result returned by the backend /infer.
///
/// Mirrors the JSON produced by backend/pipeline.py -> HazardPipeline.infer().
class HazardResult {
  final String hazardClass;
  final String? generalCategory;
  final double confidence;
  final String severity;

  /// Normalised [cx, cy, w, h] in 0..1 (centre format), as YOLO emits.
  final List<double> boxXywhn;
  final int numModelsAgree;
  final String recommendedAction;

  HazardResult({
    required this.hazardClass,
    required this.generalCategory,
    required this.confidence,
    required this.severity,
    required this.boxXywhn,
    required this.numModelsAgree,
    required this.recommendedAction,
  });

  factory HazardResult.fromJson(Map<String, dynamic> j) {
    return HazardResult(
      hazardClass: j["hazard_class"] as String,
      generalCategory: j["general_category"] as String?,
      confidence: (j["confidence"] as num).toDouble(),
      severity: j["severity"] as String? ?? "medium",
      boxXywhn: (j["box_xywhn"] as List).map((e) => (e as num).toDouble()).toList(),
      numModelsAgree: (j["num_models_agree"] as num?)?.toInt() ?? 1,
      recommendedAction: j["recommended_action"] as String? ?? "",
    );
  }
}
