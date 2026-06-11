"""
LLM-based recommended maintenance action.

Given a final (meta-classifier) hazard result, ask an LLM for a short, practical,
safety-oriented maintenance recommendation. Supports the Gemini API; falls back
to a deterministic offline lookup so the pipeline is usable without a network /
API key (and so the mobile app demo never hard-fails).

Usage:
    from recommend_action import recommend
    rec = recommend({
        "hazard_class": "uncovered_manhole",
        "general_category": "hole_in_ground",
        "zone": "bus_stop",
        "severity": "high",
        "confidence": 0.91,
    })

Set GEMINI_API_KEY in the environment to use the live LLM. The mobile app should
call an equivalent endpoint (or this logic ported to Dart / a backend service).
"""
from __future__ import annotations

import json
import os
from typing import Optional

# Offline fallback recommendations keyed by global hazard class.
_FALLBACK = {
    "pothole": "Mark and cordon the pothole, warn pedestrians, and report to Facilities for resurfacing.",
    "uncovered_manhole": "Place a temporary barricade immediately, prevent access, and report to Facilities for urgent cover replacement.",
    "open_drain": "Barricade the open drain, add warning signage, and request immediate covering by Maintenance.",
    "cracked_pavement": "Log the cracked pavement for scheduled repair; monitor for trip-hazard widening.",
    "obstacle_on_walkway": "Remove or relocate the obstacle if safe; otherwise barricade and report for clearance.",
    "dangling_wire": "Do NOT touch. Cordon the area, treat as live, and report to Electrical Maintenance urgently.",
    "broken_bench": "Tape off the broken bench to prevent use and raise a repair/replacement request.",
    "broken_shelter_panel": "Cordon beneath the damaged panel to prevent falling-debris injury and report for repair.",
    "exposed_socket": "Treat as live; restrict access and report to Electrical Maintenance for isolation and repair.",
    "fallen_branch": "Clear the branch if light and safe; for large branches, cordon and call Grounds Maintenance.",
    "missing_barricade": "Restore a temporary barricade to secure the boundary and report the missing barrier.",
}

_PROMPT_TEMPLATE = (
    "You are a campus facilities safety assistant. Given a detected hazard, "
    "reply with ONE concise, practical, safety-oriented maintenance action "
    "(max 2 sentences). Do not add preamble.\n\n"
    "Hazard class: {hazard_class}\n"
    "General category: {general_category}\n"
    "Location zone: {zone}\n"
    "Severity: {severity}\n"
    "Confidence: {confidence}\n\n"
    "Recommended action:"
)


def _format_prompt(hazard: dict) -> str:
    return _PROMPT_TEMPLATE.format(
        hazard_class=hazard.get("hazard_class", "unknown"),
        general_category=hazard.get("general_category", "n/a"),
        zone=hazard.get("zone", "unknown"),
        severity=hazard.get("severity", "medium"),
        confidence=hazard.get("confidence", "n/a"),
    )


def _gemini(prompt: str, api_key: str, model: str = "gemini-1.5-flash") -> Optional[str]:
    """Call Gemini via REST. Returns text or None on any failure."""
    try:
        import urllib.request

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:  # network, quota, parse - fall back gracefully
        print(f"[recommend_action] Gemini call failed, using fallback: {e}")
        return None


def recommend(hazard: dict) -> str:
    """Return a recommended maintenance action for a hazard result dict."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        text = _gemini(_format_prompt(hazard), api_key)
        if text:
            return text
    return _FALLBACK.get(
        hazard.get("hazard_class", ""),
        "Cordon the area, warn nearby people, and report to Facilities Maintenance.",
    )


if __name__ == "__main__":
    demo = {
        "hazard_class": "uncovered_manhole",
        "general_category": "hole_in_ground",
        "zone": "bus_stop",
        "severity": "high",
        "confidence": 0.91,
    }
    print(recommend(demo))
