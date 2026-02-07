"""
Medication Knowledge Base and Plain Language Translator
"""

# Comprehensive medication database with plain language explanations
MEDICATION_DATABASE = {
    "aspirin": {
        "generic_name": "Acetylsalicylic Acid",
        "plain_name": "Aspirin",
        "what_for": "Pain relief, fever reduction, and blood clot prevention",
        "how_works": "Reduces pain signals in the nervous system and prevents blood clotting",
        "how_to_take": "Swallow whole with water",
        "with_food": "Take with food or milk to avoid stomach upset",
        "duration_instruction": "Complete the full course even if you feel better",
        "why_important": "Aspirin helps prevent heart attacks and strokes when taken regularly",
        "risks_of_skipping": "Missing doses increases risk of blood clots (esp. after heart attack or stroke)",
        "side_effects": "Stomach upset, heartburn, easy bruising",
        "contraindications": ["Aspirin allergy", "Bleeding disorders", "Ulcers"],
    },
    "metformin": {
        "generic_name": "Metformin",
        "plain_name": "Metformin (Diabetes Medication)",
        "what_for": "Controlling blood sugar levels in Type 2 diabetes",
        "how_works": "Reduces sugar production in the liver and helps your body use insulin better",
        "how_to_take": "Swallow with water",
        "with_food": "Take with meals to reduce stomach upset",
        "duration_instruction": "Take regularly - this is a long-term medication",
        "why_important": "Keeps blood sugar stable, preventing diabetes complications like kidney damage, blindness",
        "risks_of_skipping": "High blood sugar can damage eyes, kidneys, heart, and nerves over time",
        "side_effects": "Stomach upset, metallic taste, weakness",
        "contraindications": ["Kidney disease", "Severe liver disease", "Heart failure"],
    },
    "amoxicillin": {
        "generic_name": "Amoxicillin",
        "plain_name": "Amoxicillin (Antibiotic)",
        "what_for": "Fighting bacterial infections like ear infections, strep throat, pneumonia",
        "how_works": "Kills bacteria by breaking down their cell walls",
        "how_to_take": "Swallow with water",
        "with_food": "Can take with or without food",
        "duration_instruction": "IMPORTANT: Complete the full course even if you feel better after 2-3 days",
        "why_important": "Finishing the full course prevents infection from returning and stops antibiotic resistance",
        "risks_of_skipping": "Bacteria can survive and return, making the infection worse and harder to treat",
        "side_effects": "Nausea, diarrhea, rash (rare)",
        "contraindications": ["Penicillin allergy", "Mononucleosis"],
    },
    "lisinopril": {
        "generic_name": "Lisinopril",
        "plain_name": "Lisinopril (Blood Pressure Medication)",
        "what_for": "Lowering high blood pressure and protecting the heart",
        "how_works": "Relaxes blood vessels so blood flows more easily",
        "how_to_take": "Swallow with water",
        "with_food": "Take at the same time each day",
        "duration_instruction": "Take daily - this is long-term blood pressure control",
        "why_important": "Controls blood pressure to prevent heart attack and stroke",
        "risks_of_skipping": "High blood pressure can damage heart, brain, and kidneys",
        "side_effects": "Cough, dizziness, fatigue",
        "contraindications": ["Pregnancy", "Kidney disease", "High potassium levels"],
    },
    "ibuprofen": {
        "generic_name": "Ibuprofen",
        "plain_name": "Ibuprofen (Pain/Fever Reliever)",
        "what_for": "Pain relief, fever reduction, and reducing inflammation",
        "how_works": "Reduces prostaglandins that cause pain, fever, and swelling",
        "how_to_take": "Swallow with water",
        "with_food": "Take with food to protect stomach",
        "duration_instruction": "Use for the shortest time possible",
        "why_important": "Reduces pain and inflammation to help you feel better",
        "risks_of_skipping": "Pain and inflammation may worsen, limiting your activities",
        "side_effects": "Stomach upset, heartburn, increased blood pressure",
        "contraindications": ["Ulcers", "High blood pressure", "Kidney disease"],
    },
    "atorvastatin": {
        "generic_name": "Atorvastatin",
        "plain_name": "Atorvastatin (Cholesterol Medication)",
        "what_for": "Lowering cholesterol and reducing heart attack/stroke risk",
        "how_works": "Reduces cholesterol production in the liver",
        "how_to_take": "Swallow with water",
        "with_food": "Can take with or without food",
        "duration_instruction": "Take daily for long-term cholesterol control",
        "why_important": "Lower cholesterol reduces plaque buildup in arteries, protecting your heart",
        "risks_of_skipping": "High cholesterol increases risk of heart disease and stroke",
        "side_effects": "Muscle pain, weakness, headache",
        "contraindications": ["Liver disease", "Pregnancy"],
    },
}

# Drug interaction database
DRUG_INTERACTIONS = {
    ("metformin", "alcohol"): {
        "risk": "high",
        "message": "Alcohol can affect blood sugar control. Limit alcohol while taking Metformin.",
    },
    ("aspirin", "ibuprofen"): {
        "risk": "high",
        "message": "Taking both together increases stomach bleeding risk. Use only one.",
    },
    ("lisinopril", "potassium"): {
        "risk": "high",
        "message": "Too much potassium with this medicine is dangerous. Avoid potassium supplements.",
    },
}

# Pregnancy contraindications
PREGNANCY_CONTRAINDICATIONS = [
    "aspirin",
    "ibuprofen",
    "atorvastatin",
    "lisinopril",
    "amoxicillin",
]

# Breastfeeding contraindications
BREASTFEEDING_CONTRAINDICATIONS = [
    "aspirin",  # High doses
]

