import "dart:math" as math;

import "package:flutter/material.dart";

import "../theme.dart";

/// Top status rail: brand mark + connection indicator.
class StatusRail extends StatelessWidget {
  final bool linked;
  final bool degraded;
  const StatusRail({super.key, this.linked = true, this.degraded = false});

  @override
  Widget build(BuildContext context) {
    final Color dotColor = degraded ? Hud.sevMed : Hud.teal;
    final String connText = degraded ? "DEGRADED" : (linked ? "LINKED" : "OFFLINE");
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 10),
      child: Row(
        children: [
          // crosshair brand mark
          SizedBox(
            width: 16,
            height: 16,
            child: CustomPaint(painter: _CrosshairMark()),
          ),
          const SizedBox(width: 9),
          Text("HAZARD DETECT",
              style: Hud.chrome(
                  size: 12, weight: FontWeight.w700, spacing: 2, color: Hud.ink)),
          const Spacer(),
          _PulseDot(color: dotColor),
          const SizedBox(width: 7),
          Text(connText,
              style: Hud.chrome(
                  size: 11, weight: FontWeight.w500, color: Hud.inkMute, spacing: 1.5)),
        ],
      ),
    );
  }
}

class _CrosshairMark extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()..color = Hud.teal;
    final w = size.width, h = size.height;
    // vertical bar + horizontal bar => plus/crosshair
    canvas.drawRect(Rect.fromLTWH(w * 0.38, 0, w * 0.24, h), p);
    canvas.drawRect(Rect.fromLTWH(0, h * 0.38, w, h * 0.24), p);
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}

/// A small pulsing status dot.
class _PulseDot extends StatefulWidget {
  final Color color;
  const _PulseDot({required this.color});
  @override
  State<_PulseDot> createState() => _PulseDotState();
}

class _PulseDotState extends State<_PulseDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(seconds: 2))
        ..repeat(reverse: true);

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: Tween(begin: 1.0, end: 0.35).animate(
          CurvedAnimation(parent: _c, curve: Curves.easeInOut)),
      child: Container(
        width: 7,
        height: 7,
        decoration: BoxDecoration(
          color: widget.color,
          shape: BoxShape.circle,
          boxShadow: [BoxShadow(color: widget.color, blurRadius: 8)],
        ),
      ),
    );
  }
}

/// Four corner brackets framing the viewfinder.
class CornerBrackets extends StatelessWidget {
  final Color color;
  const CornerBrackets({super.key, this.color = Hud.teal});

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Stack(
        children: [
          Positioned(top: 12, left: 12, child: _bracket(top: true, left: true)),
          Positioned(top: 12, right: 12, child: _bracket(top: true, left: false)),
          Positioned(bottom: 12, left: 12, child: _bracket(top: false, left: true)),
          Positioned(
              bottom: 12, right: 12, child: _bracket(top: false, left: false)),
        ],
      ),
    );
  }

  Widget _bracket({required bool top, required bool left}) {
    final side = BorderSide(color: color, width: 2);
    return Container(
      width: 26,
      height: 26,
      decoration: BoxDecoration(
        border: Border(
          top: top ? side : BorderSide.none,
          bottom: top ? BorderSide.none : side,
          left: left ? side : BorderSide.none,
          right: left ? BorderSide.none : side,
        ),
      ),
    );
  }
}

/// Centred zone tag at the top of the viewfinder.
class ZoneTag extends StatelessWidget {
  final String zone;
  const ZoneTag({super.key, required this.zone});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Hud.bg.withValues(alpha: 0.55),
        border: Border.all(color: Hud.line),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text("◎ ZONE · ${zone.toUpperCase().replaceAll('_', ' ')}",
          style: Hud.chrome(size: 10, color: Hud.teal, spacing: 2)),
    );
  }
}

/// Bottom status line with a leading dot.
class StatusLine extends StatelessWidget {
  final String text;
  final Color dotColor;
  const StatusLine({super.key, required this.text, this.dotColor = Hud.teal});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(9),
      decoration: const BoxDecoration(
        color: Hud.panel,
        border: Border(top: BorderSide(color: Hud.line)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle),
          ),
          const SizedBox(width: 8),
          Flexible(
            child: Text(text,
                textAlign: TextAlign.center,
                style: Hud.mono(size: 11, color: Hud.inkMute, spacing: 1)),
          ),
        ],
      ),
    );
  }
}

/// Idle overlay: dashed reticle ring + "Awaiting Scan".
class IdleReticle extends StatelessWidget {
  const IdleReticle({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 90,
            height: 90,
            child: CustomPaint(painter: _ReticlePainter()),
          ),
          const SizedBox(height: 18),
          Text("AWAITING SCAN",
              style: Hud.chrome(size: 12, color: Hud.inkMute, spacing: 3)),
        ],
      ),
    );
  }
}

