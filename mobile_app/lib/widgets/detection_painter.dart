import "package:flutter/material.dart";

import "../models.dart";

/// Draws bounding boxes + labels over the camera preview.
///
/// Boxes are in normalised xywh (centre format, 0..1) so they scale to any
/// preview size. Colour encodes severity.
class DetectionPainter extends CustomPainter {
  final List<HazardResult> results;
  DetectionPainter(this.results);

  Color _severityColor(String severity) {
    switch (severity) {
      case "high":
        return Colors.redAccent;
      case "medium":
        return Colors.orangeAccent;
      default:
        return Colors.yellowAccent;
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    for (final r in results) {
      if (r.boxXywhn.length != 4) continue;
      final cx = r.boxXywhn[0] * size.width;
      final cy = r.boxXywhn[1] * size.height;
      final w = r.boxXywhn[2] * size.width;
      final h = r.boxXywhn[3] * size.height;
      final rect = Rect.fromCenter(center: Offset(cx, cy), width: w, height: h);

      final color = _severityColor(r.severity);
      final boxPaint = Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3;
      canvas.drawRect(rect, boxPaint);

      // label: class + confidence + agreement
      final label = "${r.hazardClass} "
          "${(r.confidence * 100).toStringAsFixed(0)}% "
          "(${r.numModelsAgree}x)";
      final tp = TextPainter(
        text: TextSpan(
          text: label,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 13,
            fontWeight: FontWeight.bold,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();

      final labelBg = Rect.fromLTWH(
          rect.left, rect.top - 20, tp.width + 8, 20);
      canvas.drawRect(labelBg, Paint()..color = color);
      tp.paint(canvas, Offset(rect.left + 4, rect.top - 19));
    }
  }

  @override
  bool shouldRepaint(covariant DetectionPainter old) =>
      old.results != results;
}
