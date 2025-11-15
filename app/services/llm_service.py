from typing import List
import os

def extract_symptoms_from_text(raw_text: str) -> List[str]:
    """Extract symptoms from patient description"""
    text = raw_text.lower()
    
    symptom_mapping = {
        'headache': 'headache',
        'head pain': 'headache',
        'head': 'headache',
        'fever': 'highfever',
        'temperature': 'highfever',
        'high fever': 'highfever',
        'cough': 'cough',
        'coughing': 'cough',
        'sneez': 'continuoussneezing',
        'burn': 'burningmicturition',
        'burning': 'burningmicturition',
        'runny': 'runnynose',
        'running nose': 'runnynose',
        'nose': 'runnynose',
        'joint': 'jointpain',
        'pain': 'jointpain',
        'weak': 'muscleweakness',
        'muscle pain': 'musclepain',
        'body ache': 'musclepain',
        'ache': 'musclepain',
        'tired': 'fatigue',
        'fatigue': 'fatigue',
        'nausea': 'nausea',
        'vomit': 'vomiting',
        'stomach': 'stomachpain',
        'belly': 'stomachpain',
        'dizzy': 'dizziness',
        'skin': 'skinrash',
        'rash': 'skinrash',
        'itch': 'itching',
        'breathe': 'breathlessness',
        'breath': 'breathlessness',
        'chest': 'chestpain',
        'sweat': 'sweating',
        'appetite': 'lossofappetite',
        'chill': 'chills',
        'shiver': 'shivering',
        'cold': 'chills',
        'throat': 'throatirritation',
    }
    
    symptoms = []
    for keyword, symptom in symptom_mapping.items():
        if keyword in text and symptom not in symptoms:
            symptoms.append(symptom)
    
    if not symptoms:
        symptoms = ['headache', 'fatigue']
    
    print(f"LLM: Extracted symptoms: {symptoms}")
    return symptoms


def generate_final_summary(raw_text: str, ml_results) -> str:
    """Generate patient summary"""
    if hasattr(ml_results, '__dict__'):
        ml_dict = ml_results.__dict__
    elif isinstance(ml_results, dict):
        ml_dict = ml_results
    else:
        ml_dict = {}
    
    predictions = ml_dict.get('predictions', [])
    if predictions and len(predictions) > 0:
        top = predictions[0]
        disease = top.get('disease', 'Unknown')
        probability = top.get('probability', 'N/A')
        description = top.get('description', '')
        
        summary = f"Based on your symptoms, our analysis suggests a {probability} probability of {disease}. "
        summary += f"{description[:200]}... "
        summary += "Please consult a healthcare provider for proper diagnosis."
        return summary
    
    return "Analysis completed. Please consult a healthcare provider."


def generate_ai_prescription(symptoms: List[str], disease: str, ml_results: dict) -> dict:
    """
    Generate AI-suggested prescription for educational/intern review
    Returns medicine suggestions with disclaimer
    """
    groq_key = os.getenv("GROQ_API_KEY", "")
    
    if groq_key:
        try:
            from groq import Groq
            import json, re
            
            client = Groq(api_key=groq_key)
            
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{
                    "role": "system",
                    "content": "You are a medical AI assistant helping medical interns learn about common treatments. Provide educational medication suggestions with proper dosages."
                }, {
                    "role": "user",
                    "content": f"""Disease: {disease}
Symptoms: {', '.join(symptoms)}

Suggest 3-4 common medications for this condition with:
- Generic name
- Dosage (e.g., "500mg twice daily")
- Duration (e.g., "5 days")
- Instructions (e.g., "Take after meals")

Return ONLY valid JSON:
{{
  "medications": [
    {{
      "name": "Medicine Name",
      "dosage": "Dosage",
      "duration": "Duration",
      "instructions": "Instructions"
    }}
  ],
  "disclaimer": "AI-generated suggestion for educational review only"
}}"""
                }],
                temperature=0.3,
                max_tokens=600
            )
            
            llm_text = response.choices[0].message.content
            match = re.search(r'\{.*\}', llm_text, re.DOTALL)
            
            if match:
                prescription = json.loads(match.group(0))
                print(f"✅ AI Prescription generated")
                return prescription
            else:
                raise Exception("No JSON in response")
                
        except Exception as e:
            print(f"Prescription generation error: {e}")
    
    # Fallback: Rule-based prescription
    return generate_rule_based_prescription(symptoms, disease)


def generate_rule_based_prescription(symptoms: List[str], disease: str) -> dict:
    """Fallback rule-based prescription generator"""
    
    medications = []
    
    # Common cold/respiratory
    if any(s in symptoms for s in ['cough', 'runnynose', 'throatirritation']):
        medications.append({
            "name": "Paracetamol 500mg",
            "dosage": "1 tablet",
            "duration": "5 days",
            "instructions": "Take twice daily after meals"
        })
        medications.append({
            "name": "Cetirizine 10mg",
            "dosage": "1 tablet",
            "duration": "5 days",
            "instructions": "Take once daily at bedtime"
        })
    
    # Fever
    if 'highfever' in symptoms or 'fever' in disease.lower():
        medications.append({
            "name": "Ibuprofen 400mg",
            "dosage": "1 tablet",
            "duration": "3 days",
            "instructions": "Take three times daily with food"
        })
    
    # Headache
    if 'headache' in symptoms:
        if not any(m['name'].startswith('Paracetamol') for m in medications):
            medications.append({
                "name": "Paracetamol 500mg",
                "dosage": "1 tablet",
                "duration": "As needed",
                "instructions": "Take when needed, max 3 times daily"
            })
    
    # Stomach issues
    if any(s in symptoms for s in ['stomachpain', 'nausea', 'vomiting']):
        medications.append({
            "name": "Omeprazole 20mg",
            "dosage": "1 capsule",
            "duration": "7 days",
            "instructions": "Take once daily before breakfast"
        })
    
    # Default if nothing matched
    if not medications:
        medications = [{
            "name": "Multivitamin",
            "dosage": "1 tablet",
            "duration": "30 days",
            "instructions": "Take once daily with breakfast"
        }]
    
    return {
        "medications": medications,
        "disclaimer": "AI-suggested prescription for educational review. Must be verified by supervising physician."
    }
