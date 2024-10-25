import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configure page
st.set_page_config(page_title="Genomics Treatment Dashboard", layout="wide")

# API endpoints
PATIENT_API = "http://localhost:8501"
TREATMENT_API = "http://localhost:8083"
DATA_INGESTION_API = "http://localhost:8084"

def load_patient_data():
    """Load all patient data"""
    try:
        response = requests.get(f"{PATIENT_API}/patient")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_treatment_recommendation(patient_id):
    """Get treatment recommendation for a patient"""
    try:
        response = requests.get(f"{PATIENT_API}/patient/{patient_id}/treatment_recommendation")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_patient_progress(patient_id):
    """Get progress history for a patient"""
    try:
        response = requests.get(f"{PATIENT_API}/patient/{patient_id}/progress")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_progress_analysis(patient_id):
    """Get progress analysis for a patient"""
    try:
        response = requests.get(f"{PATIENT_API}/patient/{patient_id}/progress/analysis")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Patient Management", "Treatment Analysis", "Progress Tracking"])

if page == "Dashboard":
    st.title("Genomics Treatment Dashboard")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    patients = load_patient_data()
    
    with col1:
        st.metric("Total Patients", len(patients))
    
    with col2:
        # Calculate average treatment efficacy
        efficacies = []
        for patient in patients:
            rec = get_treatment_recommendation(patient['id'])
            if rec and 'efficacy' in rec:
                efficacies.append(rec['efficacy'])
        avg_efficacy = np.mean(efficacies) if efficacies else 0
        st.metric("Average Treatment Efficacy", f"{avg_efficacy:.2%}")
    
    with col3:
        # Count high confidence predictions
        high_conf = sum(1 for e in efficacies if e > 0.8)
        st.metric("High Confidence Predictions", high_conf)
    
    # Treatment distribution chart
    st.subheader("Treatment Distribution")
    treatment_counts = {}
    for patient in patients:
        rec = get_treatment_recommendation(patient['id'])
        if rec and 'recommended_treatment' in rec:
            treatment = rec['recommended_treatment']
            treatment_counts[treatment] = treatment_counts.get(treatment, 0) + 1
    
    if treatment_counts:
        fig = px.pie(
            values=list(treatment_counts.values()),
            names=list(treatment_counts.keys()),
            title="Treatment Distribution"
        )
        st.plotly_chart(fig)
    
    # Efficacy distribution
    st.subheader("Treatment Efficacy Distribution")
    if efficacies:
        fig = px.histogram(
            x=efficacies,
            nbins=20,
            title="Treatment Efficacy Distribution"
        )
        st.plotly_chart(fig)

elif page == "Patient Management":
    st.title("Patient Management")
    
    # Add new patient form
    st.header("Add New Patient")
    with st.form("new_patient_form"):
        patient_id = st.text_input("Patient ID")
        patient_name = st.text_input("Patient Name")
        age = st.number_input("Patient Age", min_value=0, max_value=150)
        genomic_data = st.text_area("Genomic Data (JSON format)")
        medical_history = st.text_area("Medical History (JSON format)")
        
        submit_button = st.form_submit_button("Add Patient")
        
        if submit_button:
            try:
                genomic_json = json.loads(genomic_data)
                medical_json = json.loads(medical_history)
                
                patient_data = {
                    "id": patient_id,
                    "name": patient_name,
                    "age": age,
                    "genomic_data": genomic_json,
                    "medical_history": medical_json
                }
                
                response = requests.post(f"{PATIENT_API}/patient", json=patient_data)
                if response.status_code == 200:
                    st.success("Patient added successfully!")
                else:
                    st.error("Failed to add patient")
            except json.JSONDecodeError:
                st.error("Invalid JSON format in genomic data or medical history")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Patient list
    st.header("Patient List")
    patients = load_patient_data()
    if patients:
        patient_df = pd.DataFrame(patients)
        st.dataframe(patient_df)

