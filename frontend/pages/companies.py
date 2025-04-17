import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
from frontend.utils.api import get_api_data
from frontend.utils.auth import is_admin
from utils.ui import display_menu, show_delete_button
from utils.auth import login_user, logout_user, is_admin
from utils.image import get_image_base64, save_company_logo
from utils.api import get_api_data, post_api_data, put_api_data, delete_api_data
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Fetch variables
API_URL = os.getenv("API_URL")

def show_companies():
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
                    
                    # Se um logo foi enviado, salvar e atualizar caminho
                    if company_logo:
                        logo_relative_path = save_company_logo(company_id, company_logo)
                        
                        if logo_relative_path:
                            # Atualizar o caminho do logo no banco de dados
                            update_data = {"logo_path": logo_relative_path}
                            put_api_data(f"companies/{company_id}", update_data)
                    
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
                            # Nova implementaÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â£o
                            logo_relative_path = save_company_logo(comp['id'], new_logo)
                            
                            if logo_relative_path:
                                # Atualizar apenas o caminho do logo no banco de dados
                                update_data = {
                                    "name": new_name,
                                    "address": new_address,
                                    "logo_path": logo_relative_path
                                }
                                
                                if put_api_data(f"companies/{comp['id']}", update_data):
                                    st.success("Empresa e logo atualizados com sucesso!")
                                    if "edit_company_id" in st.session_state:
                                        del st.session_state["edit_company_id"]
                                    st.rerun()
                        
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