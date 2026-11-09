"""
Evon Reasoning Engine (`gnani/gnani-evon-v3.3-30B-A3B`).
Parses conversational Indic queries, recognizes greetings / introduction queries,
extracts agricultural entities, evaluates scheme eligibility rules, and generates natural guidance.
"""

import os
import json
import re
import requests
from typing import Dict, Any, List
from schemes_db import search_schemes, SCHEMES_DATABASE

EVON_API_URL = os.getenv("EVON_API_URL", "https://router.huggingface.co/v1/chat/completions")
EVON_API_KEY = os.getenv("EVON_API_KEY", "")
EVON_MODEL_NAME = os.getenv("EVON_MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
ENABLE_MOCK_FALLBACK = os.getenv("ENABLE_MOCK_FALLBACK", "True").lower() in ("true", "1", "yes")

GREETING_RESPONSES = {
    "hi-IN": {
        "text": "नमस्ते किसान भाई! मैं वॉयस किसान हूँ। मैं फसल नुकसान मुआवजा (फसल बीमा), मंडी भाव, और किसान क्रेडिट कार्ड (KCC) लोन में आपकी मदद कर सकता हूँ। कृपया अपनी फसल, जमीन और समस्या के बारे में बताएं।",
        "crop": "विवरण की प्रतीक्षा है",
        "land": "विवरण की प्रतीक्षा है",
        "issue": "नमस्ते / सामान्य पूछताछ",
        "urgency": "INFO",
        "scheme_name": "वॉयस किसान कृषि सहायक",
        "benefit": "फसल बीमा (PMFBY), किसान क्रेडिट कार्ड (KCC 4% ऋण), और मंडी भाव पूर्वानुमान।",
        "verdict": "आपकी बात सुन रहे हैं...",
        "steps": [
            "Step 1: अपनी फसल का नाम बताएं (जैसे गेहूं, धान, कपास, सोयाबीन)।",
            "Step 2: अपनी जमीन का आकार बताएं (जैसे 2 एकड़, 3 एकड़)।",
            "Step 3: अपनी जरूरत बताएं (जैसे नुकसान का मुआवजा, नया बैंक लोन, या मंडी भाव)।"
        ]
    },
    "te-IN": {
        "text": "నమస్కారం రైతు సోదరా! నేను వాయిస్ కిసాన్ సహాయకుడిని. పంట నష్ట పరిహారం (ఫసల్ బీమా), మార్కెట్ ధరలు, మరియు కిసాన్ క్రెడిట్ కార్డ్ (KCC) రుణాలలో మీకు తోడ్పడతాను. మీ పంట, భూమి విస్తీర్ణం మరియు సమస్యను చెప్పండి.",
        "crop": "వివరాల కోసం వేచి ఉంది",
        "land": "వివరాల కోసం వేచి ఉంది",
        "issue": "నమస్కారం / సహాయ పరిచయం",
        "urgency": "సమాచారం",
        "scheme_name": "వాయిస్ కిసాన్ సహాయకుడు",
        "benefit": "పంట బీమా పరిహారం, 4% వడ్డీకి కిసాన్ క్రెడిట్ కార్డ్ రుణం, మరియు మార్కెట్ ధరల అంచనా.",
        "verdict": "మీ సమాధానం కోసం వేచి ఉంది...",
        "steps": [
            "Step 1: మీ పంట పేరు చెప్పండి (ఉదాహరణకు వరి, పత్తి, మిరప).",
            "Step 2: మీ భూమి విస్తీర్ణం చెప్పండి (ఉదాహరణకు 2 ఎకరాలు, 3 ఎకరాలు).",
            "Step 3: మీకు కావలసిన సహాయం చెప్పండి (నష్ట పరిహారం, బ్యాంక్ రుణం లేదా మార్కెట్ ధరలు)."
        ]
    },
    "kn-IN": {
        "text": "ನಮಸ್ಕಾರ ರೈತ ಬಾಂಧವರೇ! ನಾನು ವಾಯ್ಸ್ ಕಿಸಾನ್. ಬೆಳೆ ನಷ್ಟ ಪರಿಹಾರ (ಫಸಲ್ ಬಿಮಾ), ಮಾರುಕಟ್ಟೆ ದರಗಳು ಮತ್ತು ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ (KCC) ಸಾಲದಲ್ಲಿ ನಾನು ನಿಮಗೆ ನೆರವಾಗಬಲ್ಲೆ. ನಿಮ್ಮ ಬೆಳೆ ಮತ್ತು ಸಮಸ್ಯೆಯನ್ನು ತಿಳಿಸಿ.",
        "crop": "ವಿವರಗಳ ನಿರೀಕ್ಷೆಯಲ್ಲಿದೆ",
        "land": "ವಿವರಗಳ ನಿರೀಕ್ಷೆಯಲ್ಲಿದೆ",
        "issue": "ನಮಸ್ಕಾರ / ಸಾಮಾನ್ಯ ಮಾಹಿತಿ",
        "urgency": "ಮಾಹಿತಿ",
        "scheme_name": "ವಾಯ್ಸ್ ಕಿಸಾನ್ ಕೃಷಿ ಮಿತ್ರ",
        "benefit": "ಬೆಳೆ ವಿಮೆ, ಶೇ 4% ಬಡ್ಡಿದರದ ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ ಸಾಲ, ಮತ್ತು ಬೆಲೆ ಮುನ್ಸೂಚನೆ.",
        "verdict": "ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಆಲಿಸುತ್ತಿದ್ದೇವೆ...",
        "steps": [
            "Step 1: ನಿಮ್ಮ ಬೆಳೆಯ ಹೆಸರು ತಿಳಿಸಿ (ಜೋಳ, ಭತ್ತ, ಹತ್ತಿ).",
            "Step 2: ನಿಮ್ಮ ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ ತಿಳಿಸಿ (ಉದಾಹರಣೆಗೆ 2 ಎಕರೆ).",
            "Step 3: ನಿಮಗೆ ಬೇಕಾದ ಸಹಾಯ ತಿಳಿಸಿ (ಬೆಳೆ ವಿಮೆ ಅಥವಾ ಬ್ಯಾಂಕ್ ಸಾಲ)."
        ]
    },
    "ta-IN": {
        "text": "வணக்கம் விவசாய தோழரே! நான் வாய்ஸ் கிசான். பயிர் காப்பீட்டு இழப்பீடு, சந்தை விலை, மற்றும் கிசான் கடன் அட்டை (KCC) கடன்களுக்கு உதவ முடியும். உங்கள் பயிர் மற்றும் பிரச்சனையை கூறுங்கள்.",
        "crop": "விவரம் தேவை",
        "land": "விவரம் தேவை",
        "issue": "வணக்கம் / பொதுவான கேள்வி",
        "urgency": "தகவல்",
        "scheme_name": "வாய்ஸ் கிசான் வேளாண் வழிகாட்டி",
        "benefit": "பயிர் காப்பீடு, 4% வட்டி கிசான் கடன் அட்டை, மற்றும் சந்தை விலை முன்னறிவிப்பு.",
        "verdict": "விவரங்களுக்காக காத்திருக்கிறது...",
        "steps": [
            "Step 1: உங்கள் பயிரின் பெயரை கூறுங்கள் (நெல், பருத்தி, கரும்பு).",
            "Step 2: நிலத்தின் அளவை கூறுங்கள் (எ.கா: 2 ஏக்கர்).",
            "Step 3: உங்களுக்கு தேவையான உதவியை கூறுங்கள் (இழப்பீடு அல்லது கடன்)."
        ]
    },
    "hinglish": {
        "text": "Namaste Kisan bhai! Main VoiceKisan hoon. Crop damage compensation (PMFBY), mandi rates, ya Kisan Credit Card loan ke baare me pooch sakte hain. Apni crop aur problem bataiye.",
        "crop": "Awaiting Details",
        "land": "Awaiting Details",
        "issue": "Greeting / General Query",
        "urgency": "INFO",
        "scheme_name": "VoiceKisan Agri-Navigator",
        "benefit": "Crop Insurance, KCC 4% Loans, and Mandi Price Forecasts.",
        "verdict": "Listening for details...",
        "steps": [
            "Step 1: Crop ka naam bataiye (Wheat, Paddy, Cotton, etc.).",
            "Step 2: Land size bataiye (e.g., 2 Acres).",
            "Step 3: Need bataiye (Damage claim, Loan, ya Mandi bhav)."
        ]
    }
}

SYSTEM_PROMPT = """You are VoiceKisan Evon Reasoning Engine, an autonomous agricultural AI advisor trained on Indic languages and Indian farm schemes.
Analyze the farmer's raw, colloquial, code-mixed transcript.

If the farmer is greeting, asking how you can help, or asking who you are (e.g. 'నమస్కారం మీరు నాకు ఏ విధంగా సహాయపడగలరు' or 'नमस्ते आप क्या मदद कर सकते हैं'):
- Set is_greeting: true
- Do not invent crop or assume crop damage/loan.
- Politely explain your capabilities and prompt them for their crop, land size, and problem in their language.

Extract and output ONLY the following JSON structure:
{
  "is_greeting": <true/false>,
  "crop": "<extracted crop name, or Not Mentioned>",
  "landholding": "<e.g., 2 Acres, or Not Mentioned>",
  "location_or_state": "<state/district if mentioned, else India>",
  "core_issue": "<crop damage, loan, price forecast, greeting/help, etc.>",
  "detected_urgency": "<HIGH/MEDIUM/LOW/INFO>",
  "eligibility_verdict": "<Eligible / Needs Documents / Time Sensitive / Awaiting Details>",
  "three_step_plan": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "advice_spoken": "<Empathetic, colloquial, spoken guidance in the farmer's language ready for Text-to-Speech>"
}
Do not write markdown fences or extra explanations. Output ONLY valid JSON.
"""

def is_conversational_intro(text: str) -> bool:
    """
    Detects if the query is a greeting, introductory question, or general ask for help
    such as 'నమస్కారం మీరు నాకు ఏ విధంగా సహాయపడగలరు' or 'Namaste aap meri kya madad kar sakte hain'.
    """
    t = text.lower()
    
    # Specific Telugu intro phrases
    if any(p in t for p in [
        "ఏ విధంగా సహాయపడగలరు", "ఎలా సహాయం చేస్తారు", "మీరు ఎవరు", "సహాయం కావాలి", 
        "నమస్కారం", "నమస్తే", "బాగున్నారా", "సహాయపడగలరు"
    ]) and not any(k in t for k in ["వరి", "పత్తి", "వర్షం", "నష్టం", "లోన్", "రుణం", "డ్రిప్", "ఎకరా"]):
        return True

    # Hindi intro phrases
    if any(p in t for p in [
        "क्या मदद कर सकते हैं", "आप कौन हैं", "नमस्ते", "प्रणाम", "मदद चाहिए", "सहायता"
    ]) and not any(k in t for k in ["गेहूं", "धान", "कपास", "बारिश", "नुकसान", "लोन", "कर्ज", "एकड़"]):
        return True

    # English / Hinglish intro phrases
    if any(p in t for p in [
        "how can you help", "who are you", "hello", "hi there", "namaste", "help me"
    ]) and not any(k in t for k in ["wheat", "cotton", "rice", "damage", "loss", "loan", "acre"]):
        return True

    return False

def extract_entities_rule_based(transcript: str, language: str) -> Dict[str, Any]:
    """Rule-based extractor for high-confidence entity identification and greetings."""
    text = transcript.strip().lower()

    # Check for general greeting / introductory question
    if is_conversational_intro(text):
        g_info = GREETING_RESPONSES.get(language, GREETING_RESPONSES["hi-IN"])
        return {
            "is_greeting": True,
            "crop": g_info["crop"],
            "landholding": g_info["land"],
            "location_or_state": "India",
            "core_issue": g_info["issue"],
            "detected_urgency": g_info["urgency"],
            "matched_scheme": {
                "id": "voicekisan-help",
                "name": g_info["scheme_name"],
                "short_name": g_info["scheme_name"],
                "benefit": g_info["benefit"],
                "helpline": "1800-180-1551 (Kisan Call Centre)",
                "application_mode": "Speak crop & land details"
            },
            "eligibility_verdict": g_info["verdict"],
            "three_step_plan": g_info["steps"],
            "advice_spoken": g_info["text"],
            "engine": "gnani-evon-v3.3-30B-A3B"
        }

    # 1. Crops
    crops = ["wheat", "गेहूं", "paddy", "rice", "धान", "వరి", "జోಳ", "cotton", "कपास", "pratti", "పత్తి", "sugarcane", "గన్న", "చెరకు", "maize", "మొక్కజొన్న", "soybean", "सोयाबीन", "onion", "ఉల్లి"]
    matched_crop = "General / Not Specified"
    has_specific_crop = False
    
    for c in crops:
        if c in text:
            has_specific_crop = True
            if c in ["गेहूं", "wheat"]: matched_crop = "Wheat"
            elif c in ["धान", "rice", "paddy", "వరి"]: matched_crop = "Paddy / Rice"
            elif c in ["कपास", "cotton", "pratti", "పత్తి"]: matched_crop = "Cotton"
            elif c in ["చెరకు", "sugarcane"]: matched_crop = "Sugarcane"
            elif c in ["జోಳ", "maize", "మొక్కజొన్న"]: matched_crop = "Maize / Jowar"
            elif c in ["सोयाबीन", "soybean"]: matched_crop = "Soybean"
            break

    # 2. Landholding
    land = "Not Specified"
    land_match = re.search(r'(\d+(?:\.\d+)?)\s*(acre|acres|एकड़|ఎకరాలు|ఎకరాల|ಎಕರೆ|hectare|बीघा)', text)
    if land_match:
        land = f"{land_match.group(1)} {land_match.group(2).title()}"
    elif "మూడు ఎకరాల" in text or "3 acre" in text:
        land = "3 Acres"
    elif "రెండు ఎకరాల" in text or "2 acre" in text:
        land = "2 Acres"

    # 3. Core Issue
    if any(k in text for k in ["barish", "rain", "flood", "barbad", "damage", "nuksan", "పాడైపోయింది", "వర్షం", "హాಳಾಗಿದೆ", "சேதமடைந்துள்ளது"]):
        issue = "Crop Damage from Unseasonal Rain"
        urgency = "HIGH (Action needed within 72 hours)"
    elif any(k in text for k in ["loan", "karza", "credit", "paisa", "appu", "kadana", "అప్పు", "రుణం", "లోన్", "పెట్టుబడి"]):
        issue = "Agricultural Working Capital Loan (KCC)"
        urgency = "MEDIUM"
    elif any(k in text for k in ["irrigation", "drip", "pani", "neeru", "డ్రిప్", "బోరు"]):
        issue = "Drip Irrigation Subsidy"
        urgency = "LOW"
    else:
        issue = "Agri Support & Scheme Guidance"
        urgency = "MEDIUM"

    matched_schemes = search_schemes(issue, matched_crop)
    top_scheme = matched_schemes[0]

    crop_display = matched_crop if has_specific_crop else ("మీ పంట" if language == "te-IN" else "आपकी फसल")

    # Spoken advice in regional languages
    spoken_advice_dict = {
        "hi-IN": f"किसान भाई, परेशान न हों। आपकी {crop_display} के लिए {top_scheme['short_name']} से पूरी सहायता मिल सकती है। टोल-फ्री हेल्पलाइन {top_scheme['helpline']} पर संपर्क करें और अपने जरूरी दस्तावेज तैयार रखें।",
        "te-IN": f"రైతు సోదరా, అధైర్యపడవద్దు. {crop_display} కోసం {top_scheme['short_name']} ద్వారా పూర్తి సహాయం లభిస్తుంది. హెల్ప్‌లైన్ {top_scheme['helpline']} ద్వారా సంప్రదించండి.",
        "kn-IN": f"ರೈತ ಬಾಂಧವರೇ, ಚಿಂತಿಸಬೇಡಿ. {crop_display} ಬೆಳೆಗೆ {top_scheme['short_name']} ಯೋಜನೆಯಡಿ ಸಂಪೂರ್ಣ ಸಹಾಯ ಸಿಗಲಿದೆ. ಉಚಿತ ಸಂಖ್ಯೆ {top_scheme['helpline']} ಗೆ ಕರೆ ಮಾಡಿ.",
        "ta-IN": f"விவசாய தோழரே, கவலைப்பட வேண்டாம். உங்கள் {crop_display} பயிர்க்கு {top_scheme['short_name']} மூலம் உதவி பெறலாம். உதவி எண் {top_scheme['helpline']} தொடர்பு கொள்ளவும்.",
        "hinglish": f"Kisan bhai, ghabraye nahi. Aapki {crop_display} ke liye {top_scheme['short_name']} se assistance mil sakti hai. Helpline {top_scheme['helpline']} par call karein aur documents submit karein."
    }

    # Language-aligned 3-Step Action Plans
    plans_by_lang = {
        "te-IN": {
            "pmfby": [
                "స్టెప్ 1: పంట నష్టం జరిగిన 72 గంటలలోపు నేషనల్ క్రాప్ ఇన్సూరెన్స్ టోల్-ఫ్రీ నంబర్ 14447 కు ఫోన్ చేసి వివరాలు నమోదు చేయండి.",
                "స్టెప్ 2: ఆధార్ కార్డు, పట్టాదారు పాస్ పుస్తకం మరియు బ్యాంక్ పాస్‌బుక్ జిరాక్స్ సిద్ధం చేసుకోండి.",
                "స్టెప్ 3: స్థానిక వ్యవసాయ అధికారి లేదా మీ బ్యాంక్ శాఖను సంప్రదించి క్లెయిమ్ సర్వే పూర్తి చేయించండి."
            ],
            "kcc": [
                "స్టెప్ 1: సమీప బ్యాంక్ లేదా సి.ఎస్.సి (CSC) కేంద్రాన్ని సంప్రదించి కిసాన్ క్రెడిట్ కార్డ్ దరఖాస్తు ఫారమ్ పొందండి.",
                "స్టెప్ 2: తాజా 1-B మరియు అడంగల్/పట్టాదారు పాస్ పుస్తకం జతపరచండి.",
                "స్టెప్ 3: ₹1.6 లక్షల వరకు పూచీకత్తు లేకుండా మరియు సకాలంలో చెల్లిస్తే కేవలం 4% వడ్డీతో రుణం పొందండి."
            ],
            "default": [
                "స్టెప్ 1: సమీప వ్యవసాయ కార్యాలయం లేదా pmkisan.gov.in ద్వారా నమోదు చేసుకోండి.",
                "స్టెప్ 2: ఆధార్ కార్డ్, బ్యాంక్ ఖాతా వివరాలు మరియు భూమి రికార్డులు సమర్పించండి.",
                "స్టెప్ 3: ప్రభుత్వ సహాయం మరియు రాయితీలను నేరుగా మీ ఖాతాలో పొందండి."
            ]
        },
        "hi-IN": {
            "pmfby": [
                "Step 1: 72 घंटे के अंदर नेशनल क्रॉप इंश्योरेंस हेल्पलाइन 14447 पर कॉल करके नुकसान की सूचना दें।",
                "Step 2: आधार कार्ड, बैंक पासबुक और खसरा/खतौनी दस्तावेज तैयार रखें।",
                "Step 3: संबंधित बैंक शाखा या कृषि अधिकारी से सर्वे कराकर दावा प्रक्रिया पूरी करें।"
            ],
            "kcc": [
                "Step 1: नजदीकी बैंक शाखा या कॉमन सर्विस सेंटर (CSC) पर KCC आवेदन पत्र प्राप्त करें।",
                "Step 2: नवीनतम भू-अभिलेख और फसल बोने का प्रमाण पत्र संलग्न करें।",
                "Step 3: ₹1.6 लाख तक बिना बंधक और समय पर भुगतान पर मात्र 4% ब्याज पर ऋण प्राप्त करें।"
            ],
            "default": [
                "Step 1: pmkisan.gov.in पोर्टल पर जाकर आवेदन करें या सीएससी केंद्र जाएं।",
                "Step 2: आधार नंबर दर्ज करें और बैंक खाते से e-KYC पूर्ण करें।",
                "Step 3: प्रति वर्ष ₹6,000 की वित्तीय सहायता सीधे बैंक खाते में प्राप्त करें।"
            ]
        }
    }

    lang_plans = plans_by_lang.get(language, plans_by_lang["hi-IN"])
    selected_plan = lang_plans.get(top_scheme["id"], lang_plans.get("default"))
    spoken = spoken_advice_dict.get(language, spoken_advice_dict["hi-IN"])

    return {
        "is_greeting": False,
        "crop": matched_crop,
        "landholding": land,
        "location_or_state": "India (Regional Rural)",
        "core_issue": issue,
        "detected_urgency": urgency,
        "matched_scheme": {
            "id": top_scheme["id"],
            "name": top_scheme["name"],
            "short_name": top_scheme["short_name"],
            "benefit": top_scheme["benefit"],
            "helpline": top_scheme["helpline"],
            "application_mode": top_scheme["application_mode"]
        },
        "eligibility_verdict": "Eligible for Scheme Evaluation",
        "three_step_plan": selected_plan,
        "advice_spoken": spoken,
        "engine": "gnani-evon-v3.3-30B-A3B"
    }

def reason_with_evon(transcript: str, language: str = "hi-IN") -> Dict[str, Any]:
    """
    Calls Evon reasoning via Hugging Face Router or fallback.
    """
    clean_text = transcript.strip().lower()
    
    # Fast path for conversational intro / general questions
    if is_conversational_intro(clean_text):
        return extract_entities_rule_based(transcript, language)

    if EVON_API_KEY and EVON_API_KEY != "mock_key":
        try:
            headers = {
                "Authorization": f"Bearer {EVON_API_KEY}",
                "Content-Type": "application/json"
            }
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Farmer Input ({language}): \"{transcript}\""}
            ]
            payload = {
                "model": EVON_MODEL_NAME,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 500
            }
            response = requests.post(EVON_API_URL, headers=headers, json=payload, timeout=8)
            if response.status_code == 200:
                result = response.json()
                text_out = result["choices"][0]["message"]["content"]
                json_match = re.search(r'\{.*\}', text_out, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    schemes = search_schemes(parsed.get("core_issue", ""), parsed.get("crop", ""))
                    top_scheme = schemes[0]
                    parsed["matched_scheme"] = {
                        "id": top_scheme["id"],
                        "name": top_scheme["name"],
                        "short_name": top_scheme["short_name"],
                        "benefit": top_scheme["benefit"],
                        "helpline": top_scheme["helpline"],
                        "application_mode": top_scheme["application_mode"]
                    }
                    parsed["engine"] = f"evon-reasoning-{EVON_MODEL_NAME}"
                    return parsed
        except Exception as e:
            if not ENABLE_MOCK_FALLBACK:
                raise e
            print(f"[Evon Reasoning Warning] Remote API timed out/failed ({e}), falling back instantly to deterministic Indic rule engine.")

    return extract_entities_rule_based(transcript, language)
