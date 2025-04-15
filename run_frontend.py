#!/usr/bin/env python3
"""
Script para iniciar a aplicação frontend modularizada do FleetPilot.
"""
import os
import subprocess
import sys

def run_frontend():
    """Executa a aplicação frontend usando Streamlit"""
    try:
        # Verificar se o Streamlit está instalado
        try:
            import streamlit
        except ImportError:
            print("Streamlit não está instalado. Instalando...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
        
        # Executar o Streamlit com o app.py modularizado
        print("Iniciando a aplicação frontend...")
        subprocess.run(["streamlit", "run", "frontend/app.py"])
    except Exception as e:
        print(f"Erro ao iniciar o frontend: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    # Verificar se os diretórios necessários existem
    if not os.path.exists("frontend/images/company_logos"):
        print("Criando diretórios necessários...")
        os.makedirs("frontend/images/company_logos", exist_ok=True)
    
    # Iniciar o frontend
    run_frontend()