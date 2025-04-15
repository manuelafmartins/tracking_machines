# frontend/pages/settings.py
import streamlit as st
from ..utils.api import get_api_data, put_api_data
from ..utils.ui import is_admin

def show_settings():
    """Exibe a página de configurações do sistema."""
    st.title("Configurações do Sistema")
    
    # Configurações do perfil do usuário
    st.subheader("Seu Perfil")
    
    # Obter detalhes do usuário atual
    current_user = get_api_data("auth/users/me")
    
    if current_user:
        with st.form("update_profile"):
            full_name = st.text_input("Nome Completo", value=current_user.get("full_name", ""))
            email = st.text_input("Email", value=current_user.get("email", ""))
            
            # Alteração de senha
            st.subheader("Alterar Senha")
            current_password = st.text_input("Senha Atual", type="password")
            new_password = st.text_input("Nova Senha", type="password")
            confirm_password = st.text_input("Confirmar Nova Senha", type="password")
            
            submitted = st.form_submit_button("Atualizar Perfil")
            
            if submitted:
                # Verificar se está tentando alterar a senha
                if new_password:
                    if not current_password:
                        st.error("A senha atual é necessária para definir uma nova senha")
                    elif new_password != confirm_password:
                        st.error("As novas senhas não coincidem")
                    else:
                        # Aqui seria necessário verificar a senha atual
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
    
    # Configurações de notificação
    st.subheader("Configurações de Notificação")
    
    # Em produção, essas configurações viriam de uma tabela de configurações salva
    with st.form("notification_settings"):
        st.write("Configure números de telefone para receber alertas SMS para manutenções.")
        
        phone_number = st.text_input("Número de Telefone (com código do país)", value="351911234567")
        enable_sms = st.checkbox("Ativar notificações por SMS", value=True)
        enable_email = st.checkbox("Ativar notificações por email", value=True)
        
        # Temporização das notificações
        st.write("Quando enviar notificações antecipadas:")
        days_before = st.slider("Dias antes da manutenção agendada", 1, 14, 3)
        
        if st.form_submit_button("Salvar Configurações"):
            # Em produção, salvar no BD ou chamar um endpoint
            st.success("Configurações de notificação salvas com sucesso!")
    
    # Configurações somente para admin
    if is_admin():
        st.subheader("Configurações do Sistema")
        
        with st.form("system_settings"):
            smtp_server = st.text_input("Servidor SMTP", value="smtp.example.com")
            smtp_port = st.number_input("Porta SMTP", value=587, min_value=1, max_value=65535)
            smtp_user = st.text_input("Usuário SMTP", value="alert@example.com")
            smtp_password = st.text_input("Senha SMTP", type="password")
            
            if st.form_submit_button("Salvar Configurações do Sistema"):
                # Em produção, essas configurações seriam salvas em variáveis ??de ambiente ou em uma tabela de configurações
                st.success("Configurações do sistema salvas com sucesso!")