"""
Schemes Knowledge Base for VoiceKisan.
Contains official rules and criteria for major central/state government schemes:
- PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)
- KCC (Kisan Credit Card)
- PMFBY (Pradhan Mantri Fasal Bima Yojana)
- PMKSY (Pradhan Mantri Krishi Sinchayee Yojana)
"""

from typing import Dict, Any, List

SCHEMES_DATABASE: List[Dict[str, Any]] = [
    {
        "id": "pm-kisan",
        "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "short_name": "PM-KISAN",
        "target_need": ["income support", "seed money", "working capital", "cash transfer", "fertilizer expense"],
        "max_land_limit_acres": None,  # Open to all landholding farmer families with cultivable land
        "benefit": "₹6,000 per year directly into bank accounts in 3 equal installments of ₹2,000.",
        "eligibility_criteria": [
            "Farmer family holding cultivable land in their name.",
            "Must have Aadhaar seeded with active Bank Account.",
            "Excluded: Institutional landholders, serving/retired government officers, income tax payers."
        ],
        "mandatory_documents": [
            "Aadhaar Card",
            "Land ownership papers (Khasra/Khatauni/7/12 extract/Pahani)",
            "Active Bank Passbook with IFSC",
            "e-KYC biometric/OTP verification"
        ],
        "application_mode": "Online via pmkisan.gov.in or nearest Common Service Centre (CSC)",
        "helpline": "155261 / 011-24300606"
    },
    {
        "id": "kcc",
        "name": "Kisan Credit Card (KCC)",
        "short_name": "Kisan Credit Card",
        "target_need": ["loan", "credit", "crop loan", "working capital loan", "equipment purchase", "tractor loan", "low interest loan"],
        "max_land_limit_acres": None,
        "benefit": "Subsidized collateral-free loan up to ₹1.6 Lakh (up to ₹3 Lakh at effectively 4% interest per annum with prompt repayment).",
        "eligibility_criteria": [
            "All farmers – individuals/joint borrowers who are owner cultivators.",
            "Tenant farmers, oral lessees, and sharecroppers are also eligible with self-declaration.",
            "SHGs or Joint Liability Groups (JLGs) of farmers including tenant farmers."
        ],
        "mandatory_documents": [
            "Completed Application Form with 2 passport photographs",
            "Proof of Identity (Aadhaar/Voter ID)",
            "Proof of Address",
            "Land Record proof (RoR/Patta) with crop sowing certificate"
        ],
        "application_mode": "Nearest Commercial Bank branch, RRB, Cooperative Bank, or via PM-KISAN portal",
        "helpline": "1800-180-1551 (Kisan Call Centre)"
    },
    {
        "id": "pmfby",
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "short_name": "PM Fasal Bima Yojana",
        "target_need": ["crop damage", "crop loss", "flood damage", "drought", "pest attack", "unseasonal rain", "hailstorm"],
        "max_land_limit_acres": None,
        "benefit": "Comprehensive risk insurance covering post-harvest and localized calamities. Premium is only 2% for Kharif, 1.5% for Rabi food/oilseed crops, and 5% for commercial/horticultural crops.",
        "eligibility_criteria": [
            "All farmers growing notified crops in notified areas during season (both loanee and non-loanee).",
            "CRITICAL: Crop damage must be intimated within 72 hours of occurrence."
        ],
        "mandatory_documents": [
            "Crop Insurance Policy Number / KCC details",
            "Aadhaar Card",
            "Land Sowing Certificate / Patta passbook",
            "Geotagged photos of damaged crop / Field survey report"
        ],
        "application_mode": "Crop Insurance App, pmfby.gov.in portal, or inform Bank/Agriculture Officer within 72 hrs",
        "helpline": "14447 (National Crop Insurance Portal Helpline)"
    },
    {
        "id": "pmksy",
        "name": "PM Krishi Sinchayee Yojana (Micro-Irrigation Subsidies)",
        "short_name": "PMKSY Drip/Sprinkler Subsidy",
        "target_need": ["irrigation", "drip irrigation", "sprinkler", "water scarcity", "borewell subsidy"],
        "max_land_limit_acres": None,
        "benefit": "Up to 55% subsidy for small/marginal farmers and 45% for other farmers for installing drip and sprinkler systems.",
        "eligibility_criteria": [
            "All landholder farmers with assured water source.",
            "Preference to small and marginal farmers (under 5 acres)."
        ],
        "mandatory_documents": [
            "Land title (RoR)",
            "Aadhaar card",
            "Electricity bill / Water source certificate",
            "Bank passbook"
        ],
        "application_mode": "District Horticulture / Agriculture Officer or State Agri-portal",
        "helpline": "1800-180-1551"
    }
]

def search_schemes(issue_text: str, crop: str = "", landholding_acres: float = None) -> List[Dict[str, Any]]:
    """
    Find relevant schemes based on semantic keywords in the issue/need.
    """
    issue_lower = issue_text.lower()
    crop_lower = crop.lower()
    matches = []

    for scheme in SCHEMES_DATABASE:
        score = 0
        for needle in scheme["target_need"]:
            if needle in issue_lower or needle in crop_lower:
                score += 2
        
        # Priority keyword checks
        if "damage" in issue_lower or "rain" in issue_lower or "flood" in issue_lower or "loss" in issue_lower or "nuksan" in issue_lower or "nashtam" in issue_lower or "hansam" in issue_lower:
            if scheme["id"] == "pmfby":
                score += 5
        elif "loan" in issue_lower or "paisa" in issue_lower or "credit" in issue_lower or "karza" in issue_lower or "appu" in issue_lower or "kadana" in issue_lower:
            if scheme["id"] == "kcc":
                score += 5
        elif "subsidy" in issue_lower or "kisan" in issue_lower or "installment" in issue_lower or "kist" in issue_lower or "help" in issue_lower:
            if scheme["id"] == "pm-kisan":
                score += 4

        if score > 0:
            matches.append((score, scheme))

    matches.sort(key=lambda x: x[0], reverse=True)
    if matches:
        return [m[1] for m in matches]
    return [SCHEMES_DATABASE[0]]  # Default to PM-KISAN
