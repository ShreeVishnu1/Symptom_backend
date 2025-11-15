from fastapi import APIRouter, Depends, HTTPException
from ..models import User, Consultation
from ..auth import get_current_user
from typing import List

router = APIRouter()

@router.get("/my-consultations", response_model=List[Consultation])
async def get_my_consultations(current_user: User = Depends(get_current_user)):
    """
    Get all consultations for the logged-in patient
    """
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can access this")
    
    consultations = await Consultation.find(
        Consultation.patient_email == current_user.email
    ).sort(-Consultation.consultation_date).to_list()
    
    return consultations

@router.get("/consultation/{consultation_id}")
async def get_consultation_details(
    consultation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get specific consultation details
    """
    from beanie import PydanticObjectId
    
    consultation = await Consultation.get(PydanticObjectId(consultation_id))
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    # Check if user has access
    if current_user.role == "patient" and consultation.patient_email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "doctor" and consultation.doctor_email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return consultation
