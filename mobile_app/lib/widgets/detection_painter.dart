import "package:flutter/material.dart";

import "../models.dart";
import "../theme.dart";

/// Draws instrument-style detection boxes over the camera preview.
///
/// Boxes are in normalised xywh (centre format, 0..1) so they scale to any
/// preview size. Each box gets a thin severity-coloured border, four corner
/// brackets, and a label chip with class + confidence. Colour encodes severity.
class DetectionPainter extends CustomPainter {
  final List<HazardResult> results;
  DetectionPainter(this.results);

  @override
  void paint(Canvas canvas, Size size) {
    for (final r in results) {
      if (r.boxXywhn.length != 4) continue;
      final cx = r.boxXywhn[0] * size.width;
      final cy = r.boxXywhn[1] * size.height;
      final w = r.boxXywhn[2] * size.width;
      final h = r.boxXywhn[3] * size.height;
      final rect = Rect.fromCenter(center: Offset(cx, cy), width: w, height: h);
      final color = Hud.severityColor(r.severity);

      // faint full border
      canvas.drawRect(
        rect,
        Paint()
          ..color = color.withValues(alpha: 0.55)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.5,
      );

      // solid corner brackets
      _drawBrackets(canvas, rect, color);

      // label chip: CLASS · NN%
      _drawLabel(canvas, rect, color, r);
    }
  }

  void _drawBrackets(Canvas canvas, Rect rect, Color color) {
    const len = 11.0;
    final p = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    // top-left
    canvas.drawLine(rect.topLeft, rect.topLeft + const Offset(len, 0), p);
    canvas.drawLine(rect.topLeft, rect.topLeft + const Offset(0, len), p);
    // top-right
    canvas.drawLine(rect.topRight, rect.topRight - const Offset(len, 0), p);
    canvas.drawLine(rect.topRight, rect.topRight + const Offset(0, len), p);
    // bottom-left
    canvas.drawLine(rect.bottomLeft, rect.bottomLeft + const Offset(len, 0), p);
    canvas.drawLine(rect.bottomLeft, rect.bottomLeft - const Offset(0, len), p);
    // bottom-right
    canvas.drawLine(rect.bottomRight, rect.bottomRight - const Offset(len, 0), p);
    canvas.drawLine(rect.bottomRight, rect.bottomRight - const Offset(0, len), p);
  }

  void _drawLabel(Canvas canvas, Rect rect, Color color, HazardResult r) {
    final label = "${r.hazardClass.replaceAll('_', ' ').toUpperCase()} · "
        "${(r.confidence * 100).round()}%";
    final tp = TextPainter(
      text: TextSpan(
        text: label,
        style: Hud.chrome(
            size: 10,
            weight: FontWeight.w700,
            color: const Color(0xFF070B0C),
            spacing: 1),
      ),
      textDirection: TextDirection.ltr,
    )..layout();

    final chip = Rect.fromLTWH(
        rect.left - 1, rect.top - tp.height - 6, tp.width + 12, tp.height + 6);
    canvas.drawRect(chip, Paint()..color = color);
    tp.paint(canvas, Offset(chip.left + 6, chip.top + 3));
  }

  @override
  bool shouldRepaint(covariant DetectionPainter old) => old.results != results;
}
