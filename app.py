"""
Flask Backend — Nutrition Agentic AI
RESTful API server with agentic AI endpoints.
Phase: Deployment & Integration (Agentic AI SDLC)
"""

import os
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv

from agent import NutritionAgent

load_dotenv()

# ── App setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "nutrition-ai-dev-key")
CORS(app)

# Single agent instance (per-session state managed client-side via profile)
agent = NutritionAgent()

PLANS_DIR = Path(__file__).parent / "plans"
PLANS_DIR.mkdir(exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# STATIC / PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the main single-page application."""
    return send_from_directory("static", "index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)


# ══════════════════════════════════════════════════════════════════════════════
# API ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "Nutrition Agentic AI",
        "model": "IBM Granite (watsonx.ai)",
        "version": "1.0.0",
    })


@app.route("/api/generate-plan", methods=["POST"])
def generate_plan():
    """
    Generate a personalised nutrition plan.
    Expects JSON body with user profile fields.
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Sanitise string inputs
        profile = {
            "name": str(data.get("name", "")).strip(),
            "age": data.get("age", ""),
            "gender": str(data.get("gender", "female")).strip(),
            "diet_preference": str(data.get("diet_preference", "veg")).strip(),
            "medical_history": str(data.get("medical_history", "None")).strip(),
            "activity_level": str(data.get("activity_level", "moderate")).strip(),
            "health_goal": str(data.get("health_goal", "general wellness")).strip(),
            "location_city": str(data.get("location_city", "")).strip(),
            "location_country": str(data.get("location_country", "")).strip(),
            "allergies": str(data.get("allergies", "None")).strip(),
            "weight_kg": data.get("weight_kg", ""),
            "height_cm": data.get("height_cm", ""),
        }

        result = agent.generate_plan(profile)

        if result["success"]:
            # Extract just the filename for the download link
            md_path = result.get("md_file", "")
            result["md_filename"] = Path(md_path).name if md_path else ""
            return jsonify(result), 200
        else:
            return jsonify(result), 422

    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@app.route("/api/query", methods=["POST"])
def answer_query():
    """
    Agentic Q&A endpoint — answers user nutrition questions.
    """
    try:
        data = request.get_json(force=True)
        question = str(data.get("question", "")).strip()
        user_context = data.get("context", {})

        if not question:
            return jsonify({"success": False, "error": "Question is required"}), 400

        if len(question) > 1000:
            return jsonify({"success": False, "error": "Question too long (max 1000 chars)"}), 400

        result = agent.answer_query(question, user_context=user_context)
        return jsonify(result), 200 if result["success"] else 422

    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@app.route("/api/meal-swap", methods=["POST"])
def meal_swap():
    """
    Suggest alternative meals for a given meal + reason.
    """
    try:
        data = request.get_json(force=True)
        meal = str(data.get("meal", "")).strip()
        reason = str(data.get("reason", "preference")).strip()
        profile = data.get("profile", {})

        if not meal:
            return jsonify({"success": False, "error": "Meal is required"}), 400

        result = agent.suggest_meal_swap(meal, reason, profile)
        return jsonify(result), 200 if result["success"] else 422

    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@app.route("/api/download-plan/<filename>", methods=["GET"])
def download_plan(filename):
    """Download a previously generated nutrition plan as .md file."""
    # Security: only allow filenames matching expected pattern
    import re
    if not re.match(r"^nutrition_plan_[\w]+_\d{8}_\d{6}\.md$", filename):
        return jsonify({"error": "Invalid filename"}), 400

    filepath = PLANS_DIR / filename
    if not filepath.exists():
        return jsonify({"error": "File not found"}), 404

    return send_file(
        str(filepath),
        as_attachment=True,
        download_name=filename,
        mimetype="text/markdown",
    )


@app.route("/api/plans", methods=["GET"])
def list_plans():
    """List all saved nutrition plans."""
    plans = []
    for f in sorted(PLANS_DIR.glob("*.md"), reverse=True):
        plans.append({
            "filename": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
            "modified": f.stat().st_mtime,
        })
    return jsonify({"plans": plans[:20]})  # return latest 20


@app.route("/api/bmi", methods=["POST"])
def calculate_bmi():
    """Quick BMI calculation endpoint."""
    from agent.agent import NutritionTools
    try:
        data = request.get_json(force=True)
        weight = float(data.get("weight_kg", 0))
        height = float(data.get("height_cm", 0))
        if weight <= 0 or height <= 0:
            return jsonify({"error": "Invalid weight or height"}), 400
        result = NutritionTools.calculate_bmi(weight, height)
        return jsonify(result)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric values"}), 400


# ══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    mode_label = "DEBUG" if debug else "PRODUCTION"
    print(f"Nutrition Agentic AI -- IBM Granite LLM")
    print(f"Powered by watsonx.ai")
    print(f"URL  : http://localhost:{port}")
    print(f"Model: IBM Granite 13B Instruct v2")
    print(f"Mode : {mode_label}")
    print()
    app.run(host="0.0.0.0", port=port, debug=debug)
