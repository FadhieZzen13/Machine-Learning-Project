# Mobile App (Flutter)

Owner: **M3**. The **Dart source is scaffolded** in `lib/` (backend approach).
The platform folders (`android/`, `ios/`) are NOT generated yet — see "Run it"
below. This README documents the structure and how it connects to the pipeline.

## What's already here (`lib/`)
| File | Purpose |
|------|---------|
| `main.dart` | App entry; gets cameras, launches the screen |
| `config.dart` | **Backend URL** + zone + auto-detect interval (edit this first) |
| `models.dart` | `HazardResult` — parses the backend /infer JSON |
| `api_client.dart` | Calls backend `/infer` (multipart image) and `/health` |
| `screens/camera_screen.dart` | Live preview, Detect button, result list, Save evidence |
| `widgets/detection_painter.dart` | Draws boxes + labels, colour by severity |
| `services/evidence_store.dart` | Saves screenshot + timestamp + JSON record |

The app talks to the **Flask backend** in `../backend/` (which runs the YOLO
models + meta-classifier + LLM). This reuses all the Python code instead of
re-implementing inference in Dart.

## Run it
The lib/ code is ready, but Flutter needs the platform scaffolding generated:
```bash
# 1) install Flutter SDK (https://docs.flutter.dev/get-started/install)
# 2) from mobile_app/, generate android/ios projects INTO this folder:
flutter create .
flutter pub get
# 3) start the backend on your computer (same Wi-Fi as the phone):
#    cd ../backend && python app.py
# 4) set AppConfig.backendBaseUrl in lib/config.dart to your machine's IP
#    (Android emulator: http://10.0.2.2:5000)
flutter run
```
Add **camera permission**: `android/app/src/main/AndroidManifest.xml`
(`<uses-permission android:name="android.permission.CAMERA"/>`) and iOS
`NSCameraUsageDescription` in `ios/Runner/Info.plist`. (`flutter create` plus the
`camera` plugin docs cover the exact lines.)

> Current behaviour: tap **Detect** to capture a frame → backend infers → boxes
> + actions overlay. Continuous live streaming (auto-detect loop) is a planned
> enhancement; capture-on-tap is enough for the demo and is simpler/robust.

## Required features (assignment §10)
- Real-time inference from the **device camera** (live frames).
- Run the three YOLO models — **on-device** (TFLite/ONNX) or via a **backend**
  inference service the app calls. Decide as a group (see project_plan §7.3).
- Show the **meta-classifier final result**, not just raw YOLO outputs.
- Draw bounding box + final label + confidence + **severity**.
- Fetch **LLM recommended action** (Gemini API or local) — mirror the logic in
  `../ml/llm/recommend_action.py` (port to Dart, or call a backend that runs it).
- **Evidence capture**: save screenshot + timestamp + detection record.

## Suggested architecture
```
camera frame
  → inference (tflite_flutter on-device  OR  POST to backend /infer)
  → harmonise + IoU group + features  (same logic as feature_extraction.py)
  → meta-classifier (tflite on-device OR backend)
  → severity lookup (config/classes.yaml severity map)
  → LLM action (backend /recommend  OR  Gemini SDK)
  → overlay painter draws boxes + labels + action
  → "Save evidence" → local DB (sqflite) + image file
```

## Recommended packages
`camera`, `tflite_flutter` (on-device) or `http`/`dio` (backend), `sqflite`
(evidence log), `path_provider`, `image`.

## Decision: on-device vs backend
- **On-device**: export each YOLO `best.pt` → TFLite; export meta-classifier →
  TFLite. Lower latency, works offline, but more conversion work and the LLM
  still needs network.
- **Backend**: a small FastAPI/Flask service runs the YOLO models +
  `feature_extraction.py` + `model.py` + `recommend_action.py` and returns the
  final result. Easiest path to reuse the Python code as-is; needs connectivity.

Recommended for the demo: **backend** (reuses the existing Python modules
directly), unless offline operation is a grading emphasis.
