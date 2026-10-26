# AI Phone Translator 🇬🇧 ↔ 🇯🇵

A real-time AI Phone Translator designed to help English-speaking and Japanese-speaking people communicate over phone calls.

**Tech Stack:** Python, FastAPI, NLLB, Twilio, ngrok
**Environment:** macOS (Apple Silicon), `uv`

> **Current Status:** The translation backend and initial voice webhooks are implemented and tested using simulated HTTP requests. Real Twilio calls and the complete live translation flow are not yet verified.

---

## 🎯 Project Goal

Build a phone-call application that allows two people to speak different languages:

- Person A speaks English; Person B hears Japanese.
- Person B speaks Japanese; Person A hears English.

### Target Workflow

```text
Person A speaks English
          ↓
Twilio Speech Recognition
          ↓
FastAPI Webhook
          ↓
NLLB Translation (English → Japanese)
          ↓
Twilio Speech Output
          ↓
Person B hears Japanese
```

The reverse direction will follow the same process.

---

## 🏗️ Architecture

### Translation Layers

```text
FastAPI Route
      ↓
Translation Service
      ↓
Translation Provider (Interface)
      ↓
NLLB Translation Provider
      ↓
NLLB Model
```

| Component | Responsibility |
|---|---|
| FastAPI Route | Receives API requests |
| Translation Service | Coordinates the translation workflow |
| Translation Provider | Defines the common `translate()` contract |
| NLLB Provider | Implements translation using NLLB |
| NLLB Model | Performs the actual translation |

**Remember:** The service coordinates, the interface defines the contract, and the provider performs the translation.

This separation makes it easier to replace a model without rewriting the service.

### Phone-Call Architecture

```text
Caller
   ↓
Twilio
   ↓
Public HTTPS URL (ngrok)
   ↓
FastAPI on localhost:8000
   ↓
Translation Provider
   ↓
TwiML Response
   ↓
Twilio Speaks the Translation
```

> **Important:** This is the intended architecture. The complete real-time phone-call flow has not yet been verified.

---

## 📊 Current Project Status

| Component | Status |
|---|---|
| Python project and `uv` environment | ✅ Set up |
| FastAPI backend | ✅ Implemented |
| Translation service | ✅ Implemented |
| Translation provider interface | ✅ Implemented |
| MarianMT provider | ⚠️ Implemented; poor translation results |
| NLLB provider | ✅ Implemented |
| English → Japanese API | ✅ Tested |
| Japanese → English API | ✅ Tested |
| `/voice/incoming` endpoint | ✅ Implemented |
| Twilio speech-recognition instructions | ✅ Generated |
| `/voice/translate` endpoint | ✅ Tested with simulated text |
| ngrok public tunnel | ✅ Tested while online |
| Real Twilio phone call | ⏳ Not verified |
| Actual speech recognition during a call | ⏳ Not verified |
| Complete two-way conversation | ⏳ Remaining |

---

## 📁 Project Structure

The expected structure based on the current implementation is:

```text
ai-phone-translator/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes/
│   │       ├── translation.py
│   │       └── voice.py
│   ├── schemas/
│   │   └── translation.py
│   ├── services/
│   │   ├── translation_service.py
│   │   └── translation_provider.py
│   └── integrations/
│       └── llm/
│           ├── marian_translation_provider.py
│           └── nllb_translation_provider.py
├── scripts/
│   └── compare_translation_models.py
├── tests/
├── pyproject.toml
└── uv.lock
```

### Important Files

- `app/main.py` — Creates the FastAPI application and registers routes.
- `app/api/routes/translation.py` — Provides the translation API.
- `app/api/routes/voice.py` — Contains the incoming-call and speech-translation endpoints.
- `app/services/translation_service.py` — Coordinates translation.
- `app/services/translation_provider.py` — Defines the provider contract.
- `app/integrations/llm/nllb_translation_provider.py` — Implements NLLB translation.

> Check the actual files when resuming, as this structure may need adjustment.

---

## 🤖 Translation Model

### Selected Model

```text
facebook/nllb-200-distilled-600M
```

| Language | NLLB Code |
|---|---|
| English | `eng_Latn` |
| Japanese | `jpn_Jpan` |

The provider uses Apple Silicon MPS when available and falls back to CPU.

It loads and reuses the model and uses inference mode for translation.

### Translation Quality

MarianMT produced several incorrect translations, so we tested NLLB.

NLLB performed better on some simple phrases, but its quality is not yet reliable enough for real conversations.

For example:

Input:

```text
Hello, how are you?
```

One observed output:

```text
こんにちは こんにちは
```

This does not preserve the full meaning.

**Next:** Test realistic sentences in both directions and measure translation latency.

---

## 📞 Voice Endpoints

### 1. `POST /voice/incoming`

This endpoint returns TwiML instructions for an incoming call.

Its current flow is intended to:

1. Play a welcome message.
2. Listen for English speech using Twilio's `Gather`.
3. Send recognized text to `/voice/translate`.
4. Play a fallback message if no speech is received.

The `Gather` action must use the current public HTTPS URL:

```text
https://YOUR-NGROK-URL/voice/translate?source=en
```

### 2. `POST /voice/translate`

