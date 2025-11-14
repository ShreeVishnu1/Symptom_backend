import pickle
import pandas as pd
import numpy as np
from ..models import AuditorResponse, Prediction # Import Pydantic models
from typing import List

class AuditorService:
    model = None
    label_encoder = None
    symptom_columns = None
    severity_lookup = None
    desc_lookup = None
    prec_lookup = None

    def load_model(self):
        """
        Loads all ML models and data files from the /models and /data
        directories into memory. This is called once on app startup.
        """
        print("AuditorService: Loading models and data...")
        try:
            with open("models/ExtraTrees.pkl", "rb") as f:
                self.model = pickle.load(f)
                
            with open("models/le.pkl", "rb") as f:
                self.label_encoder = pickle.load(f)
                
            with open("models/symptom_columns.pkl", "rb") as f:
                self.symptom_columns = pickle.load(f)

            # Load CSVs and convert them to fast lookup dictionaries
            df_severity = pd.read_csv('data/Symptom-severity.csv')
            # Clean symptom names to match (e.g., 'high_fever')
            self.severity_lookup = pd.Series(
                df_severity.weight.values, 
                index=df_severity.Symptom.str.strip().str.replace(' ', '_')
            ).to_dict()
            
            df_desc = pd.read_csv('data/symptom_Description.csv')
            self.desc_lookup = pd.Series(
                df_desc.Description.values, 
                index=df_desc.Disease
            ).to_dict()
            
            self.prec_lookup = pd.read_csv('data/symptom_precaution.csv').set_index('Disease')
            
            print("AuditorService: All models and data loaded successfully.")
            
        except FileNotFoundError as e:
            print(f"FATAL AUDITOR ERROR: Missing file {e.filename}")
            # You could raise the exception here to stop the server
        except Exception as e:
            print(f"FATAL AUDITOR ERROR: {e}")

    def predict(self, patient_symptoms_list: List[str]) -> AuditorResponse:
        """
        Takes a list of symptoms from the LLM and predicts a disease.
        """
        if self.model is None:
            return AuditorResponse(predictions=[]) # Return empty if model failed to load

        print(f"AuditorService: Predicting for symptoms: {patient_symptoms_list}")
        
        # 1. Create the input vector (a row of zeros)
        input_vector = pd.Series(0, index=self.symptom_columns)
        
        # 2. Populate the vector with severity weights
        for symptom in patient_symptoms_list:
            symptom_cleaned = symptom.strip().replace(' ', '_')
            if symptom_cleaned in input_vector.index:
                # Use the weighted severity!
                weight = self.severity_lookup.get(symptom_cleaned, 1) # Default to 1 if not found
                input_vector[symptom_cleaned] = weight
            else:
                print(f"AuditorService: Warning - symptom '{symptom}' not in columns.")
        
        # 3. Reshape for the model
        input_array = input_vector.values.reshape(1, -1)
        
        # 4. Run prediction
        proba = self.model.predict_proba(input_array)[0]
        top3_idx = np.argsort(proba)[-3:][::-1] # Get top 3
        
        top3_names = self.label_encoder.inverse_transform(top3_idx)
        top3_proba = proba[top3_idx]
        
        # 5. Format the output using Pydantic models
        predictions = []
        for disease, prob in zip(top3_names, top3_proba):
            if prob < 0.05: continue # Filter out very low probability
                
            # Get precautions
            prec_dict = {}
            try:
                # Use .get(col) to avoid errors if a precaution is missing (NaN)
                prec_row = self.prec_lookup.loc[disease]
                prec_dict = {
                    "precaution_1": prec_row.get('Precaution_1'),
                    "precaution_2": prec_row.get('Precaution_2'),
                    "precaution_3": prec_row.get('Precaution_3'),
                    "precaution_4": prec_row.get('Precaution_4'),
                }
            except KeyError:
                prec_dict = {"info": "No precautions available."}

            predictions.append(
                Prediction(
                    disease=str(disease),
                    probability=f"{prob*100:.2f}%",
                    description=self.desc_lookup.get(disease, "No description available."),
                    precautions=prec_dict
                )
            )
            
        print(f"AuditorService: Predictions complete.")
        return AuditorResponse(predictions=predictions)

# Create a single global instance that the rest of the app will import
auditor = AuditorService()