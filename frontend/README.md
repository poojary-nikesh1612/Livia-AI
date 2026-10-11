# Livia AI — Mobile & Web Frontend (Expo + TypeScript)

Multimodal, voice-first agricultural advisory client for **Livia AI — A Multilingual AI Framework for Rice Leaf Disease Diagnosis and Advisory**. Farmers can interact via text, voice recordings, and up to 5 crop leaf images in **English (`en`)** or **Kannada (`kn`)**, backed by the FastAPI + LangGraph workflow in `../backend`.

---

## 1. Prerequisites

- **Node.js**: v20 LTS or v22+
- **npm**: v10+
- **Expo Go** (for physical Android/iOS devices) or Android Studio Emulator / Xcode Simulator / Web Browser
- **Running FastAPI Backend** (`../backend`) connected to PostgreSQL (Supabase)

---

## 2. Installation

```bash
cd frontend
npm install
```

> **Note on Dependency Alignment (Expo SDK 57):**
> All packages in `package.json` are aligned with Expo SDK 57 (`expo@~57.0.27`, `react@19.2.3`, `react-dom@19.2.3`, `react-native@0.86.3`, `expo-audio@~57.0.5`, `expo-file-system@~57.0.7`, `expo-image-picker@~57.0.20`). A `postinstall` script (`scripts/patch-metro.js`) automatically patches Metro's `package.json` subpath exports for Node.js 22+ compatibility.

---

## 3. Environment Configuration (`.env`)

Copy `.env.example` to `.env` inside `frontend/`:

```bash
cp .env.example .env
```

Configure the two public variables:

```ini
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
EXPO_PUBLIC_USER_ID=00000000-0000-0000-0000-000000000000
```

### Choosing `EXPO_PUBLIC_API_BASE_URL` by Target Platform

| Target Environment | Recommended `EXPO_PUBLIC_API_BASE_URL` |
|---|---|
| **Web Browser (`npx expo start --web`)** | `http://127.0.0.1:8000/api/v1` or `http://localhost:8000/api/v1` |
| **Android Emulator** | `http://10.0.2.2:8000/api/v1` |
| **iOS Simulator** | `http://localhost:8000/api/v1` |
| **Physical Device (Expo Go on LAN)** | `http://<YOUR_PC_LAN_IP>:8000/api/v1` (e.g. `http://192.168.1.42:8000/api/v1`) |
| **Deployed Production Backend** | `https://your-domain.example.com/api/v1` |

### Obtaining a Valid `EXPO_PUBLIC_USER_ID`

The backend `GET /api/v1/chat/history` and `POST /api/v1/chat` endpoints require a valid UUID corresponding to a user row in the PostgreSQL `users` table (`backend/schemas/db_models.py`). Use an existing `user_id` from your `users` table in Supabase/PostgreSQL.

---

## 4. Starting the Backend & Frontend

### Start the FastAPI Backend

From the `backend/` directory:

```bash
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

*(Binding to `0.0.0.0` ensures the server is reachable from Android emulators and physical devices on the same Wi-Fi network.)*

### Start the Expo Application

From the `frontend/` directory:

```bash
cd ../frontend
npx expo start
```

- Press **`w`** to open in a web browser
- Press **`a`** to open on an Android emulator
- Press **`i`** to open on an iOS simulator
- Scan the QR code with **Expo Go** on a physical device

---

## 5. Architecture & Key Features

- **Zero External Image Assets**: All branding (the Livia AI leaf-and-soundwave emblem) and control icons (camera, gallery, microphone, speaker, soundwaves, send arrow) are built purely with React Native Views/CSS.
- **LangGraph Thread Lifecycle (`ChatScreen.tsx`)**:
  - Automatically generates a new UUID `thread_id` when starting a new diagnostic flow.
  - Preserves and reuses the active `thread_id` while `is_flow_complete === false` (such as when Livia AI asks clarifying questions about crop age or symptoms).
  - Starts a fresh `thread_id` on the next query once `is_flow_complete === true`, or when the user taps **+ New** in the header.
- **Audio Recording & Playback (`useAudioRecorder.ts`, `useAudioPlayer.ts`)**:
  - Uses `expo-audio` (replacing deprecated `expo-av`) across Android, iOS, and Web.
  - Fresh assistant responses automatically play `ai_response_audio_base64` when available.
  - Historical assistant messages stream MP3 audio on demand via `POST /api/v1/voice/stream` in the currently selected language (`en` or `kn`) and cache the resulting file locally.
  - Enforces single-instance playback so multiple messages never play simultaneously.
- **Crop Image Selection (`InputBar.tsx`, `ImagePreview.tsx`, `utils/images.ts`)**:
  - Supports camera capture and multi-select gallery picking up to **5 images** per message.
  - Strips `data:image/...;base64,` prefixes before sending to `POST /api/v1/chat`.

---

## 6. Known Backend Notes & Troubleshooting

- **History Thread Restoration**: `GET /api/v1/chat/history` returns `{ role, display_content, images }` and does not expose the last LangGraph `thread_id` or `is_flow_complete` checkpoint state. Therefore, opening the app starts ready for a new diagnostic thread while displaying full past conversation history.
- **Inbound Voice Format**: `backend/services/voice_input.py` sends `audio_base64` to Sarvam AI STT (`saaras:v3`). Ensure `SARVAM_API_KEY` is configured in `backend/.env` when testing voice input.
- **Local HTTP Cleartext Traffic**: During local development over `http://`, Android and iOS allow local network requests in Expo Go / debug builds. For production builds, always use an `https://` backend URL.

