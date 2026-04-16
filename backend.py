"""
Health Risk Management Backend
Run with:  pip install flask flask-cors  &&  python app.py
API runs at: https://satan-angel.github.io/health-risk-system/
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import math

app = Flask(__name__)
CORS(app)  # Allow frontend to call the API


# ─── Helpers ────────────────────────────────────────────────────────────────

def calc_bmi(weight_kg, height_cm):
    h = height_cm / 100
    return round(weight_kg / (h * h), 1)

def bmi_fuzzy_membership(bmi):
    # Underweight
    if bmi <= 18:
        under = 1
    elif 18 < bmi < 22:
        under = (22 - bmi) / (22 - 18)
    else:
        under = 0
    # Normal
    if bmi <= 18 or bmi >= 26:
        normal = 0
    elif 18 < bmi <= 22:
        normal = (bmi - 18) / (22 - 18)
    else:
        normal = (26 - bmi) / (26 - 22)
    # Overweight
    if bmi <= 24:
        over = 0
    elif 24 < bmi < 28:
        over = (bmi - 24) / (28 - 24)
    else:
        over = 1
    return {
        "underweight": round(under, 2),
        "normal": round(normal, 2),
        "overweight": round(over, 2)
    }                                                                                                                                                                                                                                                                                                                     
def fuzzy_bmi_label(memberships):
    return max(memberships, key=memberships.get)

def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight", "low"
    elif bmi < 25:
        return "Normal weight", "normal"
    elif bmi < 30:
        return "Overweight", "medium"
    else:
        return "Obese", "high"

def bp_category(systolic, diastolic):
    if systolic < 120 and diastolic < 80:
        return "Normal", "normal"
    elif systolic < 130 and diastolic < 80:
        return "Elevated", "medium"
    elif systolic < 140 or diastolic < 90:
        return "High Stage 1", "high"
    else:
        return "High Stage 2", "critical"

def glucose_category(glucose, fasting=True):
    if fasting:
        if glucose < 100:
            return "Normal", "normal"
        elif glucose < 126:
            return "Prediabetes", "medium"
        else:
            return "Diabetic range", "high"
    else:
        if glucose < 140:
            return "Normal", "normal"
        elif glucose < 200:
            return "Prediabetes", "medium"
        else:
            return "Diabetic range", "high"

def sleep_category(hours):
    if hours >= 7 and hours <= 9:
        return "Optimal", "normal"
    elif hours >= 6 or hours == 9.5:
        return "Borderline", "medium"
    else:
        return "Insufficient", "high"

def calc_health_score(data):
    """
    Score from 0–100 based on multiple weighted factors.
    Higher is better.
    """
    score = 100

    # BMI penalty (weight 20)
    bmi = calc_bmi(data["weight_kg"], data["height_cm"])
    if bmi < 18.5 or bmi >= 30:
        score -= 20
    elif bmi >= 25:
        score -= 10

    # Blood pressure penalty (weight 25)
    _, bp_risk = bp_category(data["systolic"], data["diastolic"])
    if bp_risk == "critical":
        score -= 25
    elif bp_risk == "high":
        score -= 15
    elif bp_risk == "medium":
        score -= 8

    # Glucose penalty (weight 20)
    _, gl_risk = glucose_category(data["glucose"])
    if gl_risk == "high":
        score -= 20
    elif gl_risk == "medium":
        score -= 10

    # Sleep penalty (weight 10)
    _, sl_risk = sleep_category(data["sleep_hours"])
    if sl_risk == "high":
        score -= 10
    elif sl_risk == "medium":
        score -= 5

    # Smoking penalty (weight 15)
    smoking = data.get("smoking", "never")
    if smoking == "current":
        score -= 15
    elif smoking == "former":
        score -= 5

    # Activity bonus/penalty (weight 10)
    activity = data.get("activity_level", "sedentary")
    if activity == "very_active":
        score += 5
    elif activity == "moderately_active":
        score += 2
    elif activity == "sedentary":
        score -= 10

    # Age adjustment
    age = data.get("age", 30)
    if age > 60:
        score -= 5
    elif age > 45:
        score -= 2

    # Stress penalty
    stress = data.get("stress_level", 5)
    if stress >= 8:
        score -= 10
    elif stress >= 6:
        score -= 5

    return max(0, min(100, score))


def build_risk_factors(data):
    risks = []
    bmi = calc_bmi(data["weight_kg"], data["height_cm"])

    # Blood Pressure
    bp_label, bp_risk = bp_category(data["systolic"], data["diastolic"])
    risks.append({
        "name": "Blood Pressure",
        "value": f"{data['systolic']}/{data['diastolic']} mmHg",
        "status": bp_label,
        "level": bp_risk,
        "advice": "Reduce sodium, exercise regularly, limit alcohol." if bp_risk in ("high","critical")
                  else "Maintain healthy lifestyle habits."
    })

    # BMI
    bmi_label, bmi_risk = bmi_category(bmi)
    risks.append({
        "name": "BMI",
        "value": str(bmi),
        "status": bmi_label,
        "level": bmi_risk,
        "advice": "Aim for a BMI of 18.5–24.9 through balanced diet and exercise." if bmi_risk != "normal"
                  else "Maintain your current weight."
    })

    # Blood Glucose
    gl_label, gl_risk = glucose_category(data["glucose"])
    risks.append({
        "name": "Fasting Blood Glucose",
        "value": f"{data['glucose']} mg/dL",
        "status": gl_label,
        "level": gl_risk,
        "advice": "Reduce sugar intake, increase fiber, exercise regularly." if gl_risk != "normal"
                  else "Keep up your diet habits."
    })

    # Sleep
    sl_label, sl_risk = sleep_category(data["sleep_hours"])
    risks.append({
        "name": "Sleep",
        "value": f"{data['sleep_hours']} hrs/night",
        "status": sl_label,
        "level": sl_risk,
        "advice": "Aim for 7–9 hours. Maintain a consistent sleep schedule." if sl_risk != "normal"
                  else "Good sleep habits — keep it up."
    })

    # Smoking
    smoking = data.get("smoking", "never")
    smoke_map = {"never": ("Never smoked", "normal"), "former": ("Former smoker", "medium"), "current": ("Current smoker", "high")}
    s_label, s_risk = smoke_map[smoking]
    risks.append({
        "name": "Smoking",
        "value": s_label,
        "status": s_label,
        "level": s_risk,
        "advice": "Quitting smoking is the single best thing you can do for your health." if smoking == "current"
                  else ("Risk remains elevated for ~10 years after quitting." if smoking == "former" else "Great — never start.")
    })

    # Stress
    stress = data.get("stress_level", 5)
    s_risk_level = "high" if stress >= 8 else ("medium" if stress >= 6 else "normal")
    risks.append({
        "name": "Stress Level",
        "value": f"{stress} / 10",
        "status": "High" if s_risk_level == "high" else ("Moderate" if s_risk_level == "medium" else "Low"),
        "level": s_risk_level,
        "advice": "Practice mindfulness, breathing exercises, or seek professional support." if s_risk_level != "normal"
                  else "Good stress management."
    })

    # Sort: critical → high → medium → normal
    order = {"critical": 0, "high": 1, "medium": 2, "normal": 3}
    risks.sort(key=lambda r: order.get(r["level"], 4))
    return risks


def build_recommendations(data, health_score):
    recs = []
    bmi = calc_bmi(data["weight_kg"], data["height_cm"])
    _, bp_risk = bp_category(data["systolic"], data["diastolic"])
    _, gl_risk = glucose_category(data["glucose"])
    _, sl_risk = sleep_category(data["sleep_hours"])
    smoking = data.get("smoking", "never")
    activity = data.get("activity_level", "sedentary")
    stress = data.get("stress_level", 5)

    if bp_risk in ("high", "critical"):
        recs.append({"priority": "urgent", "text": "Monitor blood pressure daily and consult a doctor. Consider DASH diet."})
    if bmi >= 25:
        recs.append({"priority": "high", "text": f"Work toward a BMI under 25. At {data['weight_kg']} kg / {data['height_cm']} cm you need to lose ~{round((bmi - 24.9) * (data['height_cm']/100)**2, 1)} kg."})
    if gl_risk != "normal":
        recs.append({"priority": "high", "text": "Reduce refined carbohydrates and sugar. A fasting glucose test is recommended."})
    if sl_risk != "normal":
        recs.append({"priority": "medium", "text": "Improve sleep hygiene: consistent bedtime, no screens 1 hr before bed, dark cool room."})
    if smoking == "current":
        recs.append({"priority": "urgent", "text": "Stop smoking immediately. Consult a cessation program or nicotine replacement therapy."})
    if activity == "sedentary":
        recs.append({"priority": "medium", "text": "Aim for 150 min of moderate exercise per week. Start with daily 30-min walks."})
    if stress >= 6:
        recs.append({"priority": "medium", "text": "High stress raises cortisol and blood pressure. Try meditation, yoga, or therapy."})
    if health_score >= 80:
        recs.append({"priority": "info", "text": "Excellent health profile! Schedule an annual check-up to maintain your status."})

    if not recs:
        recs.append({"priority": "info", "text": "Your health indicators are within normal ranges. Maintain your current habits!"})

    return recs


# ─── Routes ─────────────────────────────────────────────────────────────────

@app.route("/api/assess", methods=["POST"])
def assess():
    """
    POST /api/assess
    Body (JSON):
    {
      "name": "John",
      "age": 42,
      "sex": "male",
      "weight_kg": 83.5,
      "height_cm": 175,
      "systolic": 138,
      "diastolic": 88,
      "glucose": 94,
      "sleep_hours": 6.5,
      "smoking": "never",         // never | former | current
      "activity_level": "lightly_active",  // sedentary | lightly_active | moderately_active | very_active
      "stress_level": 6           // 1–10
    }

    Returns:
    {
      "health_score": 72,
      "bmi": 27.3,
      "bmi_category": "Overweight",
      "risk_factors": [...],
      "recommendations": [...],
      "summary": "..."
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    required = ["weight_kg", "height_cm", "systolic", "diastolic", "glucose", "sleep_hours"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        bmi = calc_bmi(data["weight_kg"], data["height_cm"])
        bmi_membership = bmi_fuzzy_membership(bmi)
        bmi_label_map = {
        "underweight": "Underweight",
        "normal": "Normal weight",
        "overweight": "Overweight"
        }

        bmi_cat = bmi_label_map[fuzzy_bmi_label(bmi_membership)]
        health_score = calc_health_score(data)
        risk_factors = build_risk_factors(data)
        recommendations = build_recommendations(data, health_score)

        high_risks = [r for r in risk_factors if r["level"] in ("high", "critical")]
        risk_summary = f"{len(high_risks)} high-priority risk factor(s) identified." if high_risks else "No high-priority risks detected."

        return jsonify({
            "health_score": health_score,
            "score_label": "Excellent" if health_score >= 85 else "Good" if health_score >= 70 else "Fair" if health_score >= 55 else "Poor",
            "bmi": bmi,
            "bmi_category": bmi_cat,
            "bmi_membership": bmi_membership,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "summary": f"Hello {data.get('name','there')}. Your health score is {health_score}/100 ({('Excellent' if health_score >= 85 else 'Good' if health_score >= 70 else 'Fair' if health_score >= 55 else 'Poor')}). {risk_summary}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/bmi", methods=["POST"])
def bmi_only():
    """Quick BMI endpoint. Body: { "weight_kg": 83.5, "height_cm": 175 }"""
    data = request.get_json()
    bmi = calc_bmi(data["weight_kg"], data["height_cm"])
    membership = bmi_fuzzy_membership(bmi)
    cat = fuzzy_bmi_label(membership)

    return jsonify({
    "bmi": bmi,
    "category": cat,
    "membership": membership
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Health Risk API running"})


# ─── Run ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))

    print("=" * 50)
    print("  Health Risk Management API")
    print(f"  Running at http://localhost:{port}")
    print("  Frontend: open index.html in browser")
    print("=" * 50)

    app.run(host="0.0.0.0", port=port)