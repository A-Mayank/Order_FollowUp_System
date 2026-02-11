# AI-Assisted WhatsApp Order Follow-Up System

A production-ready MVP for automated B2C order follow-ups using WhatsApp, featuring AI personalization and sentiment analysis.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb)](https://www.mongodb.com/)
[![Twilio](https://img.shields.io/badge/Twilio-WhatsApp-F22F46?logo=twilio)](https://www.twilio.com/)

---

## 🚀 Overview

This system automates the post-purchase customer journey:
1.  **Instant Confirmation**: WhatsApp message sent immediately after order creation.
2.  **Payment Reminders**: Automated follow-ups at 15 minutes and 24 hours.
3.  **AI Personalization**: Messages are generated/refined using OpenAI or Gemini.
4.  **Sentiment Safeguard**: If a customer expresses negative sentiment, automation stops and an admin alert is created.
5.  **Admin Dashboard**: Full visibility into orders, message logs, and system alerts.

---

## 🛠️ Quick Start (Local Docker)

Running the entire stack locally is easiest with Docker:

```bash
docker-compose up --build
```
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📦 Cloud Deployment (Recommended)

### 1. Backend & Frontend (Render Unified Deployment)
We use a multi-stage Dockerfile to build both the React frontend and FastAPI backend into a single image.

1.  Create a new **Web Service** on [Render](https://render.com/).
2.  Connect your GitHub repository.
3.  Render will use the `render.yaml` and `Dockerfile` automatically.
4.  **Environment Variables**: Add all keys from `backend/.env` (see below).

### 2. Database (MongoDB Atlas)
1.  Create a free cluster on [MongoDB Atlas](https://www.mongodb.com/atlas).
2.  **Network Access**: Whitelist `0.0.0.0/0` to allow Render's dynamic IPs to connect.
3.  Copy your connection string and set it as `MONGODB_URI` in Render.

### 3. Twilio Webhook Configuration
Once your Render app is **Live**:
1.  Copy your Render URL (e.g., `https://your-app.onrender.com`).
2.  Go to [Twilio Console](https://console.twilio.com/) > Messaging > Sandbox Settings.
3.  Set the **"When a message comes in"** URL to:
    `https://your-app.onrender.com/api/webhooks/whatsapp`
4.  Method: **POST**.

---

## ⚙️ Configuration (.env)

| Variable | Description |
| :--- | :--- |
| `MONGODB_URI` | Connection string (Atlas or Local) |
| `TWILIO_ACCOUNT_SID` | Your Twilio SID |
| `TWILIO_AUTH_TOKEN` | Your Twilio Secret Token |
| `TWILIO_WHATSAPP_NUMBER` | Your Twilio number (e.g., `whatsapp:+14155238886`) |
| `AI_PROVIDER` | `openai` or `gemini` |
| `OPENAI_API_KEY` | (Required if using OpenAI) |
| `GEMINI_API_KEY` | (Required if using Gemini) |

---

## 🔧 Architecture

- **Backend**: FastAPI with Beanie ODM (MongoDB).
- **Background Jobs**: APScheduler runs the reminder sequences.
- **Frontend**: React 18 with Vite and Axios.
- **AI Service**: Unified interface for sentiment analysis and message generation.

---

## 📝 License
MIT License. Built for evaluation and demo purposes.
