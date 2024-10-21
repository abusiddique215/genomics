import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

st.set_page_config(page_title="Genomics Dashboard", layout="wide")

st.title("AI-Enhanced Personalized Treatment Recommendation System")

PATIENT_MANAGEMENT_URL = "http://localhost:8080"

# Fetch data from the backend services
@st.cache_data
def fetch_data():
    try:
        # Fetch all patients
        response = requests.get(f"{PATIENT_MANAGEMENT_URL}/patient")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error(f"Error fetching patient data: {response.text}")
            return pd.DataFrame()
    except requests.RequestException as e:
        st.error(f"Error fetching data: {e}")
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
            st.write("No genomic markers available for this patient.")
        
        # Display medical history
        st.header("Medical History")
        medical_history = patient_info.get('medical_history', {})
        if medical_history:
            st.write(medical_history)
        else:
            st.write("No medical history available for this patient.")
        
        # Here you would add the treatment recommendations section
        # This would involve calling the treatment prediction service
        # For now, we'll use a placeholder
        st.header("Treatment Recommendations")
        st.write("Treatment recommendations will be displayed here once the treatment prediction service is integrated.")
    else:
        st.error(f"Error fetching patient data: {response.text}")
else:
    st.error("Unable to fetch patient data. Please check if the patient_management service is running.")

# Add more visualizations and interactive elements as needed
