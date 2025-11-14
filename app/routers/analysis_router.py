from fastapi import APIRouter, Depends, HTTPException, Body
from ..models import User, AnalysisRequest, AnalysisResult
from ..auth import get_current_user # <-- This is the NEW dependency
from ..services import stt_service, llm_service
from ..services.auditor_service import auditor # <-- Import the object
from typing import List

router = APIRouter()

@router.post("/analyze")
async def analyze_symptoms(
    request: AnalysisRequest = Body(...),
    # This endpoint is now protected.
    # It will only work if a valid JWT is provided.
    current_user: User = Depends(get_current_user) 
):
    # ... (The rest of this file is IDENTICAL to my previous message)
    # --- 1. Transcribe Audio ---
    # (Using hackathon shortcut for speed)
    raw_text = "I have a sharp headache and a high fever of 102 degrees and I feel sick and have a cough"
    print("--- HACKATHON SHORTCUT: Using hardcoded text ---")
    
    # --- 2. Extract Symptoms ---
    symptom_list = await llm_service.extract_symptoms_from_text(raw_text)
    if not symptom_list:
        raise HTTPException(status_code=500, detail="LLM failed to extract symptoms.")

    # --- 3. Predict Disease ---
    ml_results = auditor.predict(symptom_list)

    # --- 4. Generate Summary ---
    final_summary = await llm_service.generate_final_summary(raw_text, ml_results)

    # --- 5. Save to DB ---
    new_history = AnalysisResult(
        user_uid=current_user.username, # <-- Use username instead of uid
        raw_transcription=raw_text,
        llm_symptoms=symptom_list,
        ml_results=ml_results,
        llm_final_summary=final_summary
    )
    await new_history.insert()
    
    return {
        "transcription": raw_text,
        "extracted_symptoms": symptom_list,
        "ml_predictions": ml_results,
        "final_summary": final_summary
    }

@router.get("/history", response_model=List[AnalysisResult])
async def get_history(current_user: User = Depends(get_current_user)):
    return await AnalysisResult.find(AnalysisResult.user_uid == current_user.username).to_list()