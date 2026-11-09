// VoiceKisan v2.0 - Conversational Indic Voice Intelligence Frontend
// Supports Web Audio recording, real-time waveform visualizers, conversational feed streaming, and SARIMA market HUD updates

let mediaRecorder = null;
let audioChunks = [];
let audioContext = null;
let analyser = null;
let dataArray = null;
let animationFrameId = null;
let isRecording = false;

// Persistent session id per browser tab
const SESSION_ID = "vk_session_" + Math.random().toString(36).substring(2, 9);

// DOM Elements
const recordBtn = document.getElementById('recordBtn');
const recordStatus = document.getElementById('recordStatus');
const langSelect = document.getElementById('langSelect');
const visualizerCanvas = document.getElementById('visualizerCanvas');
const canvasCtx = visualizerCanvas.getContext('2d');
const sessionIdDisplay = document.getElementById('sessionIdDisplay');
const conversationFeed = document.getElementById('conversationFeed');

// Pipeline Steps
const stepMic = document.getElementById('step-mic');
const stepPrisma = document.getElementById('step-prisma');
const stepEvon = document.getElementById('step-evon');
const stepMarket = document.getElementById('step-market');
const stepTimbre = document.getElementById('step-timbre');

// Entities
const entityCrop = document.getElementById('entityCrop');
const entityLand = document.getElementById('entityLand');
const entityIssue = document.getElementById('entityIssue');
const entityUrgency = document.getElementById('entityUrgency');

// Market Intelligence HUD
const marketHud = document.getElementById('marketHud');
const mandiDecisionBadge = document.getElementById('mandiDecisionBadge');
const statMsp = document.getElementById('statMsp');
const statMandi = document.getElementById('statMandi');
const statForecast = document.getElementById('statForecast');
const marketAdvisoryText = document.getElementById('marketAdvisoryText');

// Schemes & Plan
const schemeTitle = document.getElementById('schemeTitle');
const eligibilityTag = document.getElementById('eligibilityTag');
const schemeBenefit = document.getElementById('schemeBenefit');
const planList = document.getElementById('planList');
const ttsAudioPlayer = document.getElementById('ttsAudioPlayer');
const audioStatusText = document.getElementById('audioStatusText');

sessionIdDisplay.innerText = SESSION_ID;

// Pipeline Step Highlighter
function setPipelineStep(stepName) {
  [stepMic, stepPrisma, stepEvon, stepMarket, stepTimbre].forEach(s => {
    s.classList.remove('active');
  });

  if (stepName === 'mic') {
    stepMic.classList.add('active');
  } else if (stepName === 'prisma') {
    stepMic.classList.add('completed');
    stepPrisma.classList.add('active');
  } else if (stepName === 'evon') {
    stepPrisma.classList.add('completed');
    stepEvon.classList.add('active');
  } else if (stepName === 'market') {
    stepEvon.classList.add('completed');
    stepMarket.classList.add('active');
  } else if (stepName === 'timbre') {
    stepMarket.classList.add('completed');
    stepTimbre.classList.add('active');
  } else if (stepName === 'done') {
    [stepMic, stepPrisma, stepEvon, stepMarket, stepTimbre].forEach(s => {
      s.classList.remove('active');
      s.classList.add('completed');
    });
  }
}

// Visualizer Waveform Drawing
function drawVisualizer() {
  animationFrameId = requestAnimationFrame(drawVisualizer);
  if (!analyser) return;

  analyser.getByteFrequencyData(dataArray);

  canvasCtx.fillStyle = '#081a0e';
  canvasCtx.fillRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);

  const barWidth = (visualizerCanvas.width / dataArray.length) * 2.5;
  let barHeight;
  let x = 0;

  for (let i = 0; i < dataArray.length; i++) {
    barHeight = dataArray[i] / 3.8;
    canvasCtx.fillStyle = `rgb(${barHeight + 80}, 230, 118)`;
    canvasCtx.fillRect(x, visualizerCanvas.height - barHeight, barWidth, barHeight);
    x += barWidth + 2;
  }
}

