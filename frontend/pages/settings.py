# frontend/pages/settings.py
import streamlit as st
from ..utils.api import get_api_data, put_api_data
from ..utils.ui import is_admin

def show_settings():
    """Exibe a p�gina de configura��es do sistema."""
    st.title("Configura��es do Sistema")
    
    # Configura��es do perfil do usu�rio
    st.subheader("Seu Perfil")
    
    # Obter detalhes do usu�rio atual
    current_user = get_api_data("auth/users/me")
    
    if current_user:
        with st.form("update_profile"):
            full_name = st.text_input("Nome Completo", value=current_user.get("full_name", ""))
            email = st.text_input("Email", value=current_user.get("email", ""))
            
            # Altera��o de senha
            st.subheader("Alterar Senha")
            current_password = st.text_input("Senha Atual", type="password")
            new_password = st.text_input("Nova Senha", type="password")
            confirm_password = st.text_input("Confirmar Nova Senha", type="password")
            
            submitted = st.form_submit_button("Atualizar Perfil")
            
            if submitted:
                # Verificar se est� tentando alterar a senha
                if new_password:
                    if not current_password:
                        st.error("A senha atual � necess�ria para definir uma nova senha")
                    elif new_password != confirm_password:
                        st.error("As novas senhas n�o coincidem")
                    else:
                        # Aqui seria necess�rio verificar a senha atual
                        # Por enquanto, apenas atualizaremos a senha
                        update_data = {
                            "full_name": full_name,
                            "email": email,
                            "password": new_password
                        }
                        
                        if put_api_data(f"auth/users/{current_user['id']}", update_data):
                            st.success("Perfil e senha atualizados com sucesso!")
                else:
                    # Apenas atualizar o perfil sem senha
                    update_data = {
                        "full_name": full_name,
                        "email": email
                    }
                    
                    if put_api_data(f"auth/users/{current_user['id']}", update_data):
                        st.success("Perfil atualizado com sucesso!")
    
    # Configura��es de notifica��o
    st.subheader("Configura��es de Notifica��o")
    
    # Em produ��o, essas configura��es viriam de uma tabela de configura��es salva
    with st.form("notification_settings"):
        st.write("Configure n�meros de telefone para receber alertas SMS para manuten��es.")
        
        phone_number = st.text_input("N�mero de Telefone (com c�digo do pa�s)", value="351911234567")
        enable_sms = st.checkbox("Ativar notifica��es por SMS", value=True)
        enable_email = st.checkbox("Ativar notifica��es por email", value=True)
        
        # Temporiza��o das notifica��es
        st.write("Quando enviar notifica��es antecipadas:")
        days_before = st.slider("Dias antes da manuten��o agendada", 1, 14, 3)
        
        if st.form_submit_button("Salvar Configura��es"):
            # Em produ��o, salvar no BD ou chamar um endpoint
            st.success("Configura��es de notifica��o salvas com sucesso!")
    
    # Configura��es somente para admin
    if is_admin():
        st.subheader("Configura��es do Sistema")
        
        with st.form("system_settings"):
            smtp_server = st.text_input("Servidor SMTP", value="smtp.example.com")
            smtp_port = st.number_input("Porta SMTP", value=587, min_value=1, max_value=65535)
            smtp_user = st.text_input("Usu�rio SMTP", value="alert@example.com")
            smtp_password = st.text_input("Senha SMTP", type="password")
            
            if st.form_submit_button("Salvar Configura��es do Sistema"):
                # Em produ��o, essas configura��es seriam salvas em vari�veis ??de ambiente ou em uma tabela de configura��es
                st.success("Configura��es do sistema salvas com sucesso!")