# Mobile App (Flutter) — plan & structure

Owner: **M3**. Not yet scaffolded with `flutter create` (do that on a machine
with the Flutter SDK installed). This README defines the target structure and
how it connects to the ML pipeline.

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
