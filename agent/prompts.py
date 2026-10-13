"""
Prompt Engineering Module — Nutrition Agentic AI
Constructs structured, safe prompts for IBM Granite LLM.
Phase: Prompt Design (Agentic AI SDLC)
"""

from .guardrails import ham_tone_prefix


def build_nutrition_plan_prompt(profile: dict) -> str:
    """
    Builds a detailed, structured prompt for personalised nutrition plan generation.
    Encodes user profile, medical context, and HAM tone instructions.
    """
    name = profile.get("name", "User")
    age = profile.get("age", "Unknown")
    gender = profile.get("gender", "Not specified")
    diet = profile.get("diet_preference", "veg").lower()
    medical = profile.get("medical_history", "None reported")
    activity = profile.get("activity_level", "moderate")
    goal = profile.get("health_goal", "general wellness")
    city = profile.get("location_city", "")
    country = profile.get("location_country", "")
    allergies = profile.get("allergies", "None")
    weight = profile.get("weight_kg", "Not provided")
    height = profile.get("height_cm", "Not provided")

    location_str = f"{city}, {country}".strip(", ") or "Not specified"
    bmi_note = ""
    if weight != "Not provided" and height != "Not provided":
        try:
            bmi = float(weight) / ((float(height) / 100) ** 2)
            bmi_note = f"\n- BMI: {bmi:.1f} (calculated)"
        except (ValueError, ZeroDivisionError):
            pass

    prompt = f"""{ham_tone_prefix()}

You are a certified AI nutrition advisor. Generate a comprehensive, personalised 7-day nutrition plan for the following individual. Use markdown formatting with clear headings, tables, and bullet points.

## User Profile
- **Name:** {name}
- **Age:** {age} years
- **Gender:** {gender}
- **Diet Preference:** {diet.title()}
- **Medical History:** {medical}
- **Activity Level:** {activity.title()}
- **Primary Health Goal:** {goal.title()}
- **Location:** {location_str}
- **Food Allergies / Intolerances:** {allergies}
- **Weight:** {weight} kg
- **Height:** {height} cm{bmi_note}

## Instructions
1. Generate a **7-day personalised nutrition plan** that:
   - Respects the {diet} dietary preference strictly
   - Accounts for medical conditions: {medical}
   - Is appropriate for someone aged {age} in {location_str}
   - Avoids all allergens: {allergies}
   - Aligns with the health goal: {goal}

2. Include for each day:
   - Breakfast, Mid-Morning Snack, Lunch, Evening Snack, Dinner
   - Approximate calorie count per meal
   - Key nutrients highlighted

3. Add sections for:
   - **Daily Caloric Target** (with macronutrient breakdown table)
   - **Hydration Guidelines**
   - **Lifestyle & Exercise Recommendations**
   - **Condition-Specific Dietary Notes** (based on medical history)
   - **Recommended Micronutrients & Supplements**
   - **Foods to Avoid** (given the medical history and diet)

4. Use locally available foods common in {location_str} where possible.
5. Keep language warm, encouraging, and non-judgmental.
6. Do NOT suggest any medication changes or claim to cure any condition.

Begin the plan now:
"""
    return prompt


def build_query_prompt(user_question: str, context: dict = None) -> str:
    """
    Builds a conversational Q&A prompt for the agentic chat interface.
    Optionally includes user profile context for personalised answers.
    """
    context_str = ""
    if context:
        name = context.get("name", "")
        age = context.get("age", "")
        diet = context.get("diet_preference", "")
        medical = context.get("medical_history", "")
        if any([name, age, diet, medical]):
            context_str = f"""
## User Context (for personalisation)
- Name: {name or 'Not provided'}
- Age: {age or 'Not provided'}
- Diet: {diet or 'Not provided'}
- Medical History: {medical or 'None reported'}

"""

    prompt = f"""{ham_tone_prefix()}

You are a knowledgeable, empathetic AI nutrition assistant powered by IBM Granite.
Answer the following nutrition-related question accurately and helpfully.
Use simple, clear language. Where relevant, cite general nutritional science principles.
If the question involves a medical condition, always recommend consulting a healthcare professional.
Keep your answer concise (150–300 words) unless a detailed explanation is requested.
Do not make diagnosis or prescribe treatments.

{context_str}## User Question
{user_question}

## Your Answer
"""
    return prompt


def build_meal_swap_prompt(meal: str, reason: str, profile: dict) -> str:
    """
    Builds a prompt for suggesting alternative meals based on user preference.
    """
    diet = profile.get("diet_preference", "veg")
    medical = profile.get("medical_history", "None")
    allergies = profile.get("allergies", "None")

    return f"""{ham_tone_prefix()}

A user following a {diet} diet wants to replace the following meal:
**Original Meal:** {meal}
**Reason for swap:** {reason}
**Medical Conditions:** {medical}
**Allergies:** {allergies}

Please suggest 3 healthy alternative meals that:
1. Match the {diet} dietary preference
2. Are safe given the medical conditions and allergies
3. Have similar or better nutritional value
4. Are easy to prepare

Format as a numbered list with brief nutritional highlights for each option.
"""
