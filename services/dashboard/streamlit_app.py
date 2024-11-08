import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8080"

# Page config
st.set_page_config(
    page_title="Genomics Treatment Dashboard",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Patient Management", "Treatment Analysis", "Progress Tracking"])

def fetch_patients():
    """Fetch patients from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/patients")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching patients: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

def add_patient(patient_data):
    """Add a new patient"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/patients",
            json=patient_data
        )
        if response.status_code == 200:
            st.success("Patient added successfully!")
            return True
        else:
            st.error(f"Error adding patient: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def get_treatment_recommendation(patient_id):
    """Get treatment recommendation for a patient"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/patients/{patient_id}/treatment_recommendation"
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error getting recommendation: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Dashboard page
if page == "Dashboard":
    st.title("Genomics Treatment Dashboard")
    
    # Fetch patients
    patients = fetch_patients()
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Patients", len(patients))
    
    with col2:
        if patients:
            recommendations = [
                get_treatment_recommendation(p['id']) for p in patients
            ]
            efficacies = [
                float(r['efficacy']) for r in recommendations if r and 'efficacy' in r
            ]
            avg_efficacy = sum(efficacies) / len(efficacies) if efficacies else 0
            st.metric("Average Treatment Efficacy", f"{avg_efficacy:.1%}")
    
    with col3:
        if patients:
            high_conf = sum(
                1 for r in recommendations 
                if r and r.get('confidence_level') == 'high'
            )
            st.metric("High Confidence Predictions", high_conf)
    
    # Display patient list
    if patients:
        st.subheader("Patient List")
        df = pd.DataFrame(patients)
        st.dataframe(df)

# Patient Management page
elif page == "Patient Management":
    st.title("Patient Management")
    
    # Add new patient form
    st.subheader("Add New Patient")
    
    with st.form("new_patient_form"):
        patient_id = st.text_input("Patient ID")
        name = st.text_input("Patient Name")
        age = st.number_input("Patient Age", min_value=0, max_value=120)
        genomic_data = st.text_area("Genomic Data (JSON format)")
        medical_history = st.text_area("Medical History (JSON format)")
        
        submit = st.form_submit_button("Add Patient")
        
        if submit:
            try:
                patient_data = {
                    "id": patient_id,
                    "name": name,
                    "age": str(age),
                    "genomic_data": json.loads(genomic_data),
                    "medical_history": json.loads(medical_history)
                }
                if add_patient(patient_data):
                    st.success("Patient added successfully!")
            except json.JSONDecodeError:
                st.error("Invalid JSON format in genomic data or medical history")
    
    # Display existing patients
    st.subheader("Patient List")
    patients = fetch_patients()
    if patients:
        for patient in patients:
            with st.expander(f"Patient: {patient['name']} (ID: {patient['id']})"):
                st.json(patient)
                if st.button(f"Get Treatment Recommendation for {patient['id']}"):
                    recommendation = get_treatment_recommendation(patient['id'])
                    if recommendation:
                        st.json(recommendation)

# Treatment Analysis page
elif page == "Treatment Analysis":
    st.title("Treatment Analysis")
    
    patients = fetch_patients()
    if patients:
        recommendations = [
            get_treatment_recommendation(p['id']) for p in patients
        ]
        
        # Create visualization data
        treatment_data = []
        for p, r in zip(patients, recommendations):
            if r:
                treatment_data.append({
                    'patient_id': p['id'],
                    'treatment': r.get('recommended_treatment', 'Unknown'),
                    'efficacy': float(r.get('efficacy', 0)),
                    'confidence': r.get('confidence_level', 'Unknown')
                })
        
        if treatment_data:
            df = pd.DataFrame(treatment_data)
            
            # Treatment distribution
            st.subheader("Treatment Distribution")
            fig = px.pie(df, names='treatment')
            st.plotly_chart(fig)
            
            # Efficacy distribution
            st.subheader("Treatment Efficacy Distribution")
            fig = px.histogram(df, x='efficacy')
            st.plotly_chart(fig)

# Progress Tracking page
elif page == "Progress Tracking":
    st.title("Patient Progress Tracking")
    
    patients = fetch_patients()
    if patients:
        selected_patient = st.selectbox(
            "Select Patient",
            options=[p['id'] for p in patients],
            format_func=lambda x: f"{next(p['name'] for p in patients if p['id'] == x)} (ID: {x})"
        )
        
        if selected_patient:
            patient = next(p for p in patients if p['id'] == selected_patient)
            st.json(patient)
            
            recommendation = get_treatment_recommendation(selected_patient)
            if recommendation:
                st.subheader("Treatment Recommendation")
                st.json(recommendation)
    else:
        st.warning("No patients found")

# Add refresh button
if st.button("Refresh Data"):
    st.rerun()
