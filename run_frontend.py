#!/usr/bin/env python3
"""
Script para iniciar a aplica��o frontend modularizada do FleetPilot.
"""
import os
import subprocess
import sys

def run_frontend():
    """Executa a aplica��o frontend usando Streamlit"""
    try:
        # Verificar se o Streamlit est� instalado
        try:
            import streamlit
        except ImportError:
            print("Streamlit n�o est� instalado. Instalando...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
        
        # Executar o Streamlit com o app.py modularizado
        print("Iniciando a aplica��o frontend...")
        subprocess.run(["streamlit", "run", "frontend/app.py"])
    except Exception as e:
        print(f"Erro ao iniciar o frontend: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    # Verificar se os diret�rios necess�rios existem
    if not os.path.exists("frontend/images/company_logos"):
        print("Criando diret�rios necess�rios...")
        os.makedirs("frontend/images/company_logos", exist_ok=True)
    
    # Iniciar o frontend
    run_frontend()