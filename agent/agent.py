"""
Nutrition Agent — Core Orchestration Layer
Implements the Agentic AI SDLC loop: Perceive → Plan → Act → Reflect → Respond
Phase: Agent Orchestration (Agentic AI SDLC)
"""

import os
import json
import re
import datetime
from pathlib import Path

from .granite_client import call_granite
from .guardrails import (
    check_input_safety,
    check_output_safety,
    validate_user_profile,
    append_disclaimer,
)
from .prompts import (
    build_nutrition_plan_prompt,
    build_query_prompt,
    build_meal_swap_prompt,
)

PLANS_DIR = Path(__file__).parent.parent / "plans"
PLANS_DIR.mkdir(exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY  (Agentic AI: tool-use pattern)
# ══════════════════════════════════════════════════════════════════════════════

class NutritionTools:
    """
    Collection of deterministic tools the agent can call without LLM inference.
    These represent the 'Act' phase of the perceive-plan-act loop.
    """

    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
        """Calculates BMI and returns category."""
        if height_cm <= 0:
            return {"error": "Invalid height"}
        bmi = weight_kg / ((height_cm / 100) ** 2)
        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25.0:
            category = "Normal weight"
        elif bmi < 30.0:
            category = "Overweight"
        else:
            category = "Obese"
        return {"bmi": round(bmi, 1), "category": category}

    @staticmethod
    def calculate_tdee(age: int, gender: str, weight_kg: float,
                       height_cm: float, activity_level: str) -> dict:
        """
        Calculates Total Daily Energy Expenditure (TDEE) using
        Mifflin-St Jeor equation with activity multiplier.
        """
        gender = gender.lower()
        if gender in ("male", "m"):
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

        multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very active": 1.9,
        }
        multiplier = multipliers.get(activity_level.lower(), 1.55)
        tdee = bmr * multiplier
        return {
            "bmr": round(bmr),
            "tdee": round(tdee),
            "activity_multiplier": multiplier,
        }

    @staticmethod
    def get_nutrient_rda(age: int, gender: str) -> dict:
        """Returns approximate RDA values for key nutrients."""
        gender = gender.lower()
        is_male = gender in ("male", "m")

        # Simplified RDA table (ICMR / WHO guidelines)
        return {
            "calories_kcal": 2400 if is_male else 1900,
            "protein_g": 60 if is_male else 55,
            "carbs_g": 300 if is_male else 230,
            "fat_g": 65 if is_male else 50,
            "fiber_g": 30 if is_male else 25,
            "calcium_mg": 1000,
            "iron_mg": 17 if is_male else 21,
            "vitamin_c_mg": 40,
            "vitamin_d_iu": 600,
            "water_ml": 3700 if is_male else 2700,
        }

    @staticmethod
    def save_plan_to_markdown(plan_text: str, profile: dict) -> str:
        """
        Saves the nutrition plan as a Markdown file.
        Returns the file path.
        """
        name_slug = re.sub(r"[^\w]", "_", profile.get("name", "user").lower())
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nutrition_plan_{name_slug}_{timestamp}.md"
        filepath = PLANS_DIR / filename

        header = f"""# Nutrition Plan — {profile.get('name', 'User')}
**Generated:** {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}  
**Powered by:** IBM Granite LLM via watsonx.ai  

---

"""
        full_content = header + plan_text
        filepath.write_text(full_content, encoding="utf-8")
        return str(filepath)


# ══════════════════════════════════════════════════════════════════════════════
# AGENT ORCHESTRATION
# ══════════════════════════════════════════════════════════════════════════════