// Convert audio buffer to clean 16-bit PCM WAV Blob
function audioBufferToWav(buffer) {
  const numOfChan = buffer.numberOfChannels;
  const length = buffer.length * numOfChan * 2 + 44;
  const out = new DataView(new ArrayBuffer(length));
  const channels = [];
  let sample;
  let offset = 0;
  let pos = 0;

  function setUint16(data) {
    out.setUint16(pos, data, true);
    pos += 2;
  }
  function setUint32(data) {
    out.setUint32(pos, data, true);
    pos += 4;
  }

  setUint32(0x46464952); // "RIFF"
  setUint32(length - 8);
  setUint32(0x45564157); // "WAVE"

  setUint32(0x20746d66); // "fmt "
  setUint32(16);
  setUint16(1);          // PCM
  setUint16(numOfChan);
  setUint32(buffer.sampleRate);
  setUint32(buffer.sampleRate * 2 * numOfChan);
  setUint16(numOfChan * 2);
  setUint16(16);

  setUint32(0x61746164); // "data"
  setUint32(length - pos - 4);

  for (let i = 0; i < buffer.numberOfChannels; i++) {
    channels.push(buffer.getChannelData(i));
  }

  while (offset < buffer.length) {
    for (let i = 0; i < numOfChan; i++) {
      sample = Math.max(-1, Math.min(1, channels[i][offset]));
      sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
      out.setInt16(pos, sample, true);
      pos += 2;
    }
    offset++;
  }

  return new Blob([out], { type: 'audio/wav' });
}

// Append Chat Message
function appendChatMessage(role, text) {
  const bubble = document.createElement('div');
  bubble.className = `msg-bubble ${role === 'farmer' ? 'user-msg' : 'bot-msg'}`;
  
  const sender = document.createElement('div');
  sender.className = 'msg-sender';
  sender.innerText = role === 'farmer' ? '👨‍🌾 Farmer (You)' : '🌾 VoiceKisan';
  
  const content = document.createElement('div');
  content.className = 'msg-text';
  content.innerText = text;
  
  bubble.appendChild(sender);
  bubble.appendChild(content);
  conversationFeed.appendChild(bubble);
  conversationFeed.scrollTop = conversationFeed.scrollHeight;
}

// Audio Recording Initialization
async function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(stream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);

    const bufferLength = analyser.frequencyBinCount;
    dataArray = new Uint8Array(bufferLength);
    drawVisualizer();

    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      cancelAnimationFrame(animationFrameId);
      const rawBlob = new Blob(audioChunks);
      const arrayBuffer = await rawBlob.arrayBuffer();
      const decodedBuffer = await audioContext.decodeAudioData(arrayBuffer);
      const wavBlob = audioBufferToWav(decodedBuffer);
      await processVoiceInput(wavBlob);
    };

    mediaRecorder.start();
    isRecording = true;
    recordBtn.classList.add('recording');
    recordBtn.innerHTML = '⏹️';
    recordStatus.innerText = 'Listening to your voice... (Tap to stop)';
    setPipelineStep('mic');
  } catch (err) {
    console.warn("Microphone access error:", err);
    recordStatus.innerText = 'Mic access unavailable. Try quick preset chips below.';
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  isRecording = false;
  recordBtn.classList.remove('recording');
  recordBtn.innerHTML = '🎤';
  recordStatus.innerText = 'Processing speech with Gnani AI & Market Engine...';
}

recordBtn.addEventListener('click', toggleRecording);

// Process Voice Pipeline
async function processVoiceInput(audioBlob) {
  const selectedLang = langSelect.value;
  setPipelineStep('prisma');
  recordStatus.innerText = 'Prisma STT: Transcribing Indic speech...';

  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.wav');
  formData.append('language', selectedLang);
  formData.append('session_id', SESSION_ID);

  try {
    const response = await fetch('/api/process-voice', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) throw new Error("Failed to process voice pipeline");
    const result = await response.json();
    renderPipelineResults(result.pipeline);
  } catch (error) {
    console.error("Pipeline error:", error);
    recordStatus.innerText = 'Error processing speech. Please retry.';
  }
}

