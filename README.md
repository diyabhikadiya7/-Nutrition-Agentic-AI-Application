# 🥗 Nutrition Agentic AI Application

> **Powered by IBM Granite LLM via watsonx.ai**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-green)](https://flask.palletsprojects.com/)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-blue)](https://www.ibm.com/watsonx)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Overview

**NutriAI** is a full-stack **Agentic AI web application** that generates personalised **7-day nutrition plans** using IBM's **Granite large language model** hosted on **watsonx.ai**. Built following the complete Agentic AI SDLC, the system incorporates guardrails, ethical AI principles, and a HAM (Helpful, Accurate, Mindful) communication framework.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 IBM Granite LLM | Powered by `ibm/granite-13b-instruct-v2` on watsonx.ai |
| 🥗 Personalised Plans | 7-day meal plans tailored to age, diet, medical history & location |
| 🩺 Medical Awareness | Adapts plans for diabetes, blood pressure, thyroid, PCOS, etc. |
| 🛡️ AI Guardrails | Input & output safety checks, harmful content filtering |
| ⚕️ HAM Tone | Helpful, Accurate, Mindful — respectful, empathetic responses |
| 💬 Agentic Q&A | Conversational nutrition assistant with context memory |
| 💾 Save as .md | Auto-saves each plan as a Markdown file |
| ⬇️ Download | Download nutrition plans directly from the browser |
| 📊 BMI & TDEE | Real-time BMI calculator and TDEE estimation |
| 🌐 Demo Mode | Works without an API key using realistic mock responses |

---

## 🏗️ Agentic AI SDLC Phases

```
Phase 1: Requirements & Ethics Review   → guardrails.py
Phase 2: Data Collection & Validation   → agent.py (perceive)
Phase 3: Prompt Engineering             → prompts.py
Phase 4: Tool Use / Action              → NutritionTools class
Phase 5: LLM Inference                  → granite_client.py
Phase 6: Reflection & Safety Check      → output guardrails
Phase 7: Response & Persistence         → save to .md, return JSON
```

---

## 📁 Project Structure

```
nutrition_ai/
├── app.py                  ← Flask REST API server
├── requirements.txt        ← Python dependencies
├── .env.example            ← Environment variable template
├── run.bat                 ← Windows one-click launcher
├── .gitignore              ← Git ignore rules
├── README.md               ← This file
│
├── agent/
│   ├── __init__.py
│   ├── agent.py            ← Core agentic loop (Perceive→Plan→Act→Reflect→Respond)
│   ├── granite_client.py   ← IBM Granite LLM client (SDK + REST fallback)
│   ├── guardrails.py       ← Safety checks, HAM tone, medical disclaimer
│   └── prompts.py          ← Structured prompt templates
│
├── static/
│   ├── index.html          ← Single-page web application
│   ├── style.css           ← Responsive UI stylesheet
│   └── app.js              ← Frontend logic
│
└── plans/                  ← Generated .md nutrition plans (auto-created)
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** — [Download here](https://www.python.org/downloads/) (check *"Add Python to PATH"*)
- **Git** — [Download here](https://git-scm.com/downloads)
- **IBM watsonx.ai API key** *(optional — app runs in Demo Mode without it)*

---

### Option 1: Windows One-Click Launcher

```bat
Double-click run.bat
```

This will automatically:
1. Check Python installation
2. Create a virtual environment
3. Install all dependencies
4. Copy `.env.example` → `.env`
5. Start the Flask server
6. Open `http://localhost:5000` in your browser

---

### Option 2: Manual Setup (All Platforms)

```bash
# 1. Clone the repository
git clone https://github.com/diyabhikadiya7/-Nutrition-Agentic-AI-Application.git
cd -Nutrition-Agentic-AI-Application/nutrition_ai

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env        # Windows
cp .env.example .env          # macOS / Linux

# 5. Edit .env and add your IBM watsonx.ai credentials
#    (see Configuration section below)

# 6. Run the application
python app.py

# 7. Open browser at http://localhost:5000
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```env
# IBM watsonx.ai credentials
WATSONX_API_KEY=your_ibm_watsonx_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Flask settings
FLASK_SECRET_KEY=nutrition-ai-secret-key-change-in-production
FLASK_DEBUG=False
PORT=5000
```

### How to get IBM watsonx.ai credentials

1. Sign up at [IBM Cloud](https://cloud.ibm.com)
2. Create a **watsonx.ai** project
3. Navigate to **IAM → API Keys** and generate an API key
4. Copy your **Project ID** from the watsonx.ai dashboard

> **💡 Demo Mode:** Without an API key, the app automatically falls back to realistic mock responses — perfect for testing the UI and workflow.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/generate-plan` | Generate a personalised 7-day nutrition plan |
| `POST` | `/api/query` | Agentic Q&A — answer nutrition questions |
| `POST` | `/api/meal-swap` | Suggest meal alternatives |
| `POST` | `/api/bmi` | Calculate BMI |
| `GET` | `/api/plans` | List all saved plans |
| `GET` | `/api/download-plan/<filename>` | Download a saved `.md` plan |

### Example: Generate Plan

```bash
curl -X POST http://localhost:5000/api/generate-plan \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Priya Sharma",
    "age": 30,
    "gender": "female",
    "diet_preference": "veg",
    "medical_history": "None",
    "activity_level": "moderate",
    "health_goal": "weight loss",
    "location_city": "Mumbai",
    "location_country": "India",
    "weight_kg": 65,
    "height_cm": 162
  }'
```

---

## 🛡️ Guardrails & AI Ethics

- **Input Guardrails:** Blocks harmful queries (crash diets, medication overrides, unrealistic claims)
- **Output Guardrails:** Post-generation safety scan on all LLM responses
- **Medical Disclaimer:** Automatically appended to every generated plan
- **HAM Tone:** Every prompt enforces Helpful, Accurate, Mindful communication
- **No Diagnosis:** Explicitly avoids medical diagnoses and medication changes
- **Age Safety:** Validates age range (5–110) before processing

---

## 🧰 Technology Stack

| Layer | Technology |
|---|---|
| LLM | IBM Granite 13B Instruct v2 (watsonx.ai) |
| Backend | Python 3.9+ / Flask 3.0 |
| Frontend | Vanilla HTML5 / CSS3 / JavaScript |
| API | RESTful JSON API with Flask-CORS |
| Environment | python-dotenv |
| Output Format | Markdown (`.md`) files |

---

## ⚠️ Medical Disclaimer

> This application is for **informational purposes only** and does **NOT** constitute medical advice. Always consult a **registered dietitian** or **qualified healthcare provider** before making significant dietary changes, especially if you have an existing medical condition.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

*NutriAI — Nutrition Agentic AI | IBM Granite | watsonx.ai*
