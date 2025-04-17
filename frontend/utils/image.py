# -*- coding: utf-8 -*-
import streamlit as st
import os
import base64

DEFAULT_LOGO_PATH = "frontend/images/logo.png"

def get_image_base64(image_path: str) -> str:
    """Encodes the specified image in base64 for inline display."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Imagem não encontrada: {image_path}")
        return ""

def get_company_logo_path(logo_relative_path: str) -> str:
    """Retorna o caminho completo do logo da empresa."""
    if not logo_relative_path:
        return DEFAULT_LOGO_PATH
    
    # Caminho completo para a pasta de imagens
    image_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")
    logo_path = os.path.join(image_dir, logo_relative_path)
    
    # Verificar se o arquivo existe
    if os.path.exists(logo_path):
        return logo_path
    else:
        return DEFAULT_LOGO_PATH

def save_company_logo(company_id, file_data):
    """Salva o logo da empresa diretamente no sistema de arquivos"""
    try:
        # Criar diretório se não existir
        os.makedirs("frontend/images/company_logos", exist_ok=True)
        
        # Gerar nome de arquivo seguro
        file_extension = os.path.splitext(file_data.name)[1]
        logo_filename = f"company_{company_id}{file_extension}"
        logo_path = os.path.join("frontend/images/company_logos", logo_filename)
        
        # Salvar arquivo
        with open(logo_path, "wb") as f:
            f.write(file_data.getbuffer())
        
        # Retornar o caminho relativo para armazenar no banco de dados
        return f"company_logos/{logo_filename}"
    except Exception as e:
        st.error(f"Erro ao salvar logo: {str(e)}")
        return None