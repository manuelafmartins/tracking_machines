import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json
load_dotenv()

API_URL = os.getenv("API_URL")

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
        st.error("Não autenticado. Faça login novamente.")
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        # Debug: mostrando a URL e os dados que estão sendo enviados
        full_url = f"{API_URL}/{endpoint}"
        st.write(f"Enviando para: {full_url}")
        st.write("Dados enviados:", data)
        
        response = requests.put(full_url, headers=headers, json=data)
        
        # Debug: mostrando a resposta completa
        st.write(f"Status code: {response.status_code}")
        st.write(f"Resposta: {response.text}")
        
        if response.status_code in [200, 201, 204]:
            return True
        else:
            st.error(f"Falha ao atualizar dados em '{endpoint}'. Status code: {response.status_code}")
            if response.text:
                st.error(f"Detalhes do erro: {response.text}")
            return False
    except Exception as e:
        st.error(f"Erro de comunicação com a API: {str(e)}")
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