class _ReticlePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final c = size.center(Offset.zero);
    final r = size.width / 2;
    final ring = Paint()
      ..color = Hud.teal.withValues(alpha: 0.85)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    // dashed circle
    const dashes = 28;
    for (int i = 0; i < dashes; i++) {
      if (i.isOdd) continue;
      final a0 = (i / dashes) * 2 * math.pi;
      final a1 = ((i + 1) / dashes) * 2 * math.pi;
      canvas.drawArc(Rect.fromCircle(center: c, radius: r), a0, a1 - a0, false, ring);
    }
    // crosshair lines
    final cross = Paint()
      ..color = Hud.teal.withValues(alpha: 0.4)
      ..strokeWidth = 1;
    canvas.drawLine(Offset(0, c.dy), Offset(size.width, c.dy), cross);
    canvas.drawLine(Offset(c.dx, 0), Offset(c.dx, size.height), cross);
    // centre dot
    canvas.drawCircle(c, 4, Paint()..color = Hud.teal);
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}

/// Detecting overlay: spinner + label over a dim scrim.
class DetectingOverlay extends StatelessWidget {
  const DetectingOverlay({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Hud.bg.withValues(alpha: 0.35),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 64,
              height: 64,
              child: CircularProgressIndicator(
                  strokeWidth: 2, color: Hud.teal, backgroundColor: Hud.line),
            ),
            const SizedBox(height: 16),
            Text("ANALYSING FRAME",
                style: Hud.chrome(size: 12, color: Hud.teal, spacing: 3)),
          ],
        ),
      ),
    );
  }
}

/// Models-not-ready overlay: warning icon + missing-weights list.
class NotReadyOverlay extends StatelessWidget {
  final List<String> missing;
  const NotReadyOverlay({super.key, this.missing = const []});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(30),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 54,
              height: 54,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: Hud.sevMed, width: 2),
              ),
              child: Text("!",
                  style: Hud.chrome(
                      size: 28, weight: FontWeight.w700, color: Hud.sevMed)),
            ),
            const SizedBox(height: 14),
            Text("MODELS NOT READY",
                style: Hud.chrome(size: 13, color: Hud.ink, spacing: 2)),
            const SizedBox(height: 10),
            Text(
                "The detection pipeline is reachable but not all weights are loaded.",
                textAlign: TextAlign.center,
                style: Hud.mono(size: 11, color: Hud.inkMute, height: 1.6)),
            if (missing.isNotEmpty) ...[
              const SizedBox(height: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: missing
                    .map((m) => Text("▸ $m",
                        style: Hud.mono(size: 10, color: Hud.sevMed, height: 1.7)))
                    .toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Bottom action bar: primary Detect + ghost Save.
class ActionBar extends StatelessWidget {
  final bool busy;
  final bool canSave;
  final bool disabled;
  final VoidCallback? onDetect;
  final VoidCallback? onSave;
  const ActionBar({
    super.key,
    required this.busy,
    required this.canSave,
    this.disabled = false,
    this.onDetect,
    this.onSave,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
      decoration: const BoxDecoration(
        color: Hud.panel,
        border: Border(top: BorderSide(color: Hud.line)),
      ),
      child: Row(
        children: [
          Expanded(
            flex: 16,
            child: _primary(),
          ),
          const SizedBox(width: 10),
          Expanded(
            flex: 10,
            child: _ghost(),
          ),
        ],
      ),
    );
  }

  Widget _primary() {
    final bool enabled = !busy && !disabled && onDetect != null;
    return SizedBox(
      height: 54,
      child: ElevatedButton(
        onPressed: enabled ? onDetect : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: disabled ? Hud.inkFaint : Hud.teal,
          disabledBackgroundColor: disabled ? Hud.inkFaint : Hud.teal.withValues(alpha: 0.55),
          foregroundColor: const Color(0xFF06100E),
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (busy)
              const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(
                    strokeWidth: 2, color: Color(0xFF06100E)),
              )
            else
              const Icon(Icons.search, size: 18),
            const SizedBox(width: 9),
            Text(busy ? "WORKING" : "DETECT",
                style: Hud.chrome(
                    size: 13,
                    weight: FontWeight.w700,
                    spacing: 2,
                    color: const Color(0xFF06100E))),
          ],
        ),
      ),
    );
  }

  Widget _ghost() {
    final bool enabled = canSave && onSave != null;
    return SizedBox(
      height: 54,
      child: OutlinedButton(
        onPressed: enabled ? onSave : null,
        style: OutlinedButton.styleFrom(
          foregroundColor: Hud.ink,
          disabledForegroundColor: Hud.inkFaint,
          side: const BorderSide(color: Hud.line),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.save_outlined,
                size: 18, color: enabled ? Hud.ink : Hud.inkFaint),
            const SizedBox(width: 8),
            Text("SAVE",
                style: Hud.chrome(
                    size: 13,
                    weight: FontWeight.w700,
                    spacing: 2,
                    color: enabled ? Hud.ink : Hud.inkFaint)),
          ],
        ),
      ),
    );
  }
}
