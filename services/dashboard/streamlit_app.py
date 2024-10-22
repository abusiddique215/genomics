import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

st.set_page_config(page_title="Genomics Dashboard", layout="wide")

st.title("AI-Enhanced Personalized Treatment Recommendation System")

PATIENT_MANAGEMENT_URL = "http://localhost:8082"

# Fetch data from the backend services
@st.cache_data(ttl=5)  # Cache for 5 seconds
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
            st.error(f"Unable to fetch treatment recommendations: {recommendation_response.text}")
    else:
        st.error(f"Error fetching patient data: {response.text}")
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
        try:
            new_patient = {
                "id": patient_id,
                "name": patient_name,
                "age": patient_age,
                "genomic_data": eval(genomic_data),
                "medical_history": eval(medical_history)
            }
            response = requests.post(f"{PATIENT_MANAGEMENT_URL}/patient", json=new_patient)
            if response.status_code == 200:
                st.success("Patient added successfully!")
                st.experimental_rerun()  # Rerun the app to refresh the patient list
            else:
                st.error(f"Error adding patient: {response.text}")
        except Exception as e:
            st.error(f"Error adding patient: {str(e)}")

# Add more visualizations and interactive elements as needed
