# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import base64
from datetime import datetime, timedelta
import plotly.express as px

API_URL = "http://127.0.0.1:8000"  # Adjust if your backend runs elsewhere
LOGO_PATH = "frontend/images/logo.png"

def get_image_base64(image_path: str) -> str:
    """Encodes the specified image in base64 for inline display."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Image not found: {image_path}")
        return ""

# Set up the Streamlit page layout
st.set_page_config(
    page_title="FleetPilot",
    layout="wide"
)

# ----- API Helper Functions -----
def login_user(username: str, password: str) -> bool:
    """Attempts to log in the user with given credentials; returns True if successful."""
    try:
        resp = requests.post(
            f"{API_URL}/auth/login", 
            data={"username": username, "password": password}
        )
        if resp.status_code == 200:
            data = resp.json()
            # Store the token in session state
            st.session_state["token"] = data["access_token"]
            st.session_state["logged_in"] = True
            return True
        else:
            st.error("Invalid credentials or connection error.")
    except requests.exceptions.ConnectionError:
        st.error("API connection error. Please check if the backend is running.")
    except Exception as e:
        st.error(f"Login error: {str(e)}")
    return False

def get_api_data(endpoint: str):
    """Generic function to fetch data from the API using the stored auth token."""
    if "token" not in st.session_state:
        return None
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.get(f"{API_URL}/{endpoint}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch data from '{endpoint}'. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Communication error with the API: {str(e)}")
        return None

def post_api_data(endpoint: str, data: dict) -> bool:
    """Generic function to post JSON data to the API using the stored auth token."""
    if "token" not in st.session_state:
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.post(f"{API_URL}/{endpoint}", headers=headers, json=data)
        if response.status_code in [200, 201]:
            return True
        else:
            st.error(f"Failed to send data to '{endpoint}'. Status code: {response.status_code}")
            if response.text:
                st.error(response.text)
            return False
    except Exception as e:
        st.error(f"Communication error with the API: {str(e)}")
        return False

# ----- Initialize Session State -----
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ----- Login Screen -----
if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>FleetPilot</h1>", unsafe_allow_html=True)
    
    image_base64 = get_image_base64(LOGO_PATH)
    if image_base64:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center;">
                <img src="data:image/png;base64,{image_base64}" width="150"
                     style="border-radius: 50%; border: 2px solid #ddd; 
                            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("<h4 style='text-align: center; color: gray;'>Intelligent Fleet Management</h4>", unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if login_user(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials or connection error.")
    st.stop()

# ----- Main App (Logged In) -----
st.sidebar.image(LOGO_PATH, width=60)
st.sidebar.title("FleetPilot")

menu = st.sidebar.radio(
    "Menu", 
    ["Dashboard", "Companies", "Machines", "Maintenances", "Settings", "Logout"]
)

# -----------------------------------------------------------------------------
#                                DASHBOARD
# -----------------------------------------------------------------------------
if menu == "Dashboard":
    st.title("Fleet Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    # Fetch data from the API
    machines = get_api_data("machines") or []
    maintenances = get_api_data("maintenances") or []
    
    # Calculate upcoming maintenances within 7 days
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    # In your backend, "scheduled_date" might be the field name
    upcoming_maintenances = []
    for m in maintenances:
        # Convert "scheduled_date" from string to date
        sched_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
        if today <= sched_date <= next_week:
            upcoming_maintenances.append(m)
    
    col1.metric("Total Machines", len(machines))
    col2.metric("Upcoming Maintenances", len(upcoming_maintenances))
    col3.metric("Companies", "1")  # Replace with a real count if needed
    
    # Pie chart for machine types
    if machines:
        type_counts = {}
        for m in machines:
            machine_type = m["type"]
            type_counts[machine_type] = type_counts.get(machine_type, 0) + 1
        
        df_types = pd.DataFrame({
            "Machine Type": list(type_counts.keys()),
            "Count": list(type_counts.values())
        })
        
        fig = px.pie(df_types, values="Count", names="Machine Type", title="Distribution by Machine Type")
        st.plotly_chart(fig)
    
    # Display upcoming maintenances
    if upcoming_maintenances:
        st.subheader("Upcoming Maintenances (next 7 days)")
        st.dataframe(pd.DataFrame(upcoming_maintenances))
    else:
        st.info("No maintenances scheduled in the next 7 days.")

# -----------------------------------------------------------------------------
#                               COMPANIES
# -----------------------------------------------------------------------------
elif menu == "Companies":
    st.title("Company Management")
    
    with st.form("new_company"):
        st.subheader("Add New Company")
        company_name = st.text_input("Company Name")
        submitted = st.form_submit_button("Add")
        
        if submitted and company_name:
            # "name" is what your schema expects for CompanyCreate
            if post_api_data("companies", {"name": company_name}):
                st.success(f"Company '{company_name}' added successfully!")
    
    st.subheader("Existing Companies")
    companies = get_api_data("companies")
    
    if companies:
        # Each company is expected to have {"id": ..., "name": ...}
        for comp in companies:
            st.write(f"**{comp['name']}** (ID: {comp['id']})")
    else:
        st.info("No companies found.")

# -----------------------------------------------------------------------------
#                               MACHINES
# -----------------------------------------------------------------------------
elif menu == "Machines":
    st.title("Machine Management")
    
    # Fetch companies for the dropdown
    companies = get_api_data("companies") or []
    
    with st.form("new_machine"):
        st.subheader("Add New Machine")
        machine_name = st.text_input("Machine Name")
        # Based on your schema, possible types are "truck" or "fixed"
        machine_type = st.selectbox("Type", ["truck", "fixed"])
        
        # The user will select a company by ID
        company_options = [c["id"] for c in companies]
        selected_company_id = st.selectbox(
            "Company",
            options=company_options,
            format_func=lambda cid: next((c["name"] for c in companies if c["id"] == cid), str(cid))
        )
        
        submitted = st.form_submit_button("Add")
        
        if submitted and machine_name and selected_company_id:
            # According to the schema: {"name": str, "type": str, "company_id": int}
            payload = {
                "name": machine_name,
                "type": machine_type,
                "company_id": selected_company_id
            }
            if post_api_data("machines", payload):
                st.success(f"Machine '{machine_name}' added successfully!")
    
    st.subheader("Existing Machines")
    machines = get_api_data("machines")
    
    if machines:
        # Convert to a DataFrame
        df_machines = pd.DataFrame(machines)
        
        # Add the company name for readability
        def get_company_name(cid):
            for c in companies:
                if c["id"] == cid:
                    return c["name"]
            return "Unknown"
        
        if "company_id" in df_machines.columns:
            df_machines["company_name"] = df_machines["company_id"].apply(get_company_name)
        
        st.dataframe(df_machines)
    else:
        st.info("No machines found.")

# -----------------------------------------------------------------------------
#                              MAINTENANCES
# -----------------------------------------------------------------------------
elif menu == "Maintenances":
    st.title("Maintenance Scheduling")
    
    # Fetch machines for the form
    machines = get_api_data("machines") or []
    
    with st.form("new_maintenance"):
        st.subheader("Schedule New Maintenance")
        
        # Let user pick a machine
        machine_options = [m["id"] for m in machines]
        chosen_machine_id = st.selectbox(
            "Machine",
            options=machine_options,
            format_func=lambda mid: next(
                (f"{m['name']} ({m['type']})" for m in machines if m['id'] == mid),
                str(mid)
            )
        )
        
        # Types of maintenance
        # You can store them in English, e.g. ["Oil Change", "Full Review", "Filters", "Tires", "Other"]
        # Must match your backend if you're storing them as strings
        maintenance_type = st.selectbox(
            "Maintenance Type",
            ["Oil Change", "Full Review", "Filters", "Tires", "Other"]
        )
        
        final_type = maintenance_type
        if maintenance_type == "Other":
            user_type = st.text_input("Specify the maintenance type")
            if user_type:
                final_type = user_type
        
        scheduled_date = st.date_input(
            "Scheduled Date",
            min_value=datetime.now().date(),
            value=datetime.now().date() + timedelta(days=7)
        )
        
        submitted = st.form_submit_button("Schedule")
        
        if submitted and chosen_machine_id:
            # According to MaintenanceCreate, we send: {"machine_id", "type", "scheduled_date"}
            data = {
                "machine_id": chosen_machine_id,
                "type": final_type,
                "scheduled_date": scheduled_date.isoformat()
            }
            if post_api_data("maintenances", data):
                st.success(f"Maintenance scheduled on {scheduled_date}!")
    
    st.subheader("Scheduled Maintenances")
    maintenances = get_api_data("maintenances")
    
    if maintenances:
        # Convert to DataFrame
        df_maint = pd.DataFrame(maintenances)
        
        # Convert "scheduled_date" to datetime
        if "scheduled_date" in df_maint.columns:
            df_maint["scheduled_date"] = pd.to_datetime(df_maint["scheduled_date"])
        
        # Add machine name
        def get_machine_name(mid):
            for m in machines:
                if m["id"] == mid:
                    return m["name"]
            return "Unknown"
        
        if "machine_id" in df_maint.columns:
            df_maint["machine_name"] = df_maint["machine_id"].apply(get_machine_name)
        
        # Sort by date
        if "scheduled_date" in df_maint.columns:
            df_maint = df_maint.sort_values("scheduled_date")
        
        # Simple highlight for overdue / soon
        today = datetime.now().date()
        
        def highlight_row(row):
            if "scheduled_date" not in row:
                return [""] * len(row)
            date_val = row["scheduled_date"].date()
            if date_val <= today:
                return ["background-color: #ffcccc"] * len(row)  # Light red
            elif (date_val - today).days <= 7:
                return ["background-color: #ffffcc"] * len(row)  # Light yellow
            else:
                return [""] * len(row)
        
        st.dataframe(df_maint.style.apply(highlight_row, axis=1))
    else:
        st.info("No maintenances scheduled.")

# -----------------------------------------------------------------------------
#                               SETTINGS
# -----------------------------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    
    st.subheader("Notification Settings")
    st.write("Configure the phone number to receive SMS alerts for maintenances.")
    
    phone_number = st.text_input("Phone Number (with country code)", value="351911234567")
    if st.button("Save Settings"):
        # In production, save to DB or call an endpoint
        st.success("Settings saved successfully!")
    
    st.subheader("Company Profile")
    company_name = st.text_input("Company Name", value="My Company")
    contact_email = st.text_input("Contact Email", value="contact@mycompany.com")
    
    if st.button("Update Profile"):
        # In production, save to DB or call an endpoint
        st.success("Profile updated successfully!")

# -----------------------------------------------------------------------------
#                                LOGOUT
# -----------------------------------------------------------------------------
elif menu == "Logout":
    st.write("Confirm to logout?")
    if st.button("Confirm Logout"):
        st.session_state.clear()
        st.rerun()
