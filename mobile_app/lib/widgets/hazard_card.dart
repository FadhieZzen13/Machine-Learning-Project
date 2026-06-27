import "package:flutter/material.dart";

import "../models.dart";
import "../theme.dart";

/// Bottom sheet listing the fused hazard detections.
class DetectionSheet extends StatelessWidget {
  final List<HazardResult> results;
  final int totalModels;
  const DetectionSheet({super.key, required this.results, this.totalModels = 4});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Hud.panel2,
        border: Border(top: BorderSide(color: Hud.line)),
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: const EdgeInsets.fromLTRB(14, 10, 14, 6),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // grip
          Container(
            width: 42,
            height: 4,
            margin: const EdgeInsets.only(bottom: 12),
            decoration: BoxDecoration(
                color: Hud.line, borderRadius: BorderRadius.circular(2)),
          ),
          // header
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 2),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text("DETECTIONS ",
                    style: Hud.chrome(size: 12, spacing: 2, color: Hud.ink)),
                Text(results.length.toString().padLeft(2, "0"),
                    style: Hud.chrome(size: 12, spacing: 2, color: Hud.teal)),
                const Spacer(),
                Text("FUSED · $totalModels MODELS",
                    style: Hud.mono(size: 10, color: Hud.inkMute, spacing: 1)),
              ],
            ),
          ),
          const SizedBox(height: 10),
          // list (capped + scrollable so it never overflows the column)
          ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 280),
            child: ListView.separated(
              shrinkWrap: true,
              padding: EdgeInsets.zero,
              itemCount: results.length,
              separatorBuilder: (_, __) => const SizedBox(height: 9),
              itemBuilder: (_, i) =>
                  HazardCard(result: results[i], totalModels: totalModels),
            ),
          ),
        ],
      ),
    );
  }
}

/// One hazard row: severity stripe, name + badge, metrics, advisory.
class HazardCard extends StatelessWidget {
  final HazardResult result;
  final int totalModels;
  const HazardCard({super.key, required this.result, this.totalModels = 4});

  @override
  Widget build(BuildContext context) {
    final Color c = Hud.severityColor(result.severity);
    return Container(
      decoration: BoxDecoration(
        color: Hud.panel2,
        border: Border(
          top: const BorderSide(color: Hud.line),
          right: const BorderSide(color: Hud.line),
          bottom: const BorderSide(color: Hud.line),
          left: BorderSide(color: c, width: 3),
        ),
        borderRadius: BorderRadius.circular(10),
      ),
      padding: const EdgeInsets.fromLTRB(12, 11, 12, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // top: name + severity badge
          Row(
            children: [
              Expanded(
                child: Text(_titleCase(result.hazardClass),
                    style: Hud.chrome(
                        size: 14, weight: FontWeight.w600, color: Hud.ink, spacing: 0.5)),
              ),
              _SeverityBadge(severity: result.severity, color: c),
            ],
          ),
          const SizedBox(height: 9),
          // metrics: confidence bar + % + agreement pips
          Row(
            children: [
              Expanded(child: _ConfidenceBar(value: result.confidence, color: c)),
              const SizedBox(width: 14),
              _AgreementPips(
                  filled: result.numModelsAgree, total: totalModels, color: c),
            ],
          ),
          // advisory (only when present)
          if (result.recommendedAction.trim().isNotEmpty) ...[
            const SizedBox(height: 10),
            const _DashedDivider(),
            const SizedBox(height: 10),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.only(top: 1),
                  child: Text("◇ ADVISORY",
                      style: Hud.chrome(size: 9, color: Hud.teal, spacing: 1)),
                ),
                const SizedBox(width: 7),
                Expanded(
                  child: Text(result.recommendedAction,
                      style: Hud.mono(size: 11, color: Hud.ink, height: 1.45)),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  // hazard_class names come as snake_case (e.g. "uncovered_manhole").
  static String _titleCase(String raw) {
    return raw
        .replaceAll("_", " ")
        .split(" ")
        .where((w) => w.isNotEmpty)
        .map((w) => w[0].toUpperCase() + w.substring(1))
        .join(" ");
  }
}

class _SeverityBadge extends StatelessWidget {
  final String severity;
  final Color color;
  const _SeverityBadge({required this.severity, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        border: Border.all(color: color.withValues(alpha: 0.40)),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(severity.toUpperCase(),
          style: Hud.chrome(size: 9, weight: FontWeight.w700, color: color, spacing: 1)),
    );
  }
}

class _ConfidenceBar extends StatelessWidget {
  final double value; // 0..1
  final Color color;
  const _ConfidenceBar({required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    final pct = (value.clamp(0.0, 1.0) * 100).round();
    return Row(
      children: [
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(2),
            child: LinearProgressIndicator(
              value: value.clamp(0.0, 1.0),
              minHeight: 4,
              backgroundColor: Hud.line,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ),
        const SizedBox(width: 7),
        Text("$pct%",
            style: Hud.mono(size: 11, weight: FontWeight.w600, color: Hud.ink)),
      ],
    );
  }
}

class _AgreementPips extends StatelessWidget {
  final int filled;
  final int total;
  final Color color;
  const _AgreementPips(
      {required this.filled, required this.total, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(total, (i) {
        final on = i < filled;
        return Padding(
          padding: const EdgeInsets.only(left: 3),
          child: Transform.rotate(
            angle: 0.785398, // 45°
            child: Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: on ? color : Colors.transparent,
                border: Border.all(color: color),
              ),
            ),
          ),
        );
      }),
    );
  }
}

class _DashedDivider extends StatelessWidget {
  const _DashedDivider();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 1,
      child: CustomPaint(painter: _DashedLinePainter(), size: Size.infinite),
    );
  }
}

class _DashedLinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Hud.line
      ..strokeWidth = 1;
    const dash = 4.0, gap = 4.0;
    double x = 0;
    while (x < size.width) {
      canvas.drawLine(Offset(x, 0), Offset(x + dash, 0), paint);
      x += dash + gap;
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}
