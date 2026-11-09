# 🌾 VoiceKisan — Autonomous Indic Agri-Intelligence Agent
### Built for The Great Indian AI Internship Challenge by Gnani.ai

[![Gnani AI Stack](https://img.shields.io/badge/Gnani.ai-Prisma%20%7C%20Evon%2030B%20%7C%20Timbre-brightgreen)](https://gnani.ai)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20v0.115-009688)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue)](https://python.org)

**VoiceKisan** is an autonomous Indic voice agent and market-intelligence navigator designed for Indian smallholder farmers and rural micro-entrepreneurs. It delivers a zero-typing, conversational spoken interface that understands noisy, colloquial, code-mixed Indic speech (Hindi, Telugu, Kannada, Tamil, Hinglish) and provides statutory scheme navigation and commodity price forecasting.

---

## 🌟 Key Features
- **🎙️ Gnani Prisma STT (Vachana API v3):** Transcribes code-mixed Indic speech with server-side 16kHz PCM WAV normalization.
- **🧠 Evon Reasoning Engine (`gnani-evon-v3.3-30B-A3B`):** Multi-turn conversational intent classification, entity extraction, and scheme matching.
- **📈 SARIMA Market Forecasting:** 90-day commodity price projections compared against Government MSP floors.
- **🔊 Gnani Timbre TTS (Vachana Inference):** High-fidelity regional voice synthesis using Indic voices (*Nalini*, *Kaveri*, *Pranav*, *Kartik*).
- **📋 3-Step Action Plans:** Native-script checklists for agricultural credit and crop loss claims.

---

## 🏗️ Architecture
```
voicekisan/
├── backend/
│   ├── main.py              # FastAPI core app & static mount
│   ├── gnani_service.py     # Prisma STT & Timbre TTS clients
│   ├── evon_engine.py       # Indic reasoning & intent engine
│   ├── market_service.py    # SARIMA forecasting & MSP advisory
│   ├── session_memory.py    # Multi-turn conversational state
│   ├── schemes_db.py        # Statutory schemes knowledge base
│   └── requirements.txt     # Pinned Python dependencies
├── frontend/
│   ├── index.html           # High-contrast farmer HUD
│   ├── styles.css           # Rural emerald & gold design system
│   └── app.js               # Web Audio API recording & player
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/SivaPanyam/voicekisan.git
cd voicekisan/backend
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
```env
GNANI_API_KEY=your_gnani_vachana_api_key
GNANI_PRISMA_STT_URL=https://api.vachana.ai/stt/v3
GNANI_TIMBRE_TTS_URL=https://api.vachana.ai/api/v1/tts/inference
EVON_API_URL=https://router.huggingface.co/v1/chat/completions
EVON_API_KEY=your_huggingface_token
```

### 3. Run Locally
```bash
python main.py
```
Open **http://localhost:8000** in your browser.