// Preset Simulator
async function simulatePreset(langCode, sampleText) {
  langSelect.value = langCode;
  appendChatMessage('farmer', sampleText);
  
  setPipelineStep('prisma');
  recordStatus.innerText = `Prisma STT: Transcribing "${sampleText.substring(0, 30)}..."`;

  try {
    setPipelineStep('evon');
    recordStatus.innerText = 'Evon Engine: Analyzing agricultural parameters...';

    const reasonRes = await fetch('/api/reason', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        text: sampleText, 
        language: langCode, 
        session_id: SESSION_ID 
      })
    });
    const reasoning = await reasonRes.json();

    setPipelineStep('market');
    recordStatus.innerText = 'Market Engine: Projecting SARIMA price trend & MSP comparison...';

    setPipelineStep('timbre');
    recordStatus.innerText = 'Timbre TTS: Synthesizing regional spoken advice...';

    const ttsRes = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: reasoning.advice_spoken, language: langCode })
    });
    const ttsData = await ttsRes.json();

    renderPipelineResults({
      step1_prisma_stt: { transcript: sampleText, language: langCode },
      step2_evon_reasoning: reasoning,
      step3_timbre_tts: ttsData
    }, false);
  } catch (err) {
    console.error("Preset simulation error:", err);
    recordStatus.innerText = 'Simulation failed. Check console.';
  }
}

// Render Results
function renderPipelineResults(pipeline, shouldAppendUser = true) {
  const stt = pipeline.step1_prisma_stt;
  const evon = pipeline.step2_evon_reasoning;
  const tts = pipeline.step3_timbre_tts;

  if (shouldAppendUser && stt.transcript) {
    appendChatMessage('farmer', stt.transcript);
  }

  // 1. Bot response bubble
  appendChatMessage('assistant', evon.advice_spoken);

  // 2. Extracted Entities
  entityCrop.innerText = evon.crop || 'Not Specified';
  entityLand.innerText = evon.landholding || 'Not Specified';
  entityIssue.innerText = evon.core_issue || 'General Inquiry';
  entityUrgency.innerText = evon.detected_urgency || 'NORMAL';

  // 3. Market Intelligence HUD Update
  const market = evon.market_intelligence;
  if (market) {
    mandiDecisionBadge.innerText = market.decision_code === "HOLD" ? "HOLD STOCK" : (market.decision_code === "MSP_CENTRE" ? "SELL AT MSP" : "SELL NOW");
    statMsp.innerText = `₹${market.msp_per_quintal.toLocaleString()}`;
    statMandi.innerText = `₹${market.current_mandi_avg.toLocaleString()}`;
    statForecast.innerText = `₹${market.forecast_3_months.toLocaleString()} (+${market.expected_growth_pct}%)`;
    marketAdvisoryText.innerText = `${market.crop} Advisory: ${market.recommendation}. ${market.storage_advisory}`;
  }

  // 4. Scheme Card
  const scheme = evon.matched_scheme;
  if (scheme) {
    schemeTitle.innerText = scheme.name;
    eligibilityTag.innerText = evon.eligibility_verdict || 'Eligible';
    schemeBenefit.innerText = scheme.benefit;
  }

  // 5. Action Plan Steps
  planList.innerHTML = '';
  if (evon.three_step_plan && evon.three_step_plan.length) {
    evon.three_step_plan.forEach(step => {
      const stepDiv = document.createElement('div');
      stepDiv.className = 'action-step-item';
      stepDiv.innerText = step;
      planList.appendChild(stepDiv);
    });
  }

  // 6. Timbre Voice Audio Playback
  if (tts.audio_base64) {
    const audioSrc = `data:${tts.mime_type || 'audio/wav'};base64,${tts.audio_base64}`;
    ttsAudioPlayer.src = audioSrc;
    ttsAudioPlayer.play().catch(e => console.log("Auto-play permission:", e));
    audioStatusText.innerText = `Playing voice advice (${tts.voice || 'Indic Voice'}) via Gnani Timbre`;
  }

  setPipelineStep('done');
  recordStatus.innerText = 'Ready for next turn. Speak again or choose a scenario.';
}
