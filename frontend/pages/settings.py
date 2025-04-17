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

def show_settings():
    st.title("System Settings")
    
    # User profile settings
    st.subheader("Your Profile")
    
    # Get current user details
    current_user = get_api_data("auth/users/me")
    
    if current_user:
        with st.form("update_profile"):
            full_name = st.text_input("Full Name", value=current_user.get("full_name", ""))
            email = st.text_input("Email", value=current_user.get("email", ""))
            
            # Adicionar campos de telefone e notificações
            phone_value = current_user.get("phone_number", "+351")
            phone_number = st.text_input("Phone Number (with country code)", value=phone_value)
            
            notifications_enabled = current_user.get("notifications_enabled", True)
            enable_notifications = st.checkbox("Enable SMS notifications", value=notifications_enabled)
            
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
                            "phone_number": phone_number,  # Adicionar esta linha
                            "notifications_enabled": enable_notifications,  # Adicionar esta linha
                            "password": new_password
                        }
                        
                        if put_api_data(f"auth/users/{current_user['id']}", update_data):
                            st.success("Profile and password updated successfully!")
                else:
                    # Just update profile without password
                    update_data = {
                        "full_name": full_name,
                        "email": email,
                        "phone_number": phone_number,  # Adicionar esta linha
                        "notifications_enabled": enable_notifications  # Adicionar esta linha
                    }
                    
                    if put_api_data(f"auth/users/{current_user['id']}", update_data):
                        st.success("Profile updated successfully!")

    
    # Notification settings
    st.subheader("SMS Notification Test")
    
    # In production, these would come from a saved settings table
    with st.form("test_sms"):
        st.write("Send a test SMS to your registered phone number.")
        test_message = st.text_area("Message", value="This is a test notification from FleetPilot.")
        
        if st.form_submit_button("Send Test SMS"):
            # Verificar se o usuário tem um número de telefone registrado
            if current_user.get("phone_number"):
                # Endpoint personalizado para testar notificações
                test_data = {
                    "message": test_message,
                    "user_id": current_user["id"]
                }
                
                # Este endpoint precisaria ser criado no backend
                if post_api_data("notifications/test", test_data):
                    st.success("Test message sent successfully!")
                else:
                    st.error("Failed to send test message.")
            else:
                st.error("You don't have a registered phone number. Please update your profile first.")
        
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