def get_medication_info(medicine_name):
    """Get plain language medication information"""
    medicine_name = medicine_name.lower().strip()
    
    # Try exact match
    if medicine_name in MEDICATION_DATABASE:
        return MEDICATION_DATABASE[medicine_name]
    
    # Try partial match
    for med_name, med_info in MEDICATION_DATABASE.items():
        if medicine_name in med_name or med_name in medicine_name:
            return med_info
    
    return None

def create_plain_language_explanation(medication_info):
    """Create a comprehensive plain language explanation of medication"""
    if not medication_info:
        return None
    
    explanation = f"""
🔷 {medication_info['plain_name'].upper()}

💊 WHAT IS IT FOR?
{medication_info['what_for']}

🔄 HOW DOES IT WORK?
{medication_info['how_works']}

📋 HOW TO TAKE IT:
{medication_info['how_to_take']}

🍽️ WITH FOOD?
{medication_info['with_food']}

⏱️ HOW LONG?
{medication_info['duration_instruction']}

❤️ WHY IS THIS IMPORTANT? (THIS IS WHY YOU NEED TO TAKE IT)
{medication_info['why_important']}

⚠️ WHAT HAPPENS IF YOU SKIP DOSES?
{medication_info['risks_of_skipping']}

😷 POSSIBLE SIDE EFFECTS:
{medication_info['side_effects']}
"""
    return explanation.strip()

def check_contraindications(medicine_name, user_medical_info):
    """Check for contraindications based on patient medical history"""
    medicine_name = medicine_name.lower().strip()
    warnings = []
    
    med_info = get_medication_info(medicine_name)
    if not med_info:
        return warnings
    
    # Check allergies
    if user_medical_info.get("drug_allergies"):
        allergies = user_medical_info["drug_allergies"].lower()
        if medicine_name in allergies or med_info["generic_name"].lower() in allergies:
            warnings.append({
                "type": "ALLERGY",
                "risk": "HIGH",
                "message": f"⚠️ SEVERE: You have a documented allergy to {med_info['plain_name']}. DO NOT take this medicine.",
                "action": "CONTACT YOUR DOCTOR IMMEDIATELY"
            })
    
    # Check pregnancy
    if user_medical_info.get("is_pregnant") and medicine_name in [m.lower() for m in PREGNANCY_CONTRAINDICATIONS]:
        warnings.append({
            "type": "PREGNANCY",
            "risk": "HIGH",
            "message": f"⚠️ WARNING: {med_info['plain_name']} may harm your baby. Consult your doctor.",
            "action": "CONFIRM WITH DOCTOR"
        })
    
    # Check breastfeeding
    if user_medical_info.get("is_breastfeeding") and medicine_name in [m.lower() for m in BREASTFEEDING_CONTRAINDICATIONS]:
        warnings.append({
            "type": "BREASTFEEDING",
            "risk": "MEDIUM",
            "message": f"⚠️ WARNING: {med_info['plain_name']} may pass to baby through breast milk. Consult your doctor.",
            "action": "CONFIRM WITH DOCTOR"
        })
    
    # Check documented contraindications
    if user_medical_info.get("existing_conditions"):
        conditions = user_medical_info["existing_conditions"].lower()
        for contraindication in med_info.get("contraindications", []):
            if contraindication.lower() in conditions:
                warnings.append({
                    "type": "CONDITION",
                    "risk": "HIGH",
                    "message": f"⚠️ WARNING: You have {contraindication}, which conflicts with {med_info['plain_name']}.",
                    "action": "DISCUSS WITH YOUR DOCTOR"
                })
    
    return warnings

def get_adherence_nudge(medicine_name, frequency):
    """Generate behavioral nudges based on nudge theory"""
    med_info = get_medication_info(medicine_name)
    
    nudges = []
    
    # Why timing matters
    if med_info:
        nudge = {
            "title": "⏰ Why Timing Matters",
            "message": med_info["why_important"],
            "type": "motivation"
        }
        nudges.append(nudge)
    
    # Why full course matters (for antibiotics)
    if "antibiotic" in medicine_name.lower() or "antibiotics" in str(med_info).lower():
        nudge = {
            "title": "💪 Complete Your Course",
            "message": "Finishing all doses prevents the infection from coming back stronger. Don't stop early!",
            "type": "completion"
        }
        nudges.append(nudge)
    
    # Social proof/health consequences
    nudge = {
        "title": "🏥 Health Impact",
        "message": med_info["risks_of_skipping"] if med_info else "Skipping doses reduces the effectiveness of your treatment.",
        "type": "consequence"
    }
    nudges.append(nudge)
    
    return nudges

def format_daily_schedule(dosage, frequency):
    """Convert frequency to specific daily schedule times"""
    frequency_lower = frequency.lower().strip()
    
    schedule_mapping = {
        "once a day": ["08:00"],
        "once daily": ["08:00"],
        "twice a day": ["08:00", "20:00"],
        "twice daily": ["08:00", "20:00"],
        "three times a day": ["08:00", "13:00", "20:00"],
        "three times daily": ["08:00", "13:00", "20:00"],
        "every 8 hours": ["08:00", "16:00", "00:00"],
        "every 12 hours": ["08:00", "20:00"],
        "every 6 hours": ["06:00", "12:00", "18:00", "24:00"],
        "at bedtime": ["21:00"],
        "before breakfast": ["07:00"],
        "after meals": ["08:00", "13:00", "20:00"],
    }
    
    for key, times in schedule_mapping.items():
        if key in frequency_lower:
            return times
    
    # Default to once daily if unclear
    return ["08:00"]
