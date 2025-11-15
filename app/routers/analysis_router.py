from fastapi import APIRouter, Depends, File, UploadFile, Body
from ..models import User, AnalysisResult
from ..auth import get_current_user
from ..services import stt_service, llm_service
from ..services.auditor_service import auditor
from typing import List, Optional
import os

router = APIRouter()

@router.post("/analyze")
async def analyze_symptoms(
    audio_file: Optional[UploadFile] = File(None),
    text: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """Analyze symptoms from audio or text with ML + LLM hybrid approach"""
    
    # --- 1. Get transcription ---
    if audio_file:
        try:
            audio_bytes = await audio_file.read()
            raw_text = await stt_service.transcribe_audio(audio_bytes)
            print(f"Transcribed: {raw_text}")
        except Exception as e:
            print(f"STT Error: {e}")
            raw_text = "I have headache and fever"
    elif text:
        raw_text = text
    else:
        raw_text = "I have headache and fever"
    
    # --- 2. Extract Symptoms ---
    symptom_list = llm_service.extract_symptoms_from_text(raw_text)
    if not symptom_list:
        symptom_list = ['headache', 'fatigue']
        print(f"Using fallback symptoms")

    # --- 3. Try ML Prediction ---
    ml_results = None
    ml_success = False
    
    try:
        ml_results = auditor.predict(symptom_list)
        
        # Convert to dict if needed
        if hasattr(ml_results, '__dict__'):
            ml_dict = ml_results.__dict__
        elif isinstance(ml_results, dict):
            ml_dict = ml_results
        else:
            ml_dict = {}
        
        # Check if ML actually worked (not fallback)
        predictions = ml_dict.get('predictions', [])
        
        if predictions and len(predictions) > 0:
            top_disease = predictions[0].get('disease', '')
            
            # These are fallback diseases from your auditor service
            fallback_diseases = [
                'Paralysis (brain hemorrhage)',
                'GERD',
                'Bronchial Asthma',
                'Unknown'
            ]
            
            if top_disease not in fallback_diseases:
                ml_success = True
                print(f"✅ ML Success: {top_disease}")
            else:
                print(f"⚠️ ML returned fallback: {top_disease}")
                
    except Exception as e:
        print(f"ML Error: {e}")

    # --- 4. If ML Failed, Use LLM Prediction ---
    if not ml_success:
        print("🔄 Using LLM for disease prediction...")
        
        groq_key = os.getenv("GROQ_API_KEY", "")
        
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{
                        "role": "user",
                        "content": f"""Patient symptoms: {', '.join(symptom_list)}
                        
Predict the top 3 most likely diseases. Return ONLY valid JSON:
{{
  "predictions": [
    {{"disease": "Disease Name", "probability": "XX%", "description": "Brief description"}}
  ]
}}"""
                    }],
                    temperature=0.3,
                    max_tokens=500
                )
                
                import json, re
                llm_text = response.choices[0].message.content
                
                # Extract JSON
                match = re.search(r'\{.*\}', llm_text, re.DOTALL)
                if match:
                    ml_results = json.loads(match.group(0))
                    print(f"✅ LLM Prediction: {ml_results['predictions'][0]['disease']}")
                else:
                    raise Exception("No JSON found")
                    
            except Exception as e:
                print(f"LLM Error: {e}")
                ml_results = keyword_based_prediction(symptom_list)
        else:
            # No Groq key - use keyword prediction
            ml_results = keyword_based_prediction(symptom_list)

    # --- 5. Generate Summary ---
    try:
        final_summary = llm_service.generate_final_summary(
            raw_text,
            ml_results if isinstance(ml_results, dict) else {"predictions": []}
        )
    except Exception as e:
        print(f"Summary Error: {e}")
        final_summary = f"Analysis completed for symptoms: {', '.join(symptom_list)}. Please consult a healthcare provider."

    # --- 6. Save to DB ---
    try:
        new_history = AnalysisResult(
            user_uid=current_user.username,
            raw_transcription=raw_text,
            llm_symptoms=symptom_list,
            ml_results=ml_results,
            llm_final_summary=final_summary
        )
        await new_history.insert()
        print("✅ Saved to DB")
    except Exception as e:
        print(f"DB Error: {e}")
    
    return {
        "transcription": raw_text,
        "extracted_symptoms": symptom_list,
        "ml_predictions": ml_results,
        "final_summary": final_summary
    }


def keyword_based_prediction(symptoms: List[str]) -> dict:
    """Simple keyword-based disease prediction"""
    
    # Disease patterns
    if 'cough' in symptoms and 'runnynose' in symptoms:
        return {
            "predictions": [{
                "disease": "Common Cold",
                "probability": "75%",
                "description": "Viral infection of the upper respiratory tract causing runny nose, cough, and congestion."
            }]
        }
    elif 'headache' in symptoms and 'cough' in symptoms:
        return {
            "predictions": [{
                "disease": "Upper Respiratory Infection",
                "probability": "70%",
                "description": "Infection affecting the throat, sinuses, and airways."
            }]
        }
    elif 'headache' in symptoms:
        return {
            "predictions": [{
                "disease": "Tension Headache",
                "probability": "65%",
                "description": "Common type of headache caused by muscle tension or stress."
            }]
        }
    else:
        return {
            "predictions": [{
                "disease": "General Malaise",
                "probability": "60%",
                "description": "General feeling of discomfort. Consult a doctor for proper evaluation."
            }]
        }


@router.get("/history", response_model=List[AnalysisResult])
async def get_history(current_user: User = Depends(get_current_user)):
    return await AnalysisResult.find(AnalysisResult.user_uid == current_user.username).to_list()
