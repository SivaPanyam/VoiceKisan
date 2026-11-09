"""
Conversational State & Memory Manager.
Maintains session history per user/device so VoiceKisan can ask clarifying questions,
remember previously discussed crops, land size, and past schemes, and guide the farmer naturally.
"""

from typing import Dict, Any, List
import time

# In-memory session store (keyed by session_id / client_ip)
SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_or_create_session(session_id: str) -> Dict[str, Any]:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            "created_at": time.time(),
            "history": [],
            "known_crop": None,
            "known_land": None,
            "known_issue": None,
            "last_scheme": None,
            "turn_count": 0
        }
    return SESSIONS[session_id]

def update_session(session_id: str, farmer_text: str, evon_result: Dict[str, Any]):
    sess = get_or_create_session(session_id)
    sess["turn_count"] += 1
    
    # Update known entities if newly detected
    crop = evon_result.get("crop")
    if crop and crop not in ["General / Not Specified", "Not Specified", "Not Mentioned"]:
        sess["known_crop"] = crop
        
    land = evon_result.get("landholding")
    if land and land not in ["Not Specified", "Standard", "Not Mentioned"]:
        sess["known_land"] = land
        
    issue = evon_result.get("core_issue")
    if issue and issue not in ["General Greeting / Awaiting Details"]:
        sess["known_issue"] = issue

    matched_scheme = evon_result.get("matched_scheme")
    if matched_scheme:
        sess["last_scheme"] = matched_scheme.get("short_name")

    # Record message turns
    sess["history"].append({
        "role": "farmer",
        "text": farmer_text,
        "timestamp": time.time()
    })
    sess["history"].append({
        "role": "assistant",
        "text": evon_result.get("advice_spoken", ""),
        "timestamp": time.time()
    })
    
    # Keep last 8 turns to keep context tidy
    if len(sess["history"]) > 16:
        sess["history"] = sess["history"][-16:]

def get_session_context_summary(session_id: str) -> str:
    sess = get_or_create_session(session_id)
    parts = []
    if sess["known_crop"]:
        parts.append(f"Previously Mentioned Crop: {sess['known_crop']}")
    if sess["known_land"]:
        parts.append(f"Landholding: {sess['known_land']}")
    if sess["known_issue"]:
        parts.append(f"Past Topic: {sess['known_issue']}")
    if sess["last_scheme"]:
        parts.append(f"Recommended Scheme: {sess['last_scheme']}")
    return " | ".join(parts) if parts else "First interaction"
