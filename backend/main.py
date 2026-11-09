"""
VoiceKisan FastAPI Main Application.
Features:
- Multi-turn Conversational Memory per session
- Real-time Agricultural Mandi & Price Forecasting Engine
- Gnani Prisma STT (Vachana) + Timbre TTS (Vachana) live voice stack
- Evon Reasoning with fast Indic rule and conversational intent routing
- High contrast, mobile-first responsive dashboard
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from gnani_service import transcribe_speech, synthesize_speech
from evon_engine import reason_with_evon
from schemes_db import SCHEMES_DATABASE
from market_service import analyze_crop_market
from session_memory import get_or_create_session, update_session, get_session_context_summary

app = FastAPI(
    title="VoiceKisan - Autonomous Indic Agri-Intelligence Agent",
    description="Conversational Indic AI Agent powered by Gnani AI (Prisma & Timbre) and SARIMA Price Forecasting.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextReasonRequest(BaseModel):
    text: str
    language: Optional[str] = "hi-IN"
    session_id: Optional[str] = "default_user"

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "hi-IN"
    voice: Optional[str] = None

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "VoiceKisan Autonomous Agent",
        "version": "2.0.0",
        "gnani_ecosystem": {
            "stt": "Gnani Prisma STT (Vachana API v3)",
            "tts": "Gnani Timbre TTS (Vachana inference)",
            "reasoning": "Evon Indic Reasoning Engine",
            "market_intelligence": "SARIMA & MSP Statutory Engine"
        }
    }

@app.get("/api/schemes")
async def get_all_schemes():
    return {"schemes": SCHEMES_DATABASE}

@app.get("/api/market/{crop_name}")
async def get_market_analysis(crop_name: str, language: str = "hi-IN"):
    """Returns Mandi vs MSP and 3-month forecast for the given crop"""
    analysis = analyze_crop_market(crop_name, language=language)
    return analysis

@app.post("/api/stt")
async def handle_stt(
    audio: UploadFile = File(...),
    language: str = Form("hi-IN")
):
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio payload received")
        result = transcribe_speech(audio_bytes, language=language)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reason")
async def handle_reason(payload: TextReasonRequest):
    try:
        # Check session context
        sess_summary = get_session_context_summary(payload.session_id)
        reasoning = reason_with_evon(payload.text, language=payload.language)
        
        # Enrich with market analysis if a crop was mentioned
        crop = reasoning.get("crop")
        if crop and crop not in ["General / Not Specified", "Not Specified", "Not Mentioned"]:
            market = analyze_crop_market(crop, language=payload.language)
            reasoning["market_intelligence"] = market
            # If farmer asked about price/mandi/sell/rate, augment spoken advice
            lower_text = payload.text.lower()
            if any(w in lower_text for w in ["rate", "bhav", "price", "mandi", "bechu", "sell", "dar", "kharid"]):
                reasoning["advice_spoken"] += f" {market['spoken_advice']}"

        update_session(payload.session_id, payload.text, reasoning)
        return reasoning
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts")
async def handle_tts(payload: TTSRequest):
    try:
        tts_result = synthesize_speech(payload.text, language=payload.language, voice=payload.voice)
        return tts_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-voice")
async def process_voice_pipeline(
    audio: UploadFile = File(...),
    language: str = Form("hi-IN"),
    session_id: str = Form("default_user")
):
    """
    End-to-End Autonomous Voice Pipeline:
    1. Prisma STT (Vachana): Audio -> Accurate Indic Transcript
    2. Evon Reasoning: Multi-turn intent, Scheme Matching & SARIMA Market Forecasting
    3. Timbre TTS (Vachana): Synthesizes Regional Spoken Voice
    """
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio file is empty.")

        # Step 1: Prisma Transcription
        stt_result = transcribe_speech(audio_bytes, language=language)
        transcript = stt_result.get("transcript", "")

        # Step 2: Evon Reasoning & Memory Update
        evon_result = reason_with_evon(transcript, language=language)
        
        # Market Intelligence integration
        crop = evon_result.get("crop")
        market_data = None
        if crop and crop not in ["General / Not Specified", "Not Specified", "Not Mentioned"]:
            market_data = analyze_crop_market(crop, language=language)
            evon_result["market_intelligence"] = market_data
            
            lower_text = transcript.lower()
            if any(w in lower_text for w in ["rate", "bhav", "price", "mandi", "bechu", "sell", "dar", "kharid"]):
                evon_result["advice_spoken"] += f" {market_data['spoken_advice']}"

        update_session(session_id, transcript, evon_result)

        # Step 3: Timbre Speech Synthesis
        spoken_text = evon_result.get("advice_spoken", "")
        tts_result = synthesize_speech(spoken_text, language=language)

        return {
            "success": True,
            "session_id": session_id,
            "pipeline": {
                "step1_prisma_stt": stt_result,
                "step2_evon_reasoning": evon_result,
                "step3_timbre_tts": {
                    "audio_base64": tts_result.get("audio_base64"),
                    "mime_type": tts_result.get("mime_type", "audio/wav"),
                    "voice": tts_result.get("voice"),
                    "provider": tts_result.get("provider")
                }
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Frontend static files mounting (only mounted if directory exists and not in serverless static mode)
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if frontend_path.exists():
    try:
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    except Exception as e:
        print(f"Static mounting note: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
