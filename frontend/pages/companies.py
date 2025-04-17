import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
import re
from frontend.utils.api import get_api_data
from frontend.utils.auth import is_admin
from utils.ui import display_menu, show_delete_button
from utils.auth import login_user, logout_user, is_admin
from utils.image import get_image_base64, save_company_logo
from utils.api import get_api_data, post_api_data, put_api_data, delete_api_data
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
API_URL = os.getenv("API_URL")

# Constantes
PAYMENT_METHODS = ["Transferência Bancária", "Débito Direto", "Cartão de Crédito", "Outro"]

# Funções auxiliares
def validate_email(email):
    """Valida formato de email."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) if email else True

def validate_iban(iban):
    """Validação básica de IBAN."""
    # Validação simplificada para IBAN português (PT)
    if not iban:
        return True
    iban = iban.replace(" ", "")
    return len(iban) == 25 and iban.startswith("PT")

def validate_tax_id(tax_id):
    """Validação básica de NIF/NIPC."""
    if not tax_id:
        return True
    tax_id = tax_id.replace(" ", "")
    return len(tax_id) == 9 and tax_id.isdigit()

def render_company_card(comp):
    is_editing = st.session_state.get("edit_company_id") == comp["id"]
    border = "2px solid #1abc9c" if is_editing else "1px solid #dcdcdc"
    shadow = "0 4px 8px rgba(0, 0, 0, 0.05)" if is_editing else "0 2px 4px rgba(0, 0, 0, 0.03)"

    st.markdown(
        f"<h2 style='color:#34495e; font-size: 26px; margin: 0;'>{comp['name']}</h2>",
        unsafe_allow_html=True
    )

    with st.expander("📄 Ver detalhes", expanded=is_editing):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<h4 style='color:#34495e;'><i class='fas fa-info-circle'></i> Dados Gerais</h4>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#34495e;'><i class='fas fa-hashtag'></i> <strong>ID:</strong> {comp.get('id')}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#34495e;'><i class='fas fa-map-marker-alt'></i> <strong>Morada:</strong> {comp.get('address') or '-'}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#34495e;'><i class='fas fa-city'></i> <strong>Cidade:</strong> {comp.get('city') or '-'}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#34495e;'><i class='fas fa-mail-bulk'></i> <strong>Código Postal:</strong> {comp.get('postal_code') or '-'}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#34495e;'><i class='fas fa-globe-europe'></i> <strong>País:</strong> {comp.get('country') or '-'}</span>", unsafe_allow_html=True)

        with col2:
            st.markdown("<h4 style='color:#34495e;'><i class='fas fa-briefcase'></i> Faturação</h4>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#34495e;'><i class='fas fa-id-card'></i> <strong>NIF/NIPC:</strong> {comp.get('tax_id') or '-'}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#34495e;'><i class='fas fa-envelope'></i> <strong>Email:</strong> {comp.get('billing_email') or '-'}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#34495e;'><i class='fas fa-phone-alt'></i> <strong>Telefone:</strong> {comp.get('phone') or '-'}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#34495e;'><i class='fas fa-credit-card'></i> <strong>Pagamento:</strong> {comp.get('payment_method') or '-'}</span>", unsafe_allow_html=True)

            if (iban := comp.get("iban")):
                masked_iban = iban[:4] + " ●●●● ●●●● " + iban[-4:] if len(iban) > 8 else iban
                st.markdown(f"<span style='color:#34495e;'><i class='fas fa-university'></i> <strong>IBAN:</strong> {masked_iban}</span>", unsafe_allow_html=True)

            machines = get_api_data(f"machines/company/{comp['id']}") or []
            st.markdown(f"<span style='color:#34495e;'><i class='fas fa-truck'></i> <strong>Máquinas:</strong> {len(machines)}</span>", unsafe_allow_html=True)



        if is_admin():
            st.markdown("---")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.button(
                    "✏️ Editar",
                    key=f"edit_company_{comp['id']}",
                    on_click=lambda id=comp["id"], name=comp["name"],
                    address=comp.get("address", ""): set_edit_state(id, name, address)
                )
            with col_b2:
                show_delete_button(
                    "company",
                    comp["id"],
                    label="🗑️ Excluir",
                    confirm_text=f"Tem certeza que deseja excluir {comp['name']}?"
                )

def render_edit_form(comp):
    st.markdown("## ✏️ Editar Empresa")

    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Nome da Empresa", value=st.session_state.get("edit_company_name", comp.get("name", "")))
        new_tax_id = st.text_input("NIF/NIPC", value=comp.get("tax_id", ""))
        new_address = st.text_input("Morada", value=st.session_state.get("edit_company_address", comp.get("address", "")))
        new_postal_code = st.text_input("Código Postal", value=comp.get("postal_code", ""))
        new_city = st.text_input("Cidade", value=comp.get("city", ""))
        new_country = st.text_input("País", value=comp.get("country", "Portugal"))

    with col2:
        new_billing_email = st.text_input("Email de Faturação", value=comp.get("billing_email", ""))
        new_phone = st.text_input("Telefone", value=comp.get("phone", ""))

        payment_options = PAYMENT_METHODS
        current_payment = comp.get("payment_method", payment_options[0])
        payment_index = payment_options.index(current_payment) if current_payment in payment_options else 0

        new_payment_method = st.selectbox("Método de Pagamento Preferido", payment_options, index=payment_index)
        new_iban = st.text_input("IBAN (para transferências)", value=comp.get("iban", ""))
        new_logo = st.file_uploader("Atualizar Logo (opcional)", type=["png", "jpg", "jpeg"])

    # Validações
    errors = []
    if new_billing_email and not validate_email(new_billing_email):
        errors.append("Email de faturação inválido.")
    if new_iban and not validate_iban(new_iban):
        errors.append("IBAN inválido.")
    if new_tax_id and not validate_tax_id(new_tax_id):
        errors.append("NIF/NIPC deve ter 9 dígitos.")

    for err in errors:
        st.warning(err)

    col1, col2 = st.columns(2)
    with col1:
        submit = st.button("💾 Guardar Alterações", key=f"submit_edit_{comp['id']}")
    with col2:
        cancel = st.button("❌ Cancelar", key=f"cancel_edit_{comp['id']}")

    if submit and not errors:
        update_data = {
            "name": new_name,
            "address": new_address,
            "tax_id": new_tax_id,
            "postal_code": new_postal_code,
            "city": new_city,
            "country": new_country,
            "billing_email": new_billing_email,
            "phone": new_phone,
            "payment_method": new_payment_method,
            "iban": new_iban,
        }

        if new_logo:
            logo_relative_path = save_company_logo(comp['id'], new_logo)
            if logo_relative_path:
                update_data["logo_path"] = logo_relative_path

        if put_api_data(f"companies/{comp['id']}", update_data):
            st.success("Empresa atualizada com sucesso.")
            st.session_state.pop("edit_company_id", None)
            st.rerun()
        else:
            st.error("Erro ao atualizar empresa.")

    if cancel:
        st.session_state.pop("edit_company_id", None)
        st.rerun()


def show_companies():
    st.title("Gestão de Empresas")
    st.markdown("""
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    """, unsafe_allow_html=True)
    st.markdown("Visualize e edite os dados das empresas associadas.")
    
    
    # Inicializar estados de sessão necessários
    if "company_filter" not in st.session_state:
        st.session_state.company_filter = ""
    
    # Buscar empresas - admins veem todas, gestores de frota veem apenas a própria
    if is_admin():
        companies = get_api_data("companies") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            company = get_api_data(f"companies/{company_id}")
            companies = [company] if company else []
        else:
            companies = []
    
    # Interface dividida em duas seções: Adicionar e Listar
    tabs = ["Empresas Existentes"]
    if is_admin():
        tabs.append("Adicionar Nova Empresa")

    selected_tab = st.tabs(tabs)
    tab1 = selected_tab[0]
    tab2 = selected_tab[1] if is_admin() else None
    
    # TAB 1: Listar Empresas Existentes
    with tab1:
        if companies:
            # Contador e filtro
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Total de empresas:** {len(companies)}")
            
            
            # Aplicar filtro
            filtered_companies = companies
            if st.session_state.company_filter:
                search_term = st.session_state.company_filter.lower()
                filtered_companies = [c for c in companies if search_term in c['name'].lower()]
            
            if not filtered_companies:
                st.info("Nenhuma empresa encontrada com o filtro aplicado.")
            
            # Exibir empresas em cards estilizados
            if filtered_companies:
                for comp in filtered_companies:
                    render_company_card(comp)

                    if is_admin() and st.session_state.get("edit_company_id") == comp["id"]:
                        render_edit_form(comp)
            else:
                st.info("Nenhuma empresa encontrada com o filtro aplicado.")
        
    # TAB 2: Adicionar Nova Empresa (apenas para admins)
    if is_admin():
        with tab2:
            with st.form("new_company"):
                st.subheader("Adicionar Nova Empresa")
                
                col1, col2 = st.columns(2)
                with col1:
                    company_name = st.text_input("Nome da Empresa")
                    tax_id = st.text_input("NIF/NIPC")
                    company_address = st.text_input("Morada")
                    postal_code = st.text_input("Código Postal")
                    city = st.text_input("Cidade")
                    country = st.text_input("País", value="Portugal")
                
                with col2:
                    billing_email = st.text_input("Email de Faturação")
                    phone = st.text_input("Telefone")
                    payment_method = st.selectbox("Método de Pagamento Preferido", PAYMENT_METHODS)
                    iban = st.text_input("IBAN (para transferências bancárias)")
                    company_logo = st.file_uploader("Logo da Empresa (opcional)", type=["png", "jpg", "jpeg"])
                
                # Validação de campos
                validation_errors = []
                if billing_email and not validate_email(billing_email):
                    validation_errors.append("O email de faturação não está em um formato válido.")
                if iban and not validate_iban(iban):
                    validation_errors.append("O IBAN não parece estar em um formato válido.")
                if tax_id and not validate_tax_id(tax_id):
                    validation_errors.append("O NIF/NIPC deve ter 9 dígitos.")
                
                # Exibir erros de validação
                for error in validation_errors:
                    st.warning(error)
                
                submitted = st.form_submit_button("Adicionar Empresa")
                
                if submitted and company_name and not validation_errors:
                    # Preparar dados para envio
                    company_data = {
                        "name": company_name,
                        "address": company_address,
                        "tax_id": tax_id,
                        "postal_code": postal_code,
                        "city": city,
                        "country": country,
                        "billing_email": billing_email,
                        "phone": phone,
                        "payment_method": payment_method,
                        "iban": iban
                    }
                    
                    # Criar empresa
                    new_company_response = requests.post(
                        f"{API_URL}/companies", 
                        headers={"Authorization": f"Bearer {st.session_state['token']}"},
                        json=company_data
                    )
                    
                    if new_company_response.status_code in [200, 201]:
                        new_company = new_company_response.json()
                        company_id = new_company["id"]
                        
                        # Se um logo foi enviado, salvar e atualizar caminho
                        if company_logo:
                            logo_relative_path = save_company_logo(company_id, company_logo)
                            
                            if logo_relative_path:
                                # Atualizar o caminho do logo no banco de dados
                                update_data = {"logo_path": logo_relative_path}
                                put_api_data(f"companies/{company_id}", update_data)
                        
                        st.success(f"Empresa '{company_name}' adicionada com sucesso!")
                        # Mudar para a aba de listagem depois de adicionar
                        st.rerun()
                    else:
                        st.error(f"Erro ao criar empresa: {new_company_response.text}")
        

def set_edit_state(company_id, name, address):
    """Função auxiliar para configurar o estado de edição."""
    st.session_state["edit_company_id"] = company_id
    st.session_state["edit_company_name"] = name
    st.session_state["edit_company_address"] = address