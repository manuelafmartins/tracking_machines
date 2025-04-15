# frontend/utils/api.py
import streamlit as st
import requests
import os
from ..config import API_URL

def get_api_data(endpoint: str):
    """Função genérica para buscar dados da API usando o token de autenticação armazenado."""
    if "token" not in st.session_state:
        return None
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.get(f"{API_URL}/{endpoint}", headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            st.error("Você não tem permissão para acessar este recurso")
            return None
        else:
            st.error(f"Falha ao buscar dados de '{endpoint}'. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro de comunicação com a API: {str(e)}")
        return None

def post_api_data(endpoint: str, data: dict) -> bool:
    """Função genérica para enviar dados JSON para a API usando o token armazenado."""
    if "token" not in st.session_state:
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.post(f"{API_URL}/{endpoint}", headers=headers, json=data)
        if response.status_code in [200, 201]:
            return True
        else:
            st.error(f"Falha ao enviar dados para '{endpoint}'. Status code: {response.status_code}")
            if response.text:
                st.error(response.text)
            return False
    except Exception as e:
        st.error(f"Erro de comunicação com a API: {str(e)}")
        return False

def put_api_data(endpoint: str, data: dict) -> bool:
    """Função genérica para atualizar dados via API usando PUT."""
    if "token" not in st.session_state:
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.put(f"{API_URL}/{endpoint}", headers=headers, json=data)
        if response.status_code in [200, 201, 204]:
            return True
        else:
            st.error(f"Falha ao atualizar dados em '{endpoint}'. Status code: {response.status_code}")
            if response.text:
                st.error(response.text)
            return False
    except Exception as e:
        st.error(f"Erro de comunicação com a API: {str(e)}")
        return False

def delete_api_data(endpoint: str) -> bool:
    """Função genérica para excluir dados via API."""
    if "token" not in st.session_state:
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.delete(f"{API_URL}/{endpoint}", headers=headers)
        if response.status_code in [200, 204]:
            return True
        else:
            st.error(f"Falha ao excluir de '{endpoint}'. Status code: {response.status_code}")
            if response.text:
                st.error(response.text)
            return False
    except Exception as e:
        st.error(f"Erro de comunicação com a API: {str(e)}")
        return False

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