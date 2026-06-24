"""
Flask backend for the Campus Hazard Detection mobile app.

Endpoints:
  GET  /health      -> liveness + pipeline readiness (what's still missing)
  POST /recommend   -> hazard dict -> LLM/offline recommended action  (works NOW)
  POST /infer       -> uploaded image -> final hazard results          (needs models)

The mobile app calls /infer with a camera frame and draws the returned boxes,
labels, severity, and recommended actions. /recommend is usable immediately for
app development before the YOLO/meta models are trained.

Run:
  pip install flask
  python backend/app.py            # http://127.0.0.1:5000
"""
from __future__ import annotations

import os
import tempfile

from flask import Flask, jsonify, request

from pipeline import HazardPipeline

app = Flask(__name__)
pipeline = HazardPipeline()


@app.get("/health")
def health():
    st = pipeline.status()
    return jsonify({
        "status": "ok",
        "pipeline_ready": st.fully_ready,
        "torch": st.torch_available,
        "ultralytics": st.ultralytics_available,
        "yolo_weights": st.yolo_ready,
        "meta_weights": st.meta_ready,
        "missing": st.missing(),
    })


@app.post("/recommend")
def recommend_endpoint():
    """Body: {hazard_class, general_category, zone, severity, confidence}."""
    from recommend_action import recommend  # reuse the LLM module
    hazard = request.get_json(force=True, silent=True) or {}
    if "hazard_class" not in hazard:
        return jsonify({"error": "hazard_class is required"}), 400
    return jsonify({"recommended_action": recommend(hazard)})


@app.post("/infer")
def infer_endpoint():
    """Multipart form: file=<image>, optional zone=<str>."""
    if "file" not in request.files:
        return jsonify({"error": "multipart 'file' (image) is required"}), 400
    zone = request.form.get("zone", "unknown")

    f = request.files["file"]
    suffix = os.path.splitext(f.filename or "frame.jpg")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        f.save(tmp.name)
        path = tmp.name
    try:
        results = pipeline.infer(path, zone_context=zone)
        return jsonify({"results": results})
    except RuntimeError as e:
        # models not trained yet -> 503 with a clear "what to do" message
        return jsonify({"error": str(e)}), 503
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
