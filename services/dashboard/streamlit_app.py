import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from typing import Tuple, Optional

st.set_page_config(page_title="Genomics Dashboard", layout="wide")

st.title("AI-Enhanced Personalized Treatment Recommendation System")

PATIENT_MANAGEMENT_URL = "http://localhost:8082"

def handle_api_error(response: requests.Response) -> str:
    """Handle API error responses and return user-friendly error messages"""
    try:
        error_data = response.json()
        if isinstance(error_data, dict) and 'detail' in error_data:
            if isinstance(error_data['detail'], dict):
                return f"Error: {error_data['detail'].get('message', 'Unknown error')}"
            return f"Error: {error_data['detail']}"
        return f"Error: {response.text}"
    except:
        return f"Error: {response.text}"

def validate_json_input(json_str: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """Validate JSON input and return (is_valid, parsed_data, error_message)"""
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return False, None, "Input must be a JSON object"
        return True, data, None
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON format: {str(e)}"

# Fetch data from the backend services
@st.cache_data(ttl=5)  # Cache for 5 seconds
def fetch_data():
    try:
        # Fetch all patients
        response = requests.get(f"{PATIENT_MANAGEMENT_URL}/patient")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error(handle_api_error(response))
            return pd.DataFrame()
    except requests.RequestException as e:
        st.error(f"Error connecting to server: {str(e)}")
        return pd.DataFrame()

patients_df = fetch_data()

if not patients_df.empty:
    # Display patient information
    st.header("Patient Information")
    selected_patient = st.selectbox("Select a patient", patients_df['id'].tolist())
    
    # Fetch specific patient data
    response = requests.get(f"{PATIENT_MANAGEMENT_URL}/patient/{selected_patient}")
    if response.status_code == 200:
        patient_info = response.json()
        st.write(f"Name: {patient_info.get('name', 'N/A')}")
        st.write(f"Age: {patient_info.get('age', 'N/A')}")
        
        # Display genomic markers
        st.header("Genomic Markers")
        genomic_markers = patient_info.get('genomic_data', {})
        if genomic_markers:
            st.write(genomic_markers)
        else:
            st.info("No genomic markers available for this patient.")
        
        # Display medical history
        st.header("Medical History")
        medical_history = patient_info.get('medical_history', {})
        if medical_history:
            st.write(medical_history)
        else:
            st.info("No medical history available for this patient.")
        
        # Display treatment recommendations
        st.header("Treatment Recommendations")
        recommendation_response = requests.get(f"{PATIENT_MANAGEMENT_URL}/patient/{selected_patient}/treatment_recommendation")
        if recommendation_response.status_code == 200:
            recommendation = recommendation_response.json()
            st.write(f"Recommended Treatment: {recommendation['treatment']}")
            st.write(f"Efficacy: {recommendation['efficacy']:.2f}")
            
            # Visualize efficacy
            fig = px.bar(x=['Efficacy'], y=[recommendation['efficacy']], range_y=[0, 1],
                         labels={'x': 'Metric', 'y': 'Score'},
                         title='Treatment Efficacy')
            st.plotly_chart(fig)
        else:
            st.error(handle_api_error(recommendation_response))
    else:
        st.error(handle_api_error(response))
else:
    st.warning("No patients found in the system. Please add patients using the form below.")

# Add a form to create a new patient
st.header("Add a New Patient")
with st.form("new_patient_form"):
    patient_id = st.text_input("Patient ID")
    patient_name = st.text_input("Patient Name")
    patient_age = st.number_input("Patient Age", min_value=0, max_value=150)
    genomic_data = st.text_area("Genomic Data (JSON format)")
    medical_history = st.text_area("Medical History (JSON format)")

    submit_button = st.form_submit_button("Add Patient")

    if submit_button:
        # Validate inputs
        if not patient_id or not patient_name or patient_age == 0:
            st.error("Please fill in all required fields (ID, Name, and Age)")
        else:
            # Validate JSON inputs
            is_valid_genomic, genomic_dict, genomic_error = validate_json_input(genomic_data)
            is_valid_medical, medical_dict, medical_error = validate_json_input(medical_history)

            if not is_valid_genomic:
                st.error(f"Invalid Genomic Data: {genomic_error}")
            elif not is_valid_medical:
                st.error(f"Invalid Medical History: {medical_error}")
            else:
                try:
                    new_patient = {
                        "id": patient_id,
                        "name": patient_name,
                        "age": patient_age,
                        "genomic_data": genomic_dict,
                        "medical_history": medical_dict
                    }
                    response = requests.post(f"{PATIENT_MANAGEMENT_URL}/patient", json=new_patient)
                    if response.status_code == 200:
                        st.success("Patient added successfully!")
                        st.experimental_rerun()  # Rerun the app to refresh the patient list
                    else:
                        st.error(handle_api_error(response))
                except Exception as e:
                    st.error(f"Error adding patient: {str(e)}")

# Add more visualizations and interactive elements as needed
