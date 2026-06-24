import "dart:io";

import "package:camera/camera.dart";
import "package:flutter/material.dart";

import "../api_client.dart";
import "../config.dart";
import "../models.dart";
import "../services/evidence_store.dart";
import "../widgets/detection_painter.dart";

/// Main screen: live camera + capture/detect + result overlay + save evidence.
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

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    if (widget.cameras.isEmpty) {
      setState(() => _status = "No camera available");
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
      _status = "Ready. Tap Detect.";
    });
  }

  /// Capture one frame and run inference on it.
  Future<void> _detect() async {
    final c = _controller;
    if (c == null || !c.value.isInitialized || _busy) return;
    setState(() {
      _busy = true;
      _status = "Detecting...";
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
            ? "No hazards detected."
            : "${results.length} hazard(s) detected.";
      });
    } on InferNotReady catch (e) {
      setState(() => _status = "Models not ready: $e");
    } catch (e) {
      setState(() => _status = "Error: $e");
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _saveEvidence() async {
    if (_lastCapture == null || _results.isEmpty) return;
    final path = await EvidenceStore.save(_lastCapture!, _results);
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text("Evidence saved: $path")));
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final c = _controller;
    return Scaffold(
      appBar: AppBar(title: const Text("Campus Hazard Detection")),
      body: Column(
        children: [
          Expanded(
            child: (c != null && c.value.isInitialized)
                ? Stack(
                    fit: StackFit.expand,
                    children: [
                      CameraPreview(c),
                      CustomPaint(painter: DetectionPainter(_results)),
                    ],
                  )
                : Center(child: Text(_status)),
          ),
          if (_results.isNotEmpty) _buildResultList(),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Text(_status, textAlign: TextAlign.center),
          ),
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: _busy ? null : _detect,
                  icon: const Icon(Icons.search),
                  label: const Text("Detect"),
                ),
                ElevatedButton.icon(
                  onPressed: _results.isEmpty ? null : _saveEvidence,
                  icon: const Icon(Icons.save),
                  label: const Text("Save evidence"),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultList() {
    return ConstrainedBox(
      constraints: const BoxConstraints(maxHeight: 160),
      child: ListView(
        children: _results
            .map((r) => ListTile(
                  dense: true,
                  leading: Icon(Icons.warning,
                      color: r.severity == "high"
                          ? Colors.red
                          : r.severity == "medium"
                              ? Colors.orange
                              : Colors.amber),
                  title: Text("${r.hazardClass}  "
                      "(${(r.confidence * 100).toStringAsFixed(0)}%, "
                      "${r.severity})"),
                  subtitle: Text(r.recommendedAction),
                ))
            .toList(),
      ),
    );
  }
}