elif page == "Treatment Analysis":
    st.title("Treatment Analysis")
    
    # Patient selection
    patients = load_patient_data()
    if not patients:
        st.warning("No patients found")
    else:
        selected_patient = st.selectbox(
            "Select Patient",
            options=[p['id'] for p in patients],
            format_func=lambda x: f"Patient {x}"
        )
        
        if selected_patient:
            # Get treatment recommendation
            rec = get_treatment_recommendation(selected_patient)
            if rec:
                # Display recommendation details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Treatment Recommendation")
                    st.write(f"Recommended Treatment: {rec['recommended_treatment']}")
                    st.write(f"Efficacy: {rec['efficacy']:.2%}")
                    st.write(f"Confidence Level: {rec['confidence_level'].title()}")
                
                with col2:
                    # Efficacy gauge
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = rec['efficacy'] * 100,
                        title = {'text': "Treatment Efficacy"},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 60], 'color': "red"},
                                {'range': [60, 80], 'color': "yellow"},
                                {'range': [80, 100], 'color': "green"}
                            ]
                        }
                    ))
                    st.plotly_chart(fig)
                
                # Patient details
                st.subheader("Patient Details")
                patient_data = next((p for p in patients if p['id'] == selected_patient), None)
                if patient_data:
                    st.json(patient_data)

elif page == "Progress Tracking":
    st.title("Patient Progress Tracking")
    
    # Patient selection
    patients = load_patient_data()
    if not patients:
        st.warning("No patients found")
    else:
        selected_patient = st.selectbox(
            "Select Patient",
            options=[p['id'] for p in patients],
            format_func=lambda x: f"Patient {x}"
        )
        
        if selected_patient:
            # Add progress entry
            st.header("Add Progress Entry")
            with st.form("progress_entry_form"):
                efficacy_score = st.slider("Treatment Efficacy Score", 0.0, 1.0, 0.5)
                side_effects = st.multiselect(
                    "Side Effects",
                    ["Nausea", "Fatigue", "Headache", "Dizziness", "None"]
                )
                notes = st.text_area("Notes")
                next_appointment = st.date_input("Next Appointment")
                
                submit_button = st.form_submit_button("Add Progress Entry")
                
                if submit_button:
                    progress_data = {
                        "treatment": get_treatment_recommendation(selected_patient)['recommended_treatment'],
                        "efficacy_score": efficacy_score,
                        "side_effects": side_effects,
                        "notes": notes,
                        "next_appointment": next_appointment.isoformat()
                    }
                    
                    response = requests.post(
                        f"{PATIENT_API}/patient/{selected_patient}/progress",
                        json=progress_data
                    )
                    
                    if response.status_code == 200:
                        st.success("Progress entry added successfully!")
                    else:
                        st.error("Failed to add progress entry")
            
            # Progress history
            st.header("Progress History")
            progress_entries = get_patient_progress(selected_patient)
            
            if progress_entries:
                # Progress timeline
                progress_df = pd.DataFrame(progress_entries)
                progress_df['timestamp'] = pd.to_datetime(progress_df['timestamp'])
                
                fig = px.line(
                    progress_df,
                    x='timestamp',
                    y='efficacy_score',
                    title="Treatment Efficacy Over Time"
                )
                st.plotly_chart(fig)
                
                # Progress analysis
                analysis = get_progress_analysis(selected_patient)
                if analysis:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Average Efficacy", f"{analysis['average_efficacy']:.2%}")
                    
                    with col2:
                        st.metric("Treatment Duration", f"{analysis['treatment_duration']} days")
                    
                    with col3:
                        st.metric("Progress Trend", analysis['trend'].title())
                    
                    # Side effects summary
                    if analysis['side_effects_summary']:
                        st.subheader("Side Effects Summary")
                        fig = px.bar(
                            x=list(analysis['side_effects_summary'].keys()),
                            y=list(analysis['side_effects_summary'].values()),
                            title="Side Effects Frequency"
                        )
                        st.plotly_chart(fig)
                
                # Detailed progress entries
                st.subheader("Progress Entries")
                for entry in progress_entries:
                    with st.expander(f"Entry from {entry['timestamp']}"):
                        st.write(f"Treatment: {entry['treatment']}")
                        st.write(f"Efficacy Score: {entry['efficacy_score']:.2%}")
                        st.write(f"Side Effects: {', '.join(entry['side_effects']) if entry['side_effects'] else 'None'}")
                        st.write(f"Notes: {entry['notes']}")
                        st.write(f"Next Appointment: {entry['next_appointment']}")

# Footer
st.markdown("---")
st.markdown("Genomics Treatment Recommendation System - Dashboard")
