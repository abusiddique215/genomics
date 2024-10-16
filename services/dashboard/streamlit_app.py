import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

st.set_page_config(page_title="Genomics Dashboard", layout="wide")

st.title("AI-Enhanced Personalized Treatment Recommendation System")

# Fetch data from the backend services
@st.cache_data  # This should work with the latest Streamlit version
def fetch_data():
    try:
        # Update these endpoints to match your actual service URLs
        patient_data = requests.get("http://localhost:8002/patients").json()
        treatment_data = requests.get("http://localhost:8004/treatments").json()
        return pd.DataFrame(patient_data), pd.DataFrame(treatment_data)
    except requests.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame(), pd.DataFrame()

patients_df, treatments_df = fetch_data()

if not patients_df.empty and not treatments_df.empty:
    # Display patient information
    st.header("Patient Information")
    selected_patient = st.selectbox("Select a patient", patients_df['patient_id'].tolist())
    patient_info = patients_df[patients_df['patient_id'] == selected_patient].iloc[0]
    st.write(f"Name: {patient_info.get('name', 'N/A')}")
    st.write(f"Age: {patient_info.get('age', 'N/A')}")
    st.write(f"Gender: {patient_info.get('gender', 'N/A')}")

    # Display treatment recommendations
    st.header("Treatment Recommendations")
    patient_treatments = treatments_df[treatments_df['patient_id'] == selected_patient]
    if not patient_treatments.empty:
        fig = px.bar(patient_treatments, x='treatment', y='efficacy', title='Treatment Efficacy')
        st.plotly_chart(fig)
    else:
        st.write("No treatment data available for this patient.")

    # Display genomic markers
    st.header("Genomic Markers")
    genomic_markers = patient_info.get('genomic_markers', [])
    if genomic_markers:
        st.write(genomic_markers)
    else:
        st.write("No genomic markers available for this patient.")

else:
    st.error("Unable to fetch data. Please check if the backend services are running.")

# Add more visualizations and interactive elements as needed
