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
    
            # Dados básicos
            company_name = st.text_input("Company Name")
            
            # Nova seção para dados de faturação
            st.markdown("### Dados para faturação")
            tax_id = st.text_input("NIF/NIPC")
            
            # Morada e localização
            col1, col2 = st.columns(2)
            with col1:
                company_address = st.text_input("Address")
                postal_code = st.text_input("Postal Code")
            with col2:
                city = st.text_input("City")
                country = st.text_input("Country", value="Portugal")
            
            # Contactos
            col1, col2 = st.columns(2)
            with col1:
                billing_email = st.text_input("Billing Email")
            with col2:
                phone = st.text_input("Phone")
            
            # Detalhes bancários
            payment_method = st.selectbox("Preferred Payment Method", 
                                        ["Bank Transfer", "Direct Debit", "Credit Card", "Other"])
            iban = st.text_input("IBAN (for bank transfers)")
            
            # Logo
            company_logo = st.file_uploader("Company Logo (optional)", type=["png", "jpg", "jpeg"])
            
            submitted = st.form_submit_button("Add")
            
            if submitted and company_name:
                company_data = {
                    "name": company_name,
                    "address": company_address,
                    "tax_id": tax_id,
                    "postal_code": postal_code,
                    "city": city,
                    "country": country,
                    "billing_email": billing_email,
                    "phone": phone,
                    "payment_method": payment_method,
                    "iban": iban
                }
            
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
                    # Basic info
                    st.write(f"**Name:** {comp['name']}")
                    
                    # Billing info section
                    if any(comp.get(field) for field in ["tax_id", "postal_code", "city", "billing_email", "phone", "iban"]):
                        st.markdown("### Dados para faturação")
                        
                        if comp.get("tax_id"):
                            st.write(f"**NIF/NIPC:** {comp.get('tax_id')}")
                        
                        # Address info
                        address_parts = []
                        if comp.get("address"):
                            address_parts.append(comp.get("address"))
                        if comp.get("postal_code") or comp.get("city"):
                            postal_city = f"{comp.get('postal_code', '')} {comp.get('city', '')}".strip()
                            if postal_city:
                                address_parts.append(postal_city)
                        if comp.get("country"):
                            address_parts.append(comp.get("country"))
                        
                        if address_parts:
                            st.write(f"**Address:** {', '.join(address_parts)}")
                        
                        # Contact info
                        if comp.get("billing_email"):
                            st.write(f"**Billing Email:** {comp.get('billing_email')}")
                        if comp.get("phone"):
                            st.write(f"**Phone:** {comp.get('phone')}")
                        
                        # Payment info
                        if comp.get("payment_method"):
                            st.write(f"**Payment Method:** {comp.get('payment_method')}")
                        if comp.get("iban"):
                            st.write(f"**IBAN:** {comp.get('iban')}")
                    
                    # Get machines for this company (código existente)
                    machines = get_api_data(f"machines/company/{comp['id']}") or []
                    st.write(f"**Total Machines:** {len(machines)}")
                
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
                    
                    # Dados de faturação
                    st.markdown("### Dados para faturação")
                    new_tax_id = st.text_input("NIF/NIPC", value=comp.get("tax_id", ""))
                    
                    # Morada e localização
                    col1, col2 = st.columns(2)
                    with col1:
                        new_address = st.text_input("Address", value=st.session_state["edit_company_address"])
                        new_postal_code = st.text_input("Postal Code", value=comp.get("postal_code", ""))
                    with col2:
                        new_city = st.text_input("City", value=comp.get("city", ""))
                        new_country = st.text_input("Country", value=comp.get("country", "Portugal"))
                    
                    # Contactos
                    col1, col2 = st.columns(2)
                    with col1:
                        new_billing_email = st.text_input("Billing Email", value=comp.get("billing_email", ""))
                    with col2:
                        new_phone = st.text_input("Phone", value=comp.get("phone", ""))
                    
                    # Detalhes bancários
                    payment_options = ["Bank Transfer", "Direct Debit", "Credit Card", "Other"]
                    current_payment = comp.get("payment_method", "Bank Transfer")
                    payment_index = payment_options.index(current_payment) if current_payment in payment_options else 0
                    
                    new_payment_method = st.selectbox("Preferred Payment Method", 
                                                    payment_options, 
                                                    index=payment_index)
                    
                    new_iban = st.text_input("IBAN (for bank transfers)", value=comp.get("iban", ""))
                    
                    # Logo
                    new_logo = st.file_uploader("Update Logo (optional)", type=["png", "jpg", "jpeg"])
                    
                    # Botões de ação
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_edit = st.form_submit_button("Save Changes")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancel")
                    
                    if submit_edit and new_name:
                        # Atualizar os dados da empresa
                        update_data = {
                            "name": new_name,
                            "address": new_address,
                            "tax_id": new_tax_id,
                            "postal_code": new_postal_code,
                            "city": new_city,
                            "country": new_country,
                            "billing_email": new_billing_email,
                            "phone": new_phone,
                            "payment_method": new_payment_method,
                            "iban": new_iban
                        }
                    
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