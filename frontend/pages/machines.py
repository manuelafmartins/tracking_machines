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

def show_machines():
    title_col, btn_col = st.columns([9, 1])
    
    with title_col:
        st.title("Machine Management")
    
    with btn_col:
        # Inicializar o estado do formulÃƒÆ’Ã‚Â¡rio se nÃƒÆ’Ã‚Â£o existir
        if "show_add_machine_form" not in st.session_state:
            st.session_state["show_add_machine_form"] = False
        
        # Adicionar espaÃƒÆ’Ã‚Â§o para alinhar com o tÃƒÆ’Ã‚Â­tulo
        st.write("")
        st.write("")
        
        # Usar um ÃƒÆ’Ã‚Âºnico botÃƒÆ’Ã‚Â£o Streamlit, mas garantir que tenha o texto certo
        if st.session_state["show_add_machine_form"]:
            button_symbol = "Fechar"
        else:
            button_symbol = "Adicionar"
        
        # BotÃƒÆ’Ã‚Â£o simples do Streamlit
        if st.button(button_symbol, key="add_machine_button"):
            st.session_state["show_add_machine_form"] = not st.session_state["show_add_machine_form"]
            st.rerun()
    
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
    
    # FormulÃƒÆ’Ã‚Â¡rio de adiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o de mÃƒÆ’Ã‚Â¡quina (apenas mostrado quando necessÃƒÆ’Ã‚Â¡rio)
    if st.session_state["show_add_machine_form"]:
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
                    # Esconder o formulÃƒÆ’Ã‚Â¡rio depois de adicionar com sucesso
                    st.session_state["show_add_machine_form"] = False
                    st.rerun()
    
    
    st.subheader("Máquinas Atuais:")
    
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