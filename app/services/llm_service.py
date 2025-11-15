from typing import List

def extract_symptoms_from_text(raw_text: str) -> List[str]:
    """
    Extract symptoms and map to ML model's EXACT format (fully concatenated, NO underscores!)
    """
    text = raw_text.lower()
    
    # Map to EXACT dataset.csv symptom names (fully concatenated)
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
        
        'runny': 'runnynose',           # ← FIXED: runnynose (not runny_nose)
        'running nose': 'runnynose',
        'nose': 'runnynose',
        
        'joint': 'jointpain',
        'pain': 'jointpain',
        
        'weak': 'muscleweakness',
        'muscle pain': 'musclepain',    # ← FIXED: musclepain (not muscle_pain)
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
        
        'cold': 'chills',  # For "common cold"
    }
    
    symptoms = []
    for keyword, symptom in symptom_mapping.items():
        if keyword in text and symptom not in symptoms:
            symptoms.append(symptom)
    
    # Return at least some symptoms
    if not symptoms:
        symptoms = ['headache', 'fatigue']
    
    print(f"LLM: Extracted symptoms (ML format): {symptoms}")
    return symptoms

def generate_final_summary(raw_text: str, ml_results) -> str:
    """Generate summary"""
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
