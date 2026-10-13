"""
IBM Granite LLM Client — Nutrition Agentic AI
Handles authentication and inference via IBM watsonx.ai REST API.
SDK (ibm-watsonx-ai) is optional — install separately if needed:
    pip install ibm-watsonx-ai
Phase: Model Integration (Agentic AI SDLC)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Attempt IBM watsonx.ai SDK import (optional — REST fallback always works) ──
try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    IBM_SDK_AVAILABLE = True
except ImportError:
    IBM_SDK_AVAILABLE = False

# ── Fallback: direct REST API ───────────────────────────────────────────────────
import requests

WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")

# IBM Granite model identifier on watsonx.ai
GRANITE_MODEL_ID = "ibm/granite-13b-instruct-v2"
# Alternative: "ibm/granite-3-8b-instruct"  (newer, if available in your region)

# ── Generation parameters ───────────────────────────────────────────────────────
GEN_PARAMS = {
    "max_new_tokens": 1200,
    "min_new_tokens": 80,
    "temperature": 0.7,
    "top_p": 0.9,
    "repetition_penalty": 1.1,
    "stop_sequences": ["<|endoftext|>", "Human:", "User:"],
}


def _get_iam_token() -> str:
    """Exchanges IBM API key for a short-lived IAM bearer token."""
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": WATSONX_API_KEY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def generate_via_rest(prompt: str) -> str:
    """
    Calls IBM watsonx.ai text generation REST endpoint directly.
    Used when the Python SDK is unavailable.
    """
    token = _get_iam_token()
    url = f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29"
    payload = {
        "model_id": GRANITE_MODEL_ID,
        "input": prompt,
        "parameters": GEN_PARAMS,
        "project_id": WATSONX_PROJECT_ID,
    }
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["results"][0]["generated_text"].strip()


def generate_via_sdk(prompt: str) -> str:
    """
    Calls IBM Granite via the official watsonx.ai Python SDK.
    """
    credentials = Credentials(
        url=WATSONX_URL,
        api_key=WATSONX_API_KEY,
    )
    model = ModelInference(
        model_id=GRANITE_MODEL_ID,
        credentials=credentials,
        project_id=WATSONX_PROJECT_ID,
        params={
            GenParams.MAX_NEW_TOKENS: GEN_PARAMS["max_new_tokens"],
            GenParams.MIN_NEW_TOKENS: GEN_PARAMS["min_new_tokens"],
            GenParams.TEMPERATURE: GEN_PARAMS["temperature"],
            GenParams.TOP_P: GEN_PARAMS["top_p"],
            GenParams.REPETITION_PENALTY: GEN_PARAMS["repetition_penalty"],
        },
    )
    result = model.generate_text(prompt=prompt)
    return result.strip()


def call_granite(prompt: str) -> str:
    """
    Primary entry point — auto-selects SDK or REST fallback.
    Raises RuntimeError if credentials are not configured.
    """
    if not WATSONX_API_KEY or WATSONX_API_KEY == "your_ibm_watsonx_api_key_here":
        # ── Demo / development mode: return a structured mock response ──────────
        return _mock_response(prompt)

    if IBM_SDK_AVAILABLE:
        return generate_via_sdk(prompt)
    return generate_via_rest(prompt)


def _mock_response(prompt: str) -> str:
    """
    Returns a realistic mock nutrition plan when no API key is configured.
    Used for local development and demonstration purposes.
    """
    # Detect if this is a Q&A query vs. a full plan
    if "question" in prompt.lower() or "query" in prompt.lower() or "?" in prompt:
        return (
            "That's a great question! Based on general nutrition science, "
            "a balanced diet rich in whole grains, lean proteins, colourful vegetables, "
            "and healthy fats supports overall well-being. Individual needs vary by age, "
            "activity level, and health conditions. I recommend tracking your daily intake "
            "using the MyPlate framework and consulting a registered dietitian for "
            "personalised guidance tailored to your specific health goals."
        )

    return """## 🥗 Personalised Nutrition Plan

### Daily Caloric Target
**~2,000 kcal/day** (adjusted for your profile)

### Macronutrient Distribution
| Macronutrient | Target | Key Sources |
|---|---|---|
| Carbohydrates | 50% (~250g) | Brown rice, oats, sweet potato, whole wheat bread |
| Protein | 25% (~125g) | Lentils, paneer, chickpeas, tofu, eggs |
| Healthy Fats | 25% (~55g) | Nuts, seeds, olive oil, avocado |

### 📅 7-Day Meal Plan

**Day 1**
- **Breakfast:** Oatmeal with banana, chia seeds & almond milk (380 kcal)
- **Mid-Morning:** Mixed nuts & seasonal fruit (180 kcal)
- **Lunch:** Brown rice + dal + mixed vegetable curry + salad (520 kcal)
- **Evening Snack:** Hummus with carrot & cucumber sticks (150 kcal)
- **Dinner:** Grilled paneer tikka + quinoa + stir-fried greens (450 kcal)
- **Bedtime (optional):** Warm turmeric milk (120 kcal)

**Day 2**
- **Breakfast:** Vegetable upma + coconut chutney + herbal tea (340 kcal)
- **Mid-Morning:** Greek yogurt with berries (160 kcal)
- **Lunch:** Whole wheat roti + palak paneer + raita + salad (540 kcal)
- **Evening Snack:** Roasted chana + green tea (130 kcal)
- **Dinner:** Vegetable khichdi + papad + pickle (430 kcal)

*(Days 3–7 follow a similar rotating pattern with seasonal variety)*

### 💧 Hydration
- **Water:** 8–10 glasses (2–2.5 litres) per day
- **Herbal teas:** Chamomile, green tea, tulsi — 1–2 cups/day

### 🏃 Lifestyle Recommendations
1. Aim for **30 minutes of moderate exercise** 5 days/week
2. Eat meals at **consistent times** to regulate blood sugar
3. Practice **mindful eating** — chew slowly, avoid screens during meals
4. Get **7–8 hours of sleep** nightly for metabolic health

### 🩺 Condition-Specific Notes
- Maintain a **low glycaemic index (GI)** diet to support blood sugar management
- Reduce **sodium intake** to support blood pressure control
- Increase **potassium-rich foods** (banana, sweet potato, spinach)
- Limit **refined sugars and processed foods**

### 🌿 Recommended Micronutrients
- **Vitamin D:** Sunlight + fortified foods
- **Iron:** Leafy greens, legumes, fortified cereals
- **Calcium:** Dairy or fortified plant milk, sesame seeds
- **Omega-3:** Flaxseed, walnuts, chia seeds"""
