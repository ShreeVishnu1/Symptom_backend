import google.generativeai as genai
from ..config import settings
from ..models import AuditorResponse
from typing import List
import re

# Configure the Gemini API client
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def extract_symptoms_from_text(raw_text: str) -> List[str]:
    """
    Calls the Gemini API to extract a Python list of symptoms from raw text.
    """
    print("LLM: Calling Gemini to extract symptoms...")
    prompt = f"""
    You are a medical symptom extractor. Your job is to read the following text
    and return ONLY a Python list of the key medical symptoms.
    Use the snake_case format for symptoms (e.g., "high fever" becomes "high_fever").
    
    Example:
    Text: "I have a bad headache and a high fever of 102 degrees, and I feel sick."
    Output: ["headache", "high_fever", "nausea"]
    
    Now, process this text:
    Text: "{raw_text}"
    Output:
    """
    
    try:
        response = await model.generate_content_async(prompt)
        text_response = response.text.strip()
        
        # Find the list inside the response, e.g., "Here is the list: ['a', 'b']"
        match = re.search(r'\[.*?\]', text_response)
        if match:
            symptom_list = eval(match.group(0)) # Safely evaluate the list string
            print(f"LLM: Extracted symptoms: {symptom_list}")
            return symptom_list
        else:
            print("LLM: Error - No list found in Gemini response.")
            return []
            
    except Exception as e:
        print(f"LLM: Error parsing symptoms: {e}. Response was: {response.text}")
        return []

async def generate_final_summary(raw_text: str, ml_results: AuditorResponse) -> str:
    """
    Calls Gemini to generate the final empathetic summary for the patient.
    """
    print("LLM: Calling Gemini to generate final summary...")
    prompt = f"""
    You are "Symptom Storyteller," an empathetic AI assistant.
    Your tone is warm, supportive, and professional.
    
    A patient told you their story:
    "{raw_text}"
    
    Our internal ML model analyzed their symptoms and found these top predictions:
    {ml_results.model_dump_json(indent=2)}
    
    Your job is to combine all this information into a single, helpful summary
    for the patient. Address them directly ("You mentioned...").
    
    1. Start by validating their feelings and summarizing what you heard.
    2. Gently introduce the model's findings, explaining what they mean.
    3. Provide the precautions as helpful next steps.
    4. End with a supportive message, reminding them this is not a final diagnosis
       and that they should consult a doctor.
       
    Keep the summary concise (about 3-4 paragraphs).
    """
    
    try:
        response = await model.generate_content_async(prompt)
        print("LLM: Final summary generated.")
        return response.text
    except Exception as e:
        print(f"LLM: Error generating summary: {e}")
        return "An error occurred while generating your summary. Please try again."