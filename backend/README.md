# Backend Inference Service

Flask service that runs the full pipeline (3 YOLO models → label harmonisation →
IoU grouping → meta-classifier → severity → LLM action) and serves it to the
mobile app. Reuses the modules in `../ml/` directly — no duplicated inference code.

## Run
```bash
pip install -r ../requirements.txt        # flask is included
python app.py                              # http://0.0.0.0:5000
```

## Endpoints
| Method | Path | Body | Status |
|--------|------|------|--------|
| GET | `/health` | – | ✅ works now — reports what's still missing |
| POST | `/recommend` | `{hazard_class, general_category, zone, severity, confidence}` | ✅ works now (LLM/offline) |
| POST | `/infer` | multipart `file=<image>`, `zone=<str>` | ⏳ returns 503 until models are trained |

`/infer` becomes live once these exist (the service detects them automatically):
- `../models/member1.pt`, `member2.pt`, `member3.pt` (trained YOLO weights)
- `../models/meta_classifier.pt` (trained meta-classifier)
- `pip install torch ultralytics`

## Verified
`/health` and `/recommend` were tested via Flask's test client and return
correct responses; `/infer` correctly reports 503 with the list of missing
prerequisites until the models are trained.

## LLM
Set `GEMINI_API_KEY` in the environment to use Gemini for recommendations;
otherwise the offline fallback in `../ml/llm/recommend_action.py` is used.
