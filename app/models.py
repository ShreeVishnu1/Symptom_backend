from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from beanie import Document
from typing import List, Optional, Literal # <-- Add Literal

# --- NEW: Token models for auth ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- NEW: User models for auth ---
class UserBase(BaseModel):
    username: str = Field(...)
    email: Optional[EmailStr] = None
    role: Literal["patient", "doctor"] = "patient" # Added role

class UserCreate(UserBase):
    password: str

# --- MODIFIED: User model for DB ---
class User(Document, UserBase):
    hashed_password: str
    
    class Settings:
        name = "users" # MongoDB collection name

# --- ML & Analysis Models (Unchanged) ---
class Prediction(BaseModel):
    disease: str
    probability: str
    description: str
    precautions: dict

class AuditorResponse(BaseModel):
    predictions: List[Prediction]

class AnalysisResult(Document):
    user_uid: str = Field(..., index=True) # This will now be the username
    raw_transcription: str
    llm_symptoms: List[str]
    ml_results: AuditorResponse
    llm_final_summary: str
    
    class Settings:
        name = "analysis_history"

class AnalysisRequest(BaseModel):
    text: str = Field(..., description="Input text")
    patient_id: list[str] = Field(default_factory=list, description="patient")

# ========== NEW: Consultation Model ==========
class Consultation(Document):
    """Stores consultation sessions"""
    patient_email: str = Field(..., index=True)
    patient_name: str
    doctor_email: str = Field(..., index=True)
    doctor_name: str = "Dr. Rajesh Verma"  # NEW
    
    transcription: str
    symptoms: List[str]
    diagnosis: str
    diagnosis_confidence: str
    summary: str
    
    medications: List[dict] = []
    precautions: List[str] = []
    ml_predictions: dict = {}
    
    # Follow-up appointment (NEW)
    followup_date: Optional[str] = None
    followup_time: Optional[str] = None
    
    consultation_date: datetime = Field(default_factory=datetime.now)
    status: str = "completed"
    
    class Settings:
        name = "consultations"