class NutritionAgent:
    """
    Core agentic AI orchestrator.

    Agentic AI SDLC Phases implemented:
    1. Requirements & Ethics Review  → guardrails.py
    2. Data Collection               → profile validation
    3. Planning                      → prompt engineering
    4. Tool Use / Action             → NutritionTools
    5. LLM Inference                 → granite_client.py
    6. Reflection & Safety Check     → output guardrails
    7. Response & Persistence        → save to .md, return JSON
    """

    def __init__(self):
        self.tools = NutritionTools()
        self.conversation_history: list[dict] = []

    # ── Phase 1 & 2: Perceive + Validate ──────────────────────────────────────
    def perceive(self, profile: dict) -> dict:
        """Validates and enriches the user profile."""
        valid, msg = validate_user_profile(profile)
        if not valid:
            return {"ok": False, "error": msg}

        # Enrich with calculated fields if weight/height provided
        enriched = dict(profile)
        try:
            w = float(profile.get("weight_kg", 0))
            h = float(profile.get("height_cm", 0))
            if w > 0 and h > 0:
                enriched["bmi_data"] = self.tools.calculate_bmi(w, h)

            age = int(profile.get("age", 25))
            gender = profile.get("gender", "female")
            activity = profile.get("activity_level", "moderate")
            if w > 0 and h > 0:
                enriched["tdee_data"] = self.tools.calculate_tdee(age, gender, w, h, activity)

            enriched["rda_data"] = self.tools.get_nutrient_rda(age, gender)
        except (ValueError, TypeError):
            pass  # optional enrichment — graceful degradation

        return {"ok": True, "enriched_profile": enriched}

    # ── Phase 3 & 4: Plan + Act ───────────────────────────────────────────────
    def plan_and_act(self, enriched_profile: dict) -> str:
        """Constructs the prompt and calls the LLM."""
        prompt = build_nutrition_plan_prompt(enriched_profile)
        response = call_granite(prompt)
        return response

    # ── Phase 5: Reflect ──────────────────────────────────────────────────────
    def reflect(self, llm_response: str) -> tuple[bool, str]:
        """Post-generation safety check."""
        return check_output_safety(llm_response)

    # ── Phase 6: Respond ─────────────────────────────────────────────────────
    def respond(self, plan_text: str, profile: dict) -> dict:
        """Appends disclaimer, saves .md file, returns structured result."""
        full_plan = append_disclaimer(plan_text)
        md_path = self.tools.save_plan_to_markdown(full_plan, profile)
        return {
            "success": True,
            "plan": full_plan,
            "md_file": md_path,
            "profile_summary": {
                "name": profile.get("name"),
                "age": profile.get("age"),
                "diet": profile.get("diet_preference"),
                "goal": profile.get("health_goal"),
                "bmi": profile.get("bmi_data", {}).get("bmi"),
                "bmi_category": profile.get("bmi_data", {}).get("category"),
                "tdee": profile.get("tdee_data", {}).get("tdee"),
                "rda": profile.get("rda_data"),
            },
        }

    # ── Master run method ─────────────────────────────────────────────────────
    def generate_plan(self, profile: dict) -> dict:
        """
        Full agentic pipeline:
        Perceive → Plan → Act → Reflect → Respond
        """
        # Step 1: Perceive & validate
        perception = self.perceive(profile)
        if not perception["ok"]:
            return {"success": False, "error": perception["error"]}

        enriched = perception["enriched_profile"]

        # Step 2: Plan & generate
        try:
            raw_plan = self.plan_and_act(enriched)
        except Exception as e:
            return {"success": False, "error": f"LLM generation failed: {str(e)}"}

        # Step 3: Reflect (output safety)
        safe, checked_plan = self.reflect(raw_plan)
        if not safe:
            return {"success": False, "error": checked_plan}

        # Step 4: Respond
        return self.respond(checked_plan, enriched)

    # ── Q&A Agent (conversational mode) ──────────────────────────────────────
    def answer_query(self, question: str, user_context: dict = None) -> dict:
        """
        Handles free-form nutrition Q&A with full guardrail pipeline.
        Maintains lightweight conversation history for context continuity.
        """
        # Input safety check
        safe, msg = check_input_safety(question)
        if not safe:
            return {"success": False, "error": msg}

        # Build prompt
        prompt = build_query_prompt(question, context=user_context)

        # Inference
        try:
            raw_answer = call_granite(prompt)
        except Exception as e:
            return {"success": False, "error": f"Query failed: {str(e)}"}

        # Output safety
        safe, checked_answer = self.reflect(raw_answer)
        if not safe:
            return {"success": False, "error": checked_answer}

        # Store in conversation history (last 10 turns)
        self.conversation_history.append({"q": question, "a": checked_answer})
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)

        return {"success": True, "answer": checked_answer}

    # ── Meal swap tool ────────────────────────────────────────────────────────
    def suggest_meal_swap(self, meal: str, reason: str, profile: dict) -> dict:
        """Suggests alternative meals using the LLM."""
        safe, msg = check_input_safety(f"{meal} {reason}")
        if not safe:
            return {"success": False, "error": msg}

        prompt = build_meal_swap_prompt(meal, reason, profile)
        try:
            raw = call_granite(prompt)
        except Exception as e:
            return {"success": False, "error": str(e)}

        safe, checked = self.reflect(raw)
        if not safe:
            return {"success": False, "error": checked}

        return {"success": True, "suggestions": checked}
