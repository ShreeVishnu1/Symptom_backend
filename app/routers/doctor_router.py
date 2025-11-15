from fastapi import APIRouter, Depends, Body
from ..models import User, Consultation
from ..auth import get_current_user
from typing import List
from beanie import PydanticObjectId
router = APIRouter()

@router.get("/patients", response_model=List[dict])
async def get_registered_patients(current_user: User = Depends(get_current_user)):
    """
    Get all registered patients for doctor's dashboard
    """
    if current_user.role != "doctor":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only doctors can access this")
    
    # Get all patients
    patients = await User.find(User.role == "patient").to_list()
    
    return [{
        "email": p.email,
        "name": p.username,
        "id": str(p.id)
    } for p in patients]

@router.get("/my-consultations", response_model=List[Consultation])
async def get_doctor_consultations(current_user: User = Depends(get_current_user)):
    """
    Get all consultations performed by this doctor
    """
    if current_user.role != "doctor":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only doctors can access this")
    
    consultations = await Consultation.find(
        Consultation.doctor_email == current_user.email
    ).sort(-Consultation.consultation_date).to_list()
    
    return consultations

@router.post("/schedule-followup")
async def schedule_followup(
    consultation_id: str = Body(...),
    followup_date: str = Body(...),
    followup_time: str = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Schedule follow-up appointment for a consultation"""
    if current_user.role != "doctor":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only doctors can schedule")
    
    # Update consultation
    consultation = await Consultation.get(PydanticObjectId(consultation_id))
    
    if not consultation:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    consultation.followup_date = followup_date
    consultation.followup_time = followup_time
    await consultation.save()
    
    return {"message": "Follow-up scheduled", "date": followup_date, "time": followup_time}