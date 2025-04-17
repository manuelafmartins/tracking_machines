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

def show_users():
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
        phone_number = st.text_input("Phone Number (with country code)", value="+351")  # Adicionar este campo
        notifications_enabled = st.checkbox("Enable SMS notifications", value=True)  # Adicionar este campo
        
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
                    "role": role,
                    "phone_number": phone_number,  # Adicionar esta linha
                    "notifications_enabled": notifications_enabled  # Adicionar esta linha
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
            status = "ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â°ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ Active" if user.get("is_active", True) else "ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â°ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¯ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¿ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â½ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â´ Inactive"
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
                    
                    # Adicionar campos de telefone e notificações
                    phone_value = user.get("phone_number", "+351")
                    edit_phone_number = st.text_input("Phone Number (with country code)", value=phone_value)
                    
                    # Obter valor atual das notificações, com padrÃ£o True
                    notifications_enabled = user.get("notifications_enabled", True)
                    edit_notifications_enabled = st.checkbox("Enable SMS notifications", value=notifications_enabled)
                    
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
                            "is_active": edit_is_active,
                            "phone_number": edit_phone_number,  # Adicionar esta linha
                            "notifications_enabled": edit_notifications_enabled  # Adicionar esta linha
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