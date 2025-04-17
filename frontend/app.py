# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
import base64
from datetime import datetime, timedelta
import plotly.express as px
import json
import os
from PIL import Image
import streamlit as st
import os
from utils.auth import login_user, logout_user, is_admin
from utils.image import get_image_base64, save_company_logo
from utils.ui import display_menu
from utils.api import get_api_data, post_api_data, put_api_data, delete_api_data
from pages import dashboard, companies, machines, maintenances, users, settings
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Fetch variables
LOGO_PATH = os.getenv("LOGO_PATH")
DEFAULT_LOGO_PATH = os.getenv("DEFAULT_LOGO_PATH")


# Set up the Streamlit page layout
st.set_page_config(
    page_title="FF ManutenControl",
    layout="wide"
)

# ----- Initialize Session State -----
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ----- Login Screen -----
if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>FF ManutenControl</h1>", unsafe_allow_html=True)
    
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

# Obter o logo da empresa se o usuÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡rio for um gestor de frota
company_logo_path = DEFAULT_LOGO_PATH
if user_role == "fleet_manager" and st.session_state.get("company_id"):
    company_id = st.session_state.get("company_id")
    
    # Verificar diretamente se existe um arquivo de logo para esta empresa
    possible_extensions = ['.png', '.jpg', '.jpeg']
    for ext in possible_extensions:
        potential_logo_path = os.path.join("frontend/images/company_logos", f"company_{company_id}{ext}")
        if os.path.exists(potential_logo_path):
            company_logo_path = potential_logo_path
            break
    
st.sidebar.image(company_logo_path)
st.sidebar.title("FleetPilot")

# User info section
with st.sidebar.container():
    # Usar o full_name em vez do username, com fallback para username se full_name nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â£o estiver disponÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â­vel
    full_name = st.session_state.get("full_name", username)
    st.write(f"**Nome:** {full_name}")
    st.write(f"**Função:** {user_role.replace('_', ' ').title()}")
    if user_role == "fleet_manager" and st.session_state.get("company_id"):
        # Fetch company name
        company = get_api_data(f"companies/{st.session_state['company_id']}")
        if company:
            st.write(f"**Empresa:** {company['name']}")

# Remova a parte de JavaScript que nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â£o estÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ funcionando

# Mantenha apenas o CSS para estilizar os botÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Âµes
st.markdown("""
<style>
    div.stButton > button {
        background-color: #2c3e50;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
        margin: 0px 5px;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #34495e;
    }
    div.stButton > button:focus {
        background-color: #3498db;
    }
</style>
""", unsafe_allow_html=True)

# Criar uma linha de botÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Âµes para o menu
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    dashboard_btn = st.button("Dashboard")
with col2:
    companies_btn = st.button("Empresas")
with col3:
    machines_btn = st.button("Máquinas")
with col4:
    maintenances_btn = st.button("Manutenções")

# Adicione o botÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â£o "UsuÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡rios" apenas para admins
if is_admin():
    with col5:
        users_btn = st.button("Utilizadores")
    with col6:
        settings_btn = st.button("Configurações")
else:
    with col5:
        settings_btn = st.button("Configurações")
    with col6:
        users_btn = False

# BotÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â£o de logout pode ficar separado
logout_btn = st.button("Sair")

# Controle qual pÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡gina estÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ sendo exibida
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Dashboard"

# Atualizar a pÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡gina atual com base nos botÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Âµes clicados
if dashboard_btn:
    st.session_state["current_page"] = "Dashboard"
    st.rerun()
elif companies_btn:
    st.session_state["current_page"] = "Companies"
    st.rerun()
elif machines_btn:
    st.session_state["current_page"] = "Machines"
    st.rerun()
elif maintenances_btn:
    st.session_state["current_page"] = "Maintenances"
    st.rerun()
elif users_btn:
    st.session_state["current_page"] = "Users"
    st.rerun()
elif settings_btn:
    st.session_state["current_page"] = "Settings"
    st.rerun()
elif logout_btn:
    st.session_state["current_page"] = "Logout"
    st.rerun()


menu = st.session_state["current_page"]

if menu == "Dashboard":
    dashboard.show_dashboard()

elif menu == "Companies":
    companies.show_companies()

# -----------------------------------------------------------------------------
#                               MACHINES
# -----------------------------------------------------------------------------
elif menu == "Machines":
    machines.show_machines()

# -----------------------------------------------------------------------------
#                              MAINTENANCES
# -----------------------------------------------------------------------------
elif menu == "Maintenances":
    maintenances.show_maintenances()

# -----------------------------------------------------------------------------
#                                  USERS
# -----------------------------------------------------------------------------
elif menu == "Users" and is_admin():
    users.show_users()

# -----------------------------------------------------------------------------
#                               SETTINGS
# -----------------------------------------------------------------------------
elif menu == "Settings":
    settings.show_settings()

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