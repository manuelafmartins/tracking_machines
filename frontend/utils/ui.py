# frontend/utils/auth.py
import streamlit as st
import requests
import base64
from .ui import get_image_base64
from ..config import API_URL, DEFAULT_LOGO_PATH

def login_user(username: str, password: str) -> bool:
    """Tenta fazer login do usuário com as credenciais fornecidas; retorna True se bem-sucedido."""
    try:
        resp = requests.post(
            f"{API_URL}/auth/login", 
            data={"username": username, "password": password}
        )
        if resp.status_code == 200:
            data = resp.json()
            # Armazenar dados do usuário no session state
            st.session_state["token"] = data["access_token"]
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = data["user_id"]
            st.session_state["username"] = data["username"]
            st.session_state["role"] = data["role"]
            st.session_state["company_id"] = data.get("company_id")  # Pode ser None
            
            # Obter o full_name do usuário para exibir na sidebar
            from .api import get_api_data
            user_info = get_api_data("auth/users/me")
            if user_info and "full_name" in user_info:
                st.session_state["full_name"] = user_info.get("full_name", username)
            else:
                st.session_state["full_name"] = username  # Fallback para username se full_name não estiver disponível
                
            return True
        else:
            st.error("Credenciais inválidas ou erro de conexão.")
    except requests.exceptions.ConnectionError:
        st.error("Erro de conexão com a API. Verifique se o backend está em execução.")
    except Exception as e:
        st.error(f"Erro de login: {str(e)}")
    return False

def check_authentication():
    """Verifica se o usuário está autenticado."""
    return st.session_state.get("logged_in", False)

def login_screen():
    """Exibe a tela de login."""
    st.markdown("<h1 style='text-align: center;'>FleetPilot</h1>", unsafe_allow_html=True)
    
    image_base64 = get_image_base64(DEFAULT_LOGO_PATH)
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
                st.success("Login bem-sucedido!")
                st.rerun()
            else:
                st.error("Credenciais inválidas ou erro de conexão.")