This endpoint receives recognized speech, translates it, and returns TwiML.

Expected inputs:

- `SpeechResult` — Recognized text submitted as form data.
- `source` — Source language supplied in the query string.

The endpoint selects the target language, calls the NLLB provider, and returns a `Say` instruction.

> **Important:** We tested this endpoint with simulated form data. We have not verified that Twilio sends recognized speech during an actual call.

---

## 🚀 Running the Application

Run the commands from the project root.

### Terminal 1 — Start FastAPI

```bash
cd ~/Projects/ai-phone-translator
uv run uvicorn app.main:app --reload --port 8000
```

Keep this terminal open.

Wait for a message indicating that Uvicorn is running on port 8000.

### Terminal 2 — Start ngrok

```bash
ngrok http 8000
```

Keep this terminal open and ensure the session is online.

ngrok creates a public HTTPS address that forwards requests to your local FastAPI server.

**Why do we need ngrok?**

Twilio cannot directly access `127.0.0.1:8000` on your Mac.

> **Important: ngrok URL**
>
> The free ngrok URL may change after restarting the tunnel.
>
> If it changes, update both:
>
> 1. The `Gather` action URL in `app/api/routes/voice.py`.
> 2. The incoming-call webhook URL in the Twilio Console.

---

## 🧪 Testing the Endpoints

### Test the Incoming-Call Endpoint

```bash
curl -X POST "http://127.0.0.1:8000/voice/incoming"
```

Expected result: XML containing the welcome message and a `Gather` instruction.

### Test Translation Locally

```bash
curl -X POST "http://127.0.0.1:8000/voice/translate?source=en" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "SpeechResult=Hello, how are you?"
```

Expected result: XML containing a Japanese translation inside a TwiML `Say` element.

### Test Translation Through ngrok

Replace `YOUR-NGROK-URL` with the current forwarding domain.

```bash
curl -X POST "https://YOUR-NGROK-URL/voice/translate?source=en" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "SpeechResult=Hello, how are you?"
```

A successful response confirms that the public tunnel reached FastAPI and the endpoint returned TwiML.

It does **not** prove that a real Twilio call works.

---

## 🔗 Twilio Setup and Current Limitations

The Twilio account is on a trial plan and has a US phone number.

The incoming-call webhook was configured under the number's Voice Configuration:

| Setting | Value |
|---|---|
| Handler | Webhook |
| URL | `https://YOUR-NGROK-URL/voice/incoming` |
| Method | HTTP POST |

Calling the US number from an Indian SIM resulted in an insufficient ISD balance message. We decided not to recharge just for testing.

Twilio call logs were empty during our checks.

**Remember:** `curl` requests do not create real Twilio call records.

### Current Conclusion

FastAPI and ngrok were verified using simulated requests.

However, the following remain unverified:

- Real Twilio call delivery.
- Actual speech recognition during a call.
- The complete two-way translation conversation.

---

## 🛠️ Next Steps

Follow this order when resuming development.

### Step 1 — Restart and Verify Services

Start FastAPI and ngrok and note the current public URL.

### Step 2 — Verify Callback URLs

Ensure that the `Gather` action and Twilio webhook use the current ngrok URL.

### Step 3 — Evaluate Translation Quality

Test realistic English → Japanese and Japanese → English sentences.

Record incorrect translations and inference time.

### Step 4 — Review Voice Endpoints

Verify form parsing, error handling, and public callback URLs.

### Step 5 — Verify Twilio Integration

Find a way to trigger or validate a real Twilio call without making an international call from the Indian SIM.

Simulated requests alone are insufficient.

### Step 6 — Complete Two-Way Conversation

Implement:

- Repeated conversation turns.
- English → Japanese translation.
- Japanese → English translation.
- Speech output.
- Correct routing of translated speech to the other caller.

### Step 7 — Improve Reliability

Add:

- Timeouts and controlled retries.
- Call-disconnect handling.
- WebSocket or session lifecycle management, if required by the selected architecture.
- Isolation between simultaneous calls.
- Latency measurements.

---

## ⚠️ Critical Reminders

1. A successful `curl` request does not prove that a real phone call works.
2. HTTP `200 OK` confirms request handling, not translation accuracy.
3. ngrok must remain online for the public URL to reach your local server.
4. The free ngrok URL may change after restarting.
5. NLLB output needs quality evaluation before live use.
6. A complete two-way call requires repeated conversation turns and correct routing — not just one translation endpoint.
7. Reuse the translation provider instead of loading the model for every request.

---

## 🔐 Security

An ngrok authentication token was pasted into a previous chat.

Treat it as exposed:

- Revoke or rotate it in your ngrok dashboard.
- Update the local ngrok configuration with the replacement token.
- Never share the replacement token or your Twilio Auth Token.
- Never commit secrets to GitHub.

---

## 📌 Resume Point

When continuing the project:

1. Inspect `app/api/routes/voice.py`.
2. Start FastAPI.
3. Start ngrok and check the current public URL.
4. Verify the callback URLs.
5. Evaluate translation quality.
6. Continue with live-call integration.

### Final Summary

The translation backend and initial webhook responses work with simulated requests.

The next major milestone is to verify an actual Twilio call and complete the real-time, bidirectional speech-translation flow.
