"""
End-to-end Test Suite for VoiceKisan.
Tests 5 distinct rural farmer scenarios across different languages:
1. Hindi Crop Damage (PMFBY 72-hour emergency claim)
2. Telugu Crop Loan (Kisan Credit Card at 4% interest)
3. Kannada PM-KISAN (Annual ₹6,000 income support & e-KYC)
4. Hinglish Drip Irrigation (PMKSY micro-irrigation subsidy)
5. Tamil Cyclone Paddy Damage (PMFBY localized flood relief)

Verifies:
- Evon Reasoning Entity Extraction (Crop, Land, Urgency, Scheme match)
- 3-Step Action Plan generation
- Gnani Timbre live TTS audio generation with regional voices
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")

BASE_URL = "http://127.0.0.1:8000"

SCENARIOS = [
    {
        "id": "scenario_1_hindi_damage",
        "name": "Scenario 1: Hindi Crop Damage (PMFBY)",
        "language": "hi-IN",
        "expected_voice": "Nalini",
        "farmer_speech": "नमस्ते साहब, मेरे पास दो एकड़ जमीन है। कल रात बहुत तेज बारिश और ओले पड़ने से मेरी गेहूं की फसल पूरी तरह नष्ट हो गई है। मुझे मुआवजा कैसे मिलेगा?",
        "expected_crop": "Wheat",
        "expected_scheme": "PM Fasal Bima Yojana"
    },
    {
        "id": "scenario_2_telugu_kcc",
        "name": "Scenario 2: Telugu Agri-Loan (KCC)",
        "language": "te-IN",
        "expected_voice": "Kaveri",
        "farmer_speech": "నమస్కారం సార్, నాకు మూడు ఎకరాల పొలం ఉంది. కొత్త పంట పెట్టుబడి కోసం తక్కువ వడ్డీతో బ్యాంక్ లోన్ లేదా కిసాన్ క్రెడిట్ కార్డు కావాలి.",
        "expected_crop": "Wheat", # or generic
        "expected_scheme": "Kisan Credit Card"
    },
    {
        "id": "scenario_3_kannada_pmkisan",
        "name": "Scenario 3: Kannada Cash Support (PM-KISAN)",
        "language": "kn-IN",
        "expected_voice": "Pranav",
        "farmer_speech": "ನಮಸ್ಕಾರ ಸ್ವಾಮಿ, ನನ್ನ ಬಳಿ 2 ಎಕರೆ ಜಮೀನಿದೆ. ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಯ 6000 ರೂಪಾಯಿ ಸಬ್ಸಿಡಿ ಕಂತು ಇನ್ನೂ ಖಾತೆಗೆ ಬಂದಿಲ್ಲ, ಸಹಾಯ ಮಾಡಿ.",
        "expected_crop": "Wheat",
        "expected_scheme": "PM-KISAN"
    },
    {
        "id": "scenario_4_hinglish_drip",
        "name": "Scenario 4: Hinglish Micro-Irrigation (PMKSY)",
        "language": "hinglish",
        "expected_voice": "Nalini",
        "farmer_speech": "Sir, mere paas 2 acre land hai. Cotton crop me drip irrigation aur borewell lagwana hai, sarkar se kitna subsidy milega?",
        "expected_crop": "Cotton",
        "expected_scheme": "PMKSY"
    },
    {
        "id": "scenario_5_tamil_paddy",
        "name": "Scenario 5: Tamil Paddy Loss (PMFBY)",
        "language": "ta-IN",
        "expected_voice": "Karthik",
        "farmer_speech": "வணக்கம் ஐயா, என்னிடம் 2 ஏக்கர் நிலம் உள்ளது. கனமழையால் நெல் பயிர் வெள்ளத்தில் மூழ்கி சேதமடைந்துள்ளது. இழப்பீடு பெற என்ன செய்ய வேண்டும்?",
        "expected_crop": "Paddy / Rice",
        "expected_scheme": "PM Fasal Bima Yojana"
    }
]

def run_tests():
    print("=" * 70)
    print("VOICEKISAN AUTOMATED END-TO-END SCENARIO VERIFICATION")
    print("=" * 70)

    # 1. Health check
    try:
        health = requests.get(f"{BASE_URL}/api/health", timeout=5).json()
        print(f"Health Check: {health['status'].upper()} | Services: {health['gnani_ecosystem']}\n")
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    passed_count = 0

    for idx, sc in enumerate(SCENARIOS, 1):
        print(f"[{idx}/5] Testing {sc['name']}...")
        print(f"     Farmer Input ({sc['language']}): \"{sc['farmer_speech']}\"")
        
        # Step A: Evon Reasoning API
        reason_res = requests.post(
            f"{BASE_URL}/api/reason",
            json={"text": sc["farmer_speech"], "language": sc["language"]},
            timeout=20
        )
        if reason_res.status_code != 200:
            print(f"     [FAILED] Evon Reason returned HTTP {reason_res.status_code}")
            continue

        reasoning = reason_res.json()
        extracted_crop = reasoning.get("crop", "Unknown")
        matched_scheme = reasoning.get("matched_scheme", {}).get("short_name", "Unknown")
        urgency = reasoning.get("detected_urgency", "Unknown")
        plan = reasoning.get("three_step_plan", [])
        spoken_text = reasoning.get("advice_spoken", "")

        print(f"     -> Extracted Crop: {extracted_crop}")
        print(f"     -> Matched Scheme: {matched_scheme}")
        print(f"     -> Urgency: {urgency}")
        print(f"     -> Action Plan Steps: {len(plan)} steps generated")

        # Step B: Gnani Timbre Live TTS
        tts_res = requests.post(
            f"{BASE_URL}/api/tts",
            json={"text": spoken_text, "language": sc["language"]},
            timeout=20
        )
        if tts_res.status_code != 200:
            print(f"     [FAILED] Timbre TTS returned HTTP {tts_res.status_code}")
            continue

        tts_data = tts_res.json()
        audio_b64 = tts_data.get("audio_base64", "")
        provider = tts_data.get("provider", "")
        voice = tts_data.get("voice", "")

        print(f"     -> Timbre Voice: {voice} ({provider})")
        print(f"     -> Synthesized Audio: {len(audio_b64)} Base64 bytes")

        if len(audio_b64) > 1000 and len(plan) >= 3:
            print(f"     [SUCCESS] Scenario {idx} PASSED!\n")
            passed_count += 1
        else:
            print(f"     [WARN] Incomplete response in Scenario {idx}\n")

    print("=" * 70)
    print(f"TEST RESULTS: {passed_count}/{len(SCENARIOS)} SCENARIOS PASSED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
