import streamlit as st
import sqlite3
import google.generativeai as genai
from datetime import date

# Configure Gemini AI
genai.configure(api_key="write the API Key")
model = genai.GenerativeModel("gemini-2.5-flash")

# Database setup
def init_db():
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            email TEXT NOT NULL,
            glucose REAL NOT NULL,
            haemoglobin REAL NOT NULL,
            cholesterol REAL NOT NULL,
            remarks TEXT
        )
    """)
    conn.commit()
    conn.close()

# Get AI prediction
def get_ai_prediction(glucose, haemoglobin, cholesterol):
    prompt = f"""
    A patient has the following blood test results:
    - Glucose: {glucose} mg/dL
    - Haemoglobin: {haemoglobin} g/dL
    - Cholesterol: {cholesterol} mg/dL
    Based on these values give a brief 2 line health prediction and possible risk.
    """
    response = model.generate_content(prompt)
    return response.text

# Initialize database
init_db()

# App title
st.title("MIRA - Health Prediction App")
st.markdown("Medical Intelligence - Patient Blood Test Records")

# Add Patient Form
st.subheader("Add New Patient")
with st.form("add_form"):
    full_name = st.text_input("Full Name")
    dob = st.date_input("Date of Birth", min_value=date(1900, 1, 1), max_value=date.today(), value=date(1990, 1, 1))
    email = st.text_input("Email Address")
    glucose = st.number_input("Glucose (mg/dL)", min_value=0.0)
    haemoglobin = st.number_input("Haemoglobin (g/dL)", min_value=0.0)
    cholesterol = st.number_input("Cholesterol (mg/dL)", min_value=0.0)
    submitted = st.form_submit_button("Add Patient")

    if submitted:
        if not full_name or not email or "@" not in email:
            st.error("Please enter valid name and email!")
        else:
            remarks = get_ai_prediction(glucose, haemoglobin, cholesterol)
            conn = sqlite3.connect("patients.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patients (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (full_name, str(dob), email, glucose, haemoglobin, cholesterol, remarks))
            conn.commit()
            conn.close()
            st.success("Patient added successfully!")
            st.rerun()

# View All Patients
st.subheader("All Patient Records")
conn = sqlite3.connect("patients.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM patients")
patients = cursor.fetchall()
conn.close()

if patients:
    for patient in patients:
        with st.expander(f"Patient: {patient[1]}"):
            st.write(f"Date of Birth: {patient[2]}")
            st.write(f"Email: {patient[3]}")
            st.write(f"Glucose: {patient[4]}")
            st.write(f"Haemoglobin: {patient[5]}")
            st.write(f"Cholesterol: {patient[6]}")
            st.write(f"AI Remarks: {patient[7]}")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Edit", key=f"edit_{patient[0]}"):
                    st.session_state[f"editing_{patient[0]}"] = True

            with col2:
                if st.button("Delete", key=f"del_{patient[0]}"):
                    conn = sqlite3.connect("patients.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM patients WHERE id=?", (patient[0],))
                    conn.commit()
                    conn.close()
                    st.rerun()

            with col3:
                if st.button("Refresh AI", key=f"ref_{patient[0]}"):
                    new_remarks = get_ai_prediction(patient[4], patient[5], patient[6])
                    conn = sqlite3.connect("patients.db")
                    cursor = conn.cursor()
                    cursor.execute("UPDATE patients SET remarks=? WHERE id=?", (new_remarks, patient[0]))
                    conn.commit()
                    conn.close()
                    st.rerun()

            if st.session_state.get(f"editing_{patient[0]}", False):
                with st.form(key=f"edit_form_{patient[0]}"):
                    new_name = st.text_input("Full Name", value=patient[1])
                    new_dob = st.date_input("Date of Birth", min_value=date(1900,1,1), max_value=date.today(), value=date.fromisoformat(patient[2]))
                    new_email = st.text_input("Email", value=patient[3])
                    new_glucose = st.number_input("Glucose", min_value=0.0, value=float(patient[4]))
                    new_haemoglobin = st.number_input("Haemoglobin", min_value=0.0, value=float(patient[5]))
                    new_cholesterol = st.number_input("Cholesterol", min_value=0.0, value=float(patient[6]))
                    save = st.form_submit_button("Save Changes")

                    if save:
                        new_remarks = get_ai_prediction(new_glucose, new_haemoglobin, new_cholesterol)
                        conn = sqlite3.connect("patients.db")
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE patients SET full_name=?, dob=?, email=?, glucose=?, haemoglobin=?, cholesterol=?, remarks=?
                            WHERE id=?
                        """, (new_name, str(new_dob), new_email, new_glucose, new_haemoglobin, new_cholesterol, new_remarks, patient[0]))
                        conn.commit()
                        conn.close()
                        st.session_state[f"editing_{patient[0]}"] = False
                        st.success("Patient updated successfully!")
                        st.rerun()
else:
    st.info("No patient records found. Add a patient above!")