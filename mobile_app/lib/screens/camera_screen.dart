import "dart:io";

import "package:camera/camera.dart";
import "package:flutter/material.dart";

import "../api_client.dart";
import "../config.dart";
import "../models.dart";
import "../services/evidence_store.dart";
import "../theme.dart";
import "../widgets/detection_painter.dart";
import "../widgets/hazard_card.dart";
import "../widgets/hud.dart";

/// Main screen: live camera + capture/detect + result overlay + save evidence.
///
/// Styling follows the "Field Instrument HUD" blueprint
/// (mobile_app/design/hazard_detect_ui.html). The camera + inference logic is
/// unchanged from the original scaffold — only the presentation is restyled.
class CameraScreen extends StatefulWidget {
  final List<CameraDescription> cameras;
  const CameraScreen({super.key, required this.cameras});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  CameraController? _controller;
  bool _busy = false;
  String _status = "Initialising camera...";
  List<HazardResult> _results = [];
  File? _lastCapture;

  /// Set when the backend returns 503 (models not trained yet). Holds the list
  /// of missing weights so the not-ready overlay can show what to do.
  List<String>? _missing;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    if (widget.cameras.isEmpty) {
      setState(() => _status = "NO CAMERA AVAILABLE");
      return;
    }
    final c = CameraController(
      widget.cameras.first,
      ResolutionPreset.medium,
      enableAudio: false,
    );
    await c.initialize();
    if (!mounted) return;
    setState(() {
      _controller = c;
      _status = "READY · TAP DETECT TO SCAN";
    });
  }

  /// Capture one frame and run inference on it.
  Future<void> _detect() async {
    final c = _controller;
    if (c == null || !c.value.isInitialized || _busy) return;
    setState(() {
      _busy = true;
      _missing = null;
      _status = "RUNNING 4 MODELS + META-CLASSIFIER…";
    });
    try {
      final shot = await c.takePicture();
      final file = File(shot.path);
      final results = await ApiClient.infer(file, zone: AppConfig.defaultZone);
      if (!mounted) return;
      setState(() {
        _lastCapture = file;
        _results = results;
        _status = results.isEmpty
            ? "NO HAZARDS DETECTED"
            : "${results.length} HAZARD(S) DETECTED";
      });
    } on InferNotReady catch (e) {
      // Parse "missing weights: models/x.pt; missing weights: ..." into a list.
      final parts = e.message
          .split(";")
          .map((s) => s.replaceAll("missing weights:", "").trim())
          .where((s) => s.isNotEmpty)
          .toList();
      setState(() {
        _results = [];
        _missing = parts.isEmpty ? [e.message] : parts;
        _status = "/INFER UNAVAILABLE · 503";
      });
    } catch (e) {
      setState(() => _status = "ERROR: $e");
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _saveEvidence() async {
    if (_lastCapture == null || _results.isEmpty) return;
    final path = await EvidenceStore.save(_lastCapture!, _results);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      backgroundColor: Hud.panel2,
      content: Text("EVIDENCE SAVED · $path",
          style: Hud.mono(size: 11, color: Hud.teal)),
    ));
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool notReady = _missing != null;
    final Color dotColor = (notReady || _status.startsWith("ERROR"))
        ? Hud.sevMed
        : Hud.teal;

    return Scaffold(
      backgroundColor: Hud.bg,
      body: SafeArea(
        child: Column(
          children: [
            StatusRail(linked: !notReady, degraded: notReady),
            Expanded(child: _buildViewfinder(notReady)),
            if (_results.isNotEmpty)
              DetectionSheet(results: _results),
            StatusLine(text: _status, dotColor: dotColor),
            ActionBar(
              busy: _busy,
              canSave: _results.isNotEmpty && _lastCapture != null,
              disabled: notReady,
              onDetect: _detect,
              onSave: _saveEvidence,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildViewfinder(bool notReady) {
    final c = _controller;
    final bool camReady = c != null && c.value.isInitialized;
    final Color bracketColor = notReady ? Hud.sevMed : Hud.teal;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: Stack(
          fit: StackFit.expand,
          children: [
            // base layer: camera preview or dark instrument panel
            if (camReady)
              FittedBox(
                fit: BoxFit.cover,
                child: SizedBox(
                  width: c.value.previewSize?.height ?? 1,
                  height: c.value.previewSize?.width ?? 1,
                  child: CameraPreview(c),
                ),
              )
            else
              const ColoredBox(color: Hud.panel),

            // detection boxes
            if (_results.isNotEmpty && !_busy)
              CustomPaint(painter: DetectionPainter(_results)),

            // HUD frame
            CornerBrackets(color: bracketColor),

            // zone tag (only when camera is live and pipeline is healthy)
            if (camReady && !notReady)
              const Positioned(
                top: 14,
                left: 0,
                right: 0,
                child: Center(child: ZoneTag(zone: AppConfig.defaultZone)),
              ),

            // state overlays (priority: not-ready > detecting > idle)
            if (notReady)
              NotReadyOverlay(missing: _missing!)
            else if (_busy)
              const DetectingOverlay()
            else if (_results.isEmpty)
              camReady
                  ? const IdleReticle()
                  : Center(
                      child: Text(_status,
                          style: Hud.chrome(
                              size: 12, color: Hud.inkMute, spacing: 2)),
                    ),
          ],
        ),
      ),
    );
  }
}
