from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import init_db
from .services.auditor_service import auditor # Your ML model service
from .routers import analysis_router, auth_router # Your API endpoints
from .routers import patient_router, doctor_router  # NEW
# This "lifespan" function is CRITICAL
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs ONCE when the app starts
    print("FastAPI: Startup event triggered.")
    await init_db()             # Connect to MongoDB
    auditor.load_model()        # Load ML model into memory
    print("FastAPI: Model loaded, DB connected. App is ready.")
    yield
    print("FastAPI: Shutting down.")

app = FastAPI(title="Symptom Storyteller API", lifespan=lifespan)

# This is CRITICAL for your React app to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your API endpoints
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analysis_router.router, prefix="/api", tags=["Analysis"])
app.include_router(patient_router.router, prefix="/api/patient", tags=["patient"])  # NEW
app.include_router(doctor_router.router, prefix="/api/doctor", tags=["doctor"])    # NEW

@app.get("/")
def read_root():
    return {"message": "Symptom Storyteller API is running!"}