# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import base64
from datetime import datetime, timedelta
import plotly.express as px
import json
import os
from PIL import Image

API_URL = "http://127.0.0.1:8000"  # Adjust if your backend runs elsewhere
LOGO_PATH = "frontend/images/logo.png"
DEFAULT_LOGO_PATH = "frontend/images/logo.png"

def get_image_base64(image_path: str) -> str:
    """Encodes the specified image in base64 for inline display."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Image not found: {image_path}")
        return ""

def upload_file_to_api(endpoint: str, file_key: str, file_path: str, file_name: str = None):
    """Envia um arquivo para o backend."""
    if "token" not in st.session_state:
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    
    try:
        with open(file_path, "rb") as file:
            file_name = file_name or os.path.basename(file_path)
            files = {file_key: (file_name, file, "multipart/form-data")}
            response = requests.post(f"{API_URL}/{endpoint}", headers=headers, files=files)
            
            if response.status_code in [200, 201]:
                return True
            else:
                st.error(f"Falha ao enviar arquivo para '{endpoint}'. Status code: {response.status_code}")
                if response.text:
                    st.error(response.text)
                return False
    except Exception as e:
        st.error(f"Erro de comunicação com a API: {str(e)}")
        return False

def get_company_logo_path(logo_relative_path: str) -> str:
    """Retorna o caminho completo do logo da empresa."""
    if not logo_relative_path:
        return DEFAULT_LOGO_PATH  # Retorna o logo padrão
    
    # Caminho completo para a pasta de imagens
    image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
    logo_path = os.path.join(image_dir, logo_relative_path)
    
    # Verificar se o arquivo existe
    if os.path.exists(logo_path):
        return logo_path
    else:
        return DEFAULT_LOGO_PATH  # Retorna o logo padrão se o arquivo não existir

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
            # Store user data in session state
            st.session_state["token"] = data["access_token"]
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = data["user_id"]
            st.session_state["username"] = data["username"]
            st.session_state["role"] = data["role"]
            st.session_state["company_id"] = data.get("company_id")  # May be None
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
        elif response.status_code == 403:
            st.error("You don't have permission to access this resource")
            return None
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

def put_api_data(endpoint: str, data: dict) -> bool:
    """Generic function to update data via API using PUT."""
    if "token" not in st.session_state:
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.put(f"{API_URL}/{endpoint}", headers=headers, json=data)
        if response.status_code in [200, 201, 204]:
            return True
        else:
            st.error(f"Failed to update data at '{endpoint}'. Status code: {response.status_code}")
            if response.text:
                st.error(response.text)
            return False
    except Exception as e:
        st.error(f"Communication error with the API: {str(e)}")
        return False

def delete_api_data(endpoint: str) -> bool:
    """Generic function to delete data via API."""
    if "token" not in st.session_state:
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.delete(f"{API_URL}/{endpoint}", headers=headers)
        if response.status_code in [200, 204]:
            return True
        else:
            st.error(f"Failed to delete from '{endpoint}'. Status code: {response.status_code}")
            if response.text:
                st.error(response.text)
            return False
    except Exception as e:
        st.error(f"Communication error with the API: {str(e)}")
        return False

# ----- UI Helper Functions -----
def is_admin():
    """Check if current user is an admin"""
    return st.session_state.get("role") == "admin"

def show_delete_button(item_type, item_id, label="Delete", confirm_text=None):
    """
    Display a delete button with confirmation.
    
    Args:
        item_type: Type of item (singular form: 'user', 'company', 'machine', 'maintenance')
        item_id: ID of the item to delete
        label: Button label
        confirm_text: Confirmation message
    """
    if confirm_text is None:
        confirm_text = f"Are you sure you want to delete this {item_type}?"
    
    # Chave para rastrear o estado de confirmação no session_state
    confirm_key = f"confirm_delete_{item_type}_{item_id}"
    
    # Se já estamos em modo de confirmação
    if st.session_state.get(confirm_key, False):
        st.warning(confirm_text)
        
        # Criar dois botões lado a lado: Confirmar e Cancelar
        col1, col2 = st.columns(2)
        
        with col1:
            # Botão de confirmação
            if st.button("Confirm Delete", key=f"confirm_delete_btn_{item_type}_{item_id}"):
                # Mapear tipos de itens para seus endpoints correspondentes
                endpoint_map = {
                    "user": f"auth/users/{item_id}",
                    "company": f"companies/{item_id}",
                    "machine": f"machines/{item_id}",
                    "maintenance": f"maintenances/{item_id}"
                }
                
                # Obter o endpoint adequado para o tipo de item
                if item_type in endpoint_map:
                    endpoint = endpoint_map[item_type]
                else:
                    # Caso padrão para outros tipos não especificados
                    endpoint = f"{item_type}s/{item_id}"
                
                if delete_api_data(endpoint):
                    st.success(f"{item_type.capitalize()} deleted successfully!")
                    # Reset confirmation status
                    st.session_state[confirm_key] = False
                    st.rerun()
                return True
        
        with col2:
            # Botão de cancelar
            if st.button("Cancel", key=f"cancel_delete_{item_type}_{item_id}"):
                # Reset confirmation status
                st.session_state[confirm_key] = False
                st.rerun()
            return False
    else:
        # Mostrar o botão de delete inicial
        if st.button(label, key=f"delete_{item_type}_{item_id}"):
            # Ativar modo de confirmação
            st.session_state[confirm_key] = True
            st.rerun()
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
# Display user info in sidebar
user_role = st.session_state.get("role", "unknown")
username = st.session_state.get("username", "unknown")

# Obter o logo da empresa se o usuário for um gestor de frota
company_logo_path = DEFAULT_LOGO_PATH
if user_role == "fleet_manager" and st.session_state.get("company_id"):
    # Fetch company info
    company = get_api_data(f"companies/{st.session_state['company_id']}")
    if company and company.get("logo_path"):
        logo_path = os.path.join("frontend/images", company.get("logo_path"))
        if os.path.exists(logo_path):
            company_logo_path = logo_path

st.sidebar.image(company_logo_path, width=60)
st.sidebar.title("FleetPilot")

# User info section
with st.sidebar.container():
    st.write(f"**User:** {username}")
    st.write(f"**Role:** {user_role.replace('_', ' ').title()}")
    if user_role == "fleet_manager" and st.session_state.get("company_id"):
        # Fetch company name
        company = get_api_data(f"companies/{st.session_state['company_id']}")
        if company:
            st.write(f"**Company:** {company['name']}")
# Menu items depend on user role
menu_items = ["Dashboard", "Companies", "Machines", "Maintenances", "Settings", "Logout"]

# Admin gets an extra menu item for user management
if is_admin():
    menu_items.insert(4, "Users")

menu = st.sidebar.radio("Menu", menu_items)

# -----------------------------------------------------------------------------
#                                DASHBOARD
# -----------------------------------------------------------------------------
if menu == "Dashboard":
    st.title("Fleet Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    # Fetch data from the API - different behavior based on user role
    if is_admin():
        # Admin sees all data
        machines = get_api_data("machines") or []
        maintenances = get_api_data("maintenances") or []
        companies = get_api_data("companies") or []
    else:
        # Fleet manager sees only their company's data
        company_id = st.session_state.get("company_id")
        if company_id:
            machines = get_api_data(f"machines/company/{company_id}") or []
            maintenances = get_api_data(f"maintenances/company/{company_id}") or []
            companies = [get_api_data(f"companies/{company_id}")] if get_api_data(f"companies/{company_id}") else []
        else:
            machines = []
            maintenances = []
            companies = []
    
    # Calculate upcoming maintenances within 7 days
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    # Filter upcoming maintenances
    upcoming_maintenances = []
    for m in maintenances:
        # Convert "scheduled_date" from string to date
        sched_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
        if today <= sched_date <= next_week and not m.get("completed", False):
            upcoming_maintenances.append(m)
    
    col1.metric("Total Machines", len(machines))
    col2.metric("Upcoming Maintenances", len(upcoming_maintenances))
    col3.metric("Companies", len(companies))
    
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
        
        # Add machine name and company name for better readability
        for m in upcoming_maintenances:
            # Get machine details
            machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
            if machine:
                m["machine_name"] = machine["name"]
                
                # Get company details
                company = next((comp for comp in companies if comp["id"] == machine["company_id"]), None)
                if company:
                    m["company_name"] = company["name"]
        
        # Convert to DataFrame for nice display
        df_upcoming = pd.DataFrame(upcoming_maintenances)
        if not df_upcoming.empty:
            # Reorder and select columns for display
            columns_to_show = []
            if "scheduled_date" in df_upcoming.columns:
                columns_to_show.append("scheduled_date")
            if "type" in df_upcoming.columns:
                columns_to_show.append("type")
            if "machine_name" in df_upcoming.columns:
                columns_to_show.append("machine_name")
            if "company_name" in df_upcoming.columns:
                columns_to_show.append("company_name")
            if "notes" in df_upcoming.columns:
                columns_to_show.append("notes")
            
            # Show DataFrame with selected columns
            if columns_to_show:
                st.dataframe(df_upcoming[columns_to_show])
            else:
                st.dataframe(df_upcoming)
        else:
            st.info("No maintenances scheduled in the next 7 days.")
    else:
        st.info("No maintenances scheduled in the next 7 days.")

# -----------------------------------------------------------------------------
#                               COMPANIES
# -----------------------------------------------------------------------------
elif menu == "Companies":
    st.title("Company Management")
    
    # Only admins can add new companies
    if is_admin():
        with st.form("new_company"):
            st.subheader("Add New Company")
            company_name = st.text_input("Company Name")
            company_address = st.text_input("Address (Optional)")
            company_logo = st.file_uploader("Logo da Empresa (opcional)", type=["png", "jpg", "jpeg"])
            submitted = st.form_submit_button("Add")
            
            if submitted and company_name:
                company_data = {"name": company_name}
                if company_address:
                    company_data["address"] = company_address
                    
                # Criar empresa
                new_company_response = requests.post(
                    f"{API_URL}/companies", 
                    headers={"Authorization": f"Bearer {st.session_state['token']}"},
                    json=company_data
                )
                
                if new_company_response.status_code in [200, 201]:
                    new_company = new_company_response.json()
                    company_id = new_company["id"]
                    
                    # Se um logo foi enviado, fazer upload
                    if company_logo:
                        # Salvar o arquivo temporariamente
                        temp_file_path = f"temp_logo_{company_id}.png"
                        with open(temp_file_path, "wb") as f:
                            f.write(company_logo.getbuffer())
                        
                        # Enviar o logo para a API
                        logo_endpoint = f"companies/{company_id}/logo"
                        upload_file_to_api(logo_endpoint, "logo", temp_file_path, company_logo.name)
                        
                        # Limpar arquivo temporário
                        try:
                            os.remove(temp_file_path)
                        except:
                            pass
                    
                    st.success(f"Empresa '{company_name}' adicionada com sucesso!")
                    st.rerun()
                else:
                    st.error(f"Erro ao criar empresa: {new_company_response.text}")
    
    st.subheader("Existing Companies")
    
    # Fetch companies - admins see all, fleet managers see only their own
    if is_admin():
        companies = get_api_data("companies") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            company = get_api_data(f"companies/{company_id}")
            companies = [company] if company else []
        else:
            companies = []
    
    if companies:
        # Create tabs for each company
        for comp in companies:
            with st.expander(f"{comp['name']} (ID: {comp['id']})"):
                if comp.get("logo_path"):
                    logo_path = os.path.join("frontend/images", comp.get("logo_path"))
                    if os.path.exists(logo_path):
                        st.image(logo_path, width=150, caption="Logo atual da empresa")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Address:** {comp.get('address', 'N/A')}")
                    
                    # Get machines for this company
                    machines = get_api_data(f"machines/company/{comp['id']}") or []
                    st.write(f"**Total Machines:** {len(machines)}")
                    
                    # Get users for this company (admin only)
                    if is_admin():
                        # This would require a new endpoint to get users by company
                        # st.write(f"**Users:** ...")
                        pass
                
                # Edit/Delete buttons (admin only)
                if is_admin():
                    with col2:
                        if st.button("Edit", key=f"edit_company_{comp['id']}"):
                            st.session_state["edit_company_id"] = comp["id"]
                            st.session_state["edit_company_name"] = comp["name"]
                            st.session_state["edit_company_address"] = comp.get("address", "")
                        
                        # Delete company button with confirmation
                        show_delete_button("company", comp["id"], 
                            confirm_text=f"Are you sure you want to delete {comp['name']}? This will delete all related machines and maintenances!")

            
            # Edit form appears if this company is being edited
            if is_admin() and st.session_state.get("edit_company_id") == comp["id"]:
                with st.form(f"edit_company_{comp['id']}"):
                    st.subheader(f"Edit Company: {comp['name']}")
                    new_name = st.text_input("Company Name", value=st.session_state["edit_company_name"])
                    new_address = st.text_input("Address", value=st.session_state["edit_company_address"])
                    new_logo = st.file_uploader("Atualizar Logo (opcional)", type=["png", "jpg", "jpeg"])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_edit = st.form_submit_button("Save Changes")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancel")
                    
                    if submit_edit and new_name:
                        if submit_edit and new_name and new_logo:
                            # Salvar o arquivo temporariamente
                            temp_file_path = f"temp_logo_{comp['id']}.png"
                            with open(temp_file_path, "wb") as f:
                                f.write(new_logo.getbuffer())
                            
                            # Enviar o logo para a API
                            logo_endpoint = f"companies/{comp['id']}/logo"
                            if upload_file_to_api(logo_endpoint, "logo", temp_file_path, new_logo.name):
                                st.success("Logo atualizado com sucesso!")
                                
                                # Limpar arquivo temporário
                                try:
                                    os.remove(temp_file_path)
                                except:
                                    pass
                                
                                # Limpar a sessão e recarregar
                                if "edit_company_id" in st.session_state:
                                    del st.session_state["edit_company_id"]
                        
                        update_data = {"name": new_name}
                        if new_address:
                            update_data["address"] = new_address
                            
                        if put_api_data(f"companies/{comp['id']}", update_data):
                            st.success("Company updated successfully!")
                            # Clear edit state
                            if "edit_company_id" in st.session_state:
                                del st.session_state["edit_company_id"]
                            st.rerun()
                    
                    if cancel_edit:
                        # Clear edit state
                        if "edit_company_id" in st.session_state:
                            del st.session_state["edit_company_id"]
                        st.rerun()
    else:
        st.info("No companies found.")

# -----------------------------------------------------------------------------
#                               MACHINES
# -----------------------------------------------------------------------------
elif menu == "Machines":
    st.title("Machine Management")
    
    # Fetch companies for the dropdown - admin sees all, fleet manager sees only their own
    if is_admin():
        companies = get_api_data("companies") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            company = get_api_data(f"companies/{company_id}")
            companies = [company] if company else []
        else:
            companies = []
    
    with st.form("new_machine"):
        st.subheader("Add New Machine")
        machine_name = st.text_input("Machine Name")
        # Based on schema, possible types are "truck" or "fixed"
        machine_type = st.selectbox("Type", ["truck", "fixed"])
        
        # The user will select a company by ID - for fleet managers, this is prefilled
        if is_admin():
            company_options = [c["id"] for c in companies]
            company_labels = [c["name"] for c in companies]
            
            if company_options:
                selected_company_idx = st.selectbox(
                    "Company",
                    options=range(len(company_options)),
                    format_func=lambda idx: company_labels[idx]
                )
                selected_company_id = company_options[selected_company_idx]
            else:
                st.warning("No companies available. Please add a company first.")
                selected_company_id = None
        else:
            # Fleet managers can only add machines to their company
            if companies:
                selected_company_id = companies[0]["id"]
                st.write(f"**Company:** {companies[0]['name']}")
            else:
                st.warning("Your company information is not available.")
                selected_company_id = None
        
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
                st.rerun()
    
    st.subheader("Existing Machines")
    
    # Fetch machines - admins see all, fleet managers see only their company's
    if is_admin():
        machines = get_api_data("machines") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            machines = get_api_data(f"machines/company/{company_id}") or []
        else:
            machines = []
    
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
        
        # Display machines in expandable sections
        for idx, machine in df_machines.iterrows():
            with st.expander(f"{machine['name']} ({machine['type']}) - {machine.get('company_name', 'Unknown Company')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID:** {machine['id']}")
                    st.write(f"**Type:** {machine['type']}")
                    st.write(f"**Company:** {machine.get('company_name', 'Unknown')}")
                    
                    # Display a button to view maintenances
                    if st.button("View Maintenances", key=f"view_maint_{machine['id']}"):
                        maintenances = get_api_data(f"maintenances/machine/{machine['id']}") or []
                        if maintenances:
                            st.write("**Scheduled Maintenances:**")
                            df_maint = pd.DataFrame(maintenances)
                            st.dataframe(df_maint[["scheduled_date", "type", "completed"]])
                        else:
                            st.info(f"No maintenances scheduled for {machine['name']}")
                
                # Edit/Delete buttons
                with col2:
                    if st.button("Edit", key=f"edit_machine_{machine['id']}"):
                        st.session_state["edit_machine_id"] = machine["id"]
                        st.session_state["edit_machine_name"] = machine["name"]
                        st.session_state["edit_machine_type"] = machine["type"]
                        st.session_state["edit_machine_company_id"] = machine["company_id"]
                    
                    # Delete machine button with confirmation
                    show_delete_button("machine", machine["id"], 
                        confirm_text=f"Are you sure you want to delete {machine['name']}? This will delete all related maintenances!")
            
            # Edit form appears if this machine is being edited
            if st.session_state.get("edit_machine_id") == machine["id"]:
                with st.form(f"edit_machine_{machine['id']}"):
                    st.subheader(f"Edit Machine: {machine['name']}")
                    new_name = st.text_input("Machine Name", value=st.session_state["edit_machine_name"])
                    new_type = st.selectbox("Type", ["truck", "fixed"], 
                                          index=0 if st.session_state["edit_machine_type"] == "truck" else 1)
                    
                    # Company selection - admin can change, fleet manager cannot
                    if is_admin():
                        company_options = [c["id"] for c in companies]
                        company_labels = [c["name"] for c in companies]
                        
                        if company_options:
                            current_company_idx = 0
                            for i, cid in enumerate(company_options):
                                if cid == st.session_state["edit_machine_company_id"]:
                                    current_company_idx = i
                                    break
                                    
                            new_company_idx = st.selectbox(
                                "Company",
                                options=range(len(company_options)),
                                format_func=lambda idx: company_labels[idx],
                                index=current_company_idx
                            )
                            new_company_id = company_options[new_company_idx]
                        else:
                            new_company_id = st.session_state["edit_machine_company_id"]
                    else:
                        # Fleet managers can't change company
                        new_company_id = st.session_state["edit_machine_company_id"]
                        company_name = get_company_name(new_company_id)
                        st.write(f"**Company:** {company_name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_edit = st.form_submit_button("Save Changes")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancel")
                    
                    if submit_edit and new_name:
                        update_data = {
                            "name": new_name,
                            "type": new_type,
                            "company_id": new_company_id
                        }
                            
                        if put_api_data(f"machines/{machine['id']}", update_data):
                            st.success("Machine updated successfully!")
                            # Clear edit state
                            if "edit_machine_id" in st.session_state:
                                del st.session_state["edit_machine_id"]
                            st.rerun()
                    
                    if cancel_edit:
                        # Clear edit state
                        if "edit_machine_id" in st.session_state:
                            del st.session_state["edit_machine_id"]
                        st.rerun()
    else:
        st.info("No machines found.")

# -----------------------------------------------------------------------------
#                              MAINTENANCES
# -----------------------------------------------------------------------------
elif menu == "Maintenances":
    st.title("Maintenance Scheduling")
    
    # Fetch data based on user role
    if is_admin():
        companies = get_api_data("companies") or []
        # Fetch all machines initially
        all_machines = get_api_data("machines") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            companies = [get_api_data(f"companies/{company_id}")] if get_api_data(f"companies/{company_id}") else []
            all_machines = get_api_data(f"machines/company/{company_id}") or []
        else:
            companies = []
            all_machines = []
    
    # Create a dictionary to quickly look up company names
    company_dict = {c["id"]: c["name"] for c in companies}
    
    # Create a form to schedule new maintenance
    with st.form("new_maintenance"):
        st.subheader("Schedule New Maintenance")
        
        # Company filter (admin only)
        if is_admin() and companies:
            company_options = [c["id"] for c in companies]
            company_labels = [c["name"] for c in companies]
            
            selected_company_idx = st.selectbox(
                "Filter by Company",
                options=range(len(company_options)),
                format_func=lambda idx: company_labels[idx],
                key="company_filter"
            )
            selected_company_id = company_options[selected_company_idx]
            
            # Filter machines by selected company
            machines = [m for m in all_machines if m["company_id"] == selected_company_id]
        else:
            # Fleet managers see only their company's machines
            machines = all_machines
        
        # Let user pick a machine
        if machines:
            machine_options = [m["id"] for m in machines]
            machine_labels = [f"{m['name']} ({m['type']})" for m in machines]
            
            selected_machine_idx = st.selectbox(
                "Machine",
                options=range(len(machine_options)),
                format_func=lambda idx: machine_labels[idx]
            )
            chosen_machine_id = machine_options[selected_machine_idx]
        else:
            st.warning("No machines available. Please add a machine first.")
            chosen_machine_id = None
        
        # Types of maintenance
        maintenance_type = st.selectbox(
            "Maintenance Type",
            ["Oil Change", "Full Review", "Filters", "Tires", "Other"]
        )
        
        final_type = maintenance_type
        if maintenance_type == "Other":
            user_type = st.text_input("Specify the maintenance type")
            if user_type:
                final_type = user_type
        
        # Date selection
        scheduled_date = st.date_input(
            "Scheduled Date",
            min_value=datetime.now().date(),
            value=datetime.now().date() + timedelta(days=7)
        )
        
        # Optional notes
        notes = st.text_area("Notes (Optional)")
        
        submitted = st.form_submit_button("Schedule")
        
        if submitted and chosen_machine_id:
            # According to MaintenanceCreate, we send: {"machine_id", "type", "scheduled_date", "notes"}
            data = {
                "machine_id": chosen_machine_id,
                "type": final_type,
                "scheduled_date": scheduled_date.isoformat()
            }
            if notes:
                data["notes"] = notes
                
            if post_api_data("maintenances", data):
                st.success(f"Maintenance scheduled on {scheduled_date}!")
                st.rerun()
    
    st.subheader("Scheduled Maintenances")
    
    # Fetch maintenances based on user role
    if is_admin():
        maintenances = get_api_data("maintenances") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            maintenances = get_api_data(f"maintenances/company/{company_id}") or []
        else:
            maintenances = []
    
    if maintenances:
        # Add machine name for better display
        for m in maintenances:
            machine = next((mac for mac in all_machines if mac["id"] == m["machine_id"]), None)
            if machine:
                m["machine_name"] = machine["name"]
                m["machine_type"] = machine["type"]
                
                # Add company name
                company_id = machine.get("company_id")
                if company_id in company_dict:
                    m["company_name"] = company_dict[company_id]
        
        # Convert to DataFrame for display
        df_maint = pd.DataFrame(maintenances)
        
        # Convert "scheduled_date" to datetime
        if "scheduled_date" in df_maint.columns:
            df_maint["scheduled_date"] = pd.to_datetime(df_maint["scheduled_date"])
        
        # Sort by date
        if "scheduled_date" in df_maint.columns:
            df_maint = df_maint.sort_values("scheduled_date")
        
        # Simple highlight for overdue / soon
        today = datetime.now().date()
        
        # Display maintenances in tabs: Pending and Completed
        tab1, tab2 = st.tabs(["Pending", "Completed"])
        
        with tab1:
            # Filter for pending maintenances
            pending = df_maint[df_maint["completed"] == False] if "completed" in df_maint.columns else df_maint
            
            if not pending.empty:
                for idx, maint in pending.iterrows():
                    # Determine urgency for color coding
                    date_val = maint["scheduled_date"].date() if "scheduled_date" in maint else today
                    days_remaining = (date_val - today).days
                    
                    if days_remaining <= 0:
                        status = "🔴 Overdue"
                    elif days_remaining <= 2:
                        status = "🟠 Urgent"
                    elif days_remaining <= 7:
                        status = "🟡 Soon"
                    else:
                        status = "🟢 Scheduled"
                    
                    # Create an expander with maintenance details
                    with st.expander(f"{status} - {maint.get('type', 'Maintenance')} on {maint.get('machine_name', 'Unknown Machine')} ({date_val})"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Machine:** {maint.get('machine_name', 'Unknown')}")
                            st.write(f"**Company:** {maint.get('company_name', 'Unknown')}")
                            st.write(f"**Type:** {maint.get('type', 'Unknown')}")
                            st.write(f"**Scheduled Date:** {date_val}")
                            
                            if "notes" in maint and maint["notes"]:
                                st.write(f"**Notes:** {maint['notes']}")
                        
                        with col2:
                            # Mark as completed button
                            if st.button("Mark Completed", key=f"complete_{maint['id']}"):
                                if put_api_data(f"maintenances/{maint['id']}", {"completed": True}):
                                    st.success("Maintenance marked as completed!")
                                    st.rerun()
                            
                            # Edit button
                            if st.button("Edit", key=f"edit_maint_{maint['id']}"):
                                st.session_state["edit_maint_id"] = maint["id"]
                                st.session_state["edit_maint_type"] = maint["type"]
                                st.session_state["edit_maint_date"] = maint["scheduled_date"]
                                st.session_state["edit_maint_notes"] = maint.get("notes", "")
                            
                            # Delete button
                            show_delete_button("maintenance", maint["id"])
                    
                    # Edit form appears if this maintenance is being edited
                    if st.session_state.get("edit_maint_id") == maint["id"]:
                        with st.form(f"edit_maint_{maint['id']}"):
                            st.subheader(f"Edit Maintenance")
                            
                            edit_type = st.text_input("Maintenance Type", value=st.session_state["edit_maint_type"])
                            
                            edit_date = st.date_input(
                                "Scheduled Date",
                                value=st.session_state["edit_maint_date"].date() 
                                    if isinstance(st.session_state["edit_maint_date"], datetime) 
                                    else datetime.strptime(st.session_state["edit_maint_date"], "%Y-%m-%d").date(),
                                min_value=datetime.now().date()
                            )
                            
                            edit_notes = st.text_area("Notes", value=st.session_state["edit_maint_notes"])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                submit_edit = st.form_submit_button("Save Changes")
                            with col2:
                                cancel_edit = st.form_submit_button("Cancel")
                            
                            if submit_edit and edit_type:
                                update_data = {
                                    "type": edit_type,
                                    "scheduled_date": edit_date.isoformat(),
                                    "notes": edit_notes
                                }
                                
                                if put_api_data(f"maintenances/{maint['id']}", update_data):
                                    st.success("Maintenance updated successfully!")
                                    # Clear edit state
                                    if "edit_maint_id" in st.session_state:
                                        del st.session_state["edit_maint_id"]
                                    st.rerun()
                            
                            if cancel_edit:
                                # Clear edit state
                                if "edit_maint_id" in st.session_state:
                                    del st.session_state["edit_maint_id"]
                                st.rerun()
            else:
                st.info("No pending maintenances.")
        
        with tab2:
            # Filter for completed maintenances
            completed = df_maint[df_maint["completed"] == True] if "completed" in df_maint.columns else pd.DataFrame()
            
            if not completed.empty:
                st.dataframe(completed[["scheduled_date", "type", "machine_name", "company_name"]])
            else:
                st.info("No completed maintenances.")
    else:
        st.info("No maintenances scheduled.")

# -----------------------------------------------------------------------------
#                                  USERS
# -----------------------------------------------------------------------------
elif menu == "Users" and is_admin():
    st.title("User Management")
    
    # Fetch all companies for dropdown
    companies = get_api_data("companies") or []
    
    # Create a new user form
    with st.form("new_user"):
        st.subheader("Create New User")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        
        # Role selection
        role = st.selectbox("Role", ["admin", "fleet_manager"])
        
        # Company selection (for fleet managers)
        company_id = None
        if role == "fleet_manager":
            if companies:
                company_options = [c["id"] for c in companies]
                company_labels = [c["name"] for c in companies]
                
                selected_company_idx = st.selectbox(
                    "Assign to Company",
                    options=range(len(company_options)),
                    format_func=lambda idx: company_labels[idx]
                )
                company_id = company_options[selected_company_idx]
            else:
                st.warning("No companies available. Please create a company first.")
        
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            if not username or not password:
                st.error("Username and password are required")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                # Create user data
                user_data = {
                    "username": username,
                    "password": password,
                    "full_name": full_name,
                    "email": email,
                    "role": role
                }
                
                # Add company_id for fleet managers
                if role == "fleet_manager" and company_id:
                    user_data["company_id"] = company_id
                
                if post_api_data("auth/users", user_data):
                    st.success(f"User '{username}' created successfully!")
                    st.rerun()
    
    # List existing users
    st.subheader("Existing Users")
    
    # Fetch all users
    users = get_api_data("auth/users") or []
    
    if users:
        # Add company name for display
        for user in users:
            if user.get("company_id"):
                company = next((c for c in companies if c["id"] == user["company_id"]), None)
                if company:
                    user["company_name"] = company["name"]
        
        # Display users in expandable sections
        for user in users:
            status = "🟢 Active" if user.get("is_active", True) else "🔴 Inactive"
            with st.expander(f"{user['username']} - {user.get('role', 'Unknown').replace('_', ' ').title()} ({status})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID:** {user['id']}")
                    st.write(f"**Full Name:** {user.get('full_name', 'N/A')}")
                    st.write(f"**Email:** {user.get('email', 'N/A')}")
                    st.write(f"**Role:** {user.get('role', 'Unknown').replace('_', ' ').title()}")
                    if "company_name" in user:
                        st.write(f"**Company:** {user['company_name']}")
                
                with col2:
                    # Edit button
                    if st.button("Edit", key=f"edit_user_{user['id']}"):
                        st.session_state["edit_user_id"] = user["id"]
                        st.session_state["edit_user_username"] = user["username"]
                        st.session_state["edit_user_full_name"] = user.get("full_name", "")
                        st.session_state["edit_user_email"] = user.get("email", "")
                        st.session_state["edit_user_role"] = user.get("role", "fleet_manager")
                        st.session_state["edit_user_company_id"] = user.get("company_id")
                        st.session_state["edit_user_is_active"] = user.get("is_active", True)
                    
                    # Don't allow deleting current user
                    if user["id"] != st.session_state.get("user_id"):
                        # Delete user button with confirmation
                        show_delete_button("user", user["id"], 
                            confirm_text=f"Are you sure you want to delete user {user['username']}?")

            
            # Edit form appears if this user is being edited
            if st.session_state.get("edit_user_id") == user["id"]:
                with st.form(f"edit_user_{user['id']}"):
                    st.subheader(f"Edit User: {user['username']}")
                    
                    edit_username = st.text_input("Username", value=st.session_state["edit_user_username"])
                    edit_password = st.text_input("New Password (leave empty to keep current)", type="password")
                    edit_full_name = st.text_input("Full Name", value=st.session_state["edit_user_full_name"])
                    edit_email = st.text_input("Email", value=st.session_state["edit_user_email"])
                    
                    # Role selection (can't change Filipe Ferreira's role)
                    if user["username"] == "filipe.ferreira":
                        edit_role = "admin"
                        st.write("**Role:** Administrator (cannot be changed)")
                    else:
                        edit_role = st.selectbox(
                            "Role", 
                            ["admin", "fleet_manager"],
                            index=0 if st.session_state["edit_user_role"] == "admin" else 1
                        )
                    
                    # Company selection (for fleet managers)
                    edit_company_id = None
                    if edit_role == "fleet_manager":
                        if companies:
                            company_options = [c["id"] for c in companies]
                            company_labels = [c["name"] for c in companies]
                            
                            # Find current company index
                            current_company_idx = 0
                            current_company_id = st.session_state["edit_user_company_id"]
                            if current_company_id:
                                for i, cid in enumerate(company_options):
                                    if cid == current_company_id:
                                        current_company_idx = i
                                        break
                            
                            selected_company_idx = st.selectbox(
                                "Assign to Company",
                                options=range(len(company_options)),
                                format_func=lambda idx: company_labels[idx],
                                index=current_company_idx
                            )
                            edit_company_id = company_options[selected_company_idx]
                        else:
                            st.warning("No companies available.")
                    
                    # Active status
                    edit_is_active = st.checkbox("Active", value=st.session_state["edit_user_is_active"])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_edit = st.form_submit_button("Save Changes")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancel")
                    
                    if submit_edit:
                        # Build update data
                        update_data = {
                            "username": edit_username,
                            "full_name": edit_full_name,
                            "email": edit_email,
                            "is_active": edit_is_active
                        }
                        
                        # Only include password if provided
                        if edit_password:
                            update_data["password"] = edit_password
                        
                        # Include role if not Filipe Ferreira
                        if user["username"] != "filipe.ferreira":
                            update_data["role"] = edit_role
                        
                        # Include company_id for fleet managers
                        if edit_role == "fleet_manager" and edit_company_id:
                            update_data["company_id"] = edit_company_id
                        elif edit_role == "admin":
                            update_data["company_id"] = None
                        
                        if put_api_data(f"auth/users/{user['id']}", update_data):
                            st.success("User updated successfully!")
                            # Clear edit state
                            if "edit_user_id" in st.session_state:
                                del st.session_state["edit_user_id"]
                            st.rerun()
                    
                    if cancel_edit:
                        # Clear edit state
                        if "edit_user_id" in st.session_state:
                            del st.session_state["edit_user_id"]
                        st.rerun()
    else:
        st.info("No users found.")

# -----------------------------------------------------------------------------
#                               SETTINGS
# -----------------------------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    
    # User profile settings
    st.subheader("Your Profile")
    
    # Get current user details
    current_user = get_api_data("auth/users/me")
    
    if current_user:
        with st.form("update_profile"):
            full_name = st.text_input("Full Name", value=current_user.get("full_name", ""))
            email = st.text_input("Email", value=current_user.get("email", ""))
            
            # Password change
            st.subheader("Change Password")
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submitted = st.form_submit_button("Update Profile")
            
            if submitted:
                # Check if trying to change password
                if new_password:
                    if not current_password:
                        st.error("Current password is required to set a new password")
                    elif new_password != confirm_password:
                        st.error("New passwords do not match")
                    else:
                        # Here we would need to verify the current password
                        # For now, we'll just update the password
                        update_data = {
                            "full_name": full_name,
                            "email": email,
                            "password": new_password
                        }
                        
                        if put_api_data(f"auth/users/{current_user['id']}", update_data):
                            st.success("Profile and password updated successfully!")
                else:
                    # Just update profile without password
                    update_data = {
                        "full_name": full_name,
                        "email": email
                    }
                    
                    if put_api_data(f"auth/users/{current_user['id']}", update_data):
                        st.success("Profile updated successfully!")
    
    # Notification settings
    st.subheader("Notification Settings")
    
    # In production, these would come from a saved settings table
    with st.form("notification_settings"):
        st.write("Configure phone numbers to receive SMS alerts for maintenances.")
        
        phone_number = st.text_input("Phone Number (with country code)", value="351911234567")
        enable_sms = st.checkbox("Enable SMS notifications", value=True)
        enable_email = st.checkbox("Enable email notifications", value=True)
        
        # Notification timing
        st.write("When to send advance notifications:")
        days_before = st.slider("Days before scheduled maintenance", 1, 14, 3)
        
        if st.form_submit_button("Save Settings"):
            # In production, save to DB or call an endpoint
            st.success("Notification settings saved successfully!")
    
    # Admin-only settings
    if is_admin():
        st.subheader("System Settings")
        
        with st.form("system_settings"):
            smtp_server = st.text_input("SMTP Server", value="smtp.example.com")
            smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
            smtp_user = st.text_input("SMTP Username", value="alert@example.com")
            smtp_password = st.text_input("SMTP Password", type="password")
            
            if st.form_submit_button("Save System Settings"):
                # In production, these would be saved to environment variables or a settings table
                st.success("System settings saved successfully!")

# -----------------------------------------------------------------------------
#                                LOGOUT
# -----------------------------------------------------------------------------
elif menu == "Logout":
    st.write("Confirm to logout?")
    if st.button("Confirm Logout"):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()