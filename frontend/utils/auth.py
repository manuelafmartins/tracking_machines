# -*- coding: utf-8 -*-
import streamlit as st
import requests
from .api import get_api_data, API_URL


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
            
            # Obter o full_name do usuÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡rio para exibir no sidebar
            user_info = get_api_data("auth/users/me")
            if user_info and "full_name" in user_info:
                st.session_state["full_name"] = user_info.get("full_name", username)
            else:
                st.session_state["full_name"] = username  # Fallback para username se full_name nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â£o estiver disponÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â­vel
                
            return True
        else:
            st.error("Invalid credentials or connection error.")
    except requests.exceptions.ConnectionError:
        st.error("API connection error. Please check if the backend is running.")
    except Exception as e:
        st.error(f"Login error: {str(e)}")
    return False

def is_admin():
    """Check if current user is an admin"""
    return st.session_state.get("role") == "admin"

def logout_user():
    """Logs out the user by clearing session state"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]