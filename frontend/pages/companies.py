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

def update_company_direct(company_id, update_data):
    """
    Função para atualização direta da empresa via API REST.
    Mostra cada passo do processo e o resultado detalhado.
    """
    if "token" not in st.session_state:
        st.error("Não autenticado. Faça login novamente.")
        return False
    
    # Exibir dados que serão enviados
    st.write("### Requisição para atualizar empresa")
    st.write(f"**ID da empresa:** {company_id}")
    st.write("**Dados a enviar:**")
    for key, value in update_data.items():
        st.write(f"- {key}: `{value}`")
    
    # Preparar a requisição com autenticação
    headers = {
        "Authorization": f"Bearer {st.session_state['token']}",
        "Content-Type": "application/json"
    }
    
    # URL completa da API
    url = f"{API_URL}/companies/{company_id}"
    st.write(f"**URL:** {url}")
    
    try:
        # Fazer a requisição PUT para a API
        response = requests.put(url, headers=headers, json=update_data)
        
        # Exibir informações da resposta
        st.write("### Resposta da API")
        st.write(f"**Status code:** {response.status_code}")
        st.write(f"**Headers:**")
        for header, value in response.headers.items():
            st.write(f"- {header}: {value}")
        
        # Tentar mostrar o corpo da resposta como JSON se possível
        try:
            response_data = response.json()
            st.write("**Corpo da resposta (JSON):**")
            st.json(response_data)
        except:
            st.write("**Corpo da resposta (texto):**")
            st.code(response.text)
        
        # Verificar se a atualização foi bem-sucedida
        if response.status_code in [200, 201, 204]:
            # Verificar se os dados foram realmente atualizados buscando a empresa novamente
            updated_company = get_api_data(f"companies/{company_id}")
            
            if updated_company:
                st.write("### Verificação de atualização")
                st.write("**Dados após atualização:**")
                st.json(updated_company)
                
                # Verificar se cada campo foi atualizado corretamente
                all_updated = True
                for key, value in update_data.items():
                    if key in updated_company:
                        if updated_company[key] != value:
                            st.error(f"Campo '{key}' não foi atualizado. Enviado: '{value}', Recebido: '{updated_company[key]}'")
                            all_updated = False
                    else:
                        st.warning(f"Campo '{key}' não está presente na resposta da API.")
                
                if all_updated:
                    st.success("Todos os campos foram atualizados com sucesso!")
                    return True
                else:
                    st.warning("Alguns campos podem não ter sido atualizados corretamente.")
                    return False
            else:
                st.error("Não foi possível verificar a atualização: falha ao buscar os dados atualizados.")
                return False
        else:
            st.error(f"Falha na atualização. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        st.error(f"Erro durante a comunicação com a API: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return False

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
                    on_click=lambda id=comp["id"]: set_edit_state(id, comp)
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

    # Certifique-se de que todos os valores da empresa estejam no session_state
    if "edit_company_data" not in st.session_state:
        set_edit_state(comp["id"], comp)
    
    # Mostrar os dados originais da empresa para referência
    with st.expander("Dados originais da empresa (Debug)", expanded=False):
        st.json(st.session_state.edit_company_data)

    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Nome da Empresa", value=st.session_state.edit_company_data.get("name", ""))
        new_tax_id = st.text_input("NIF/NIPC", value=st.session_state.edit_company_data.get("tax_id", ""))
        new_address = st.text_input("Morada", value=st.session_state.edit_company_data.get("address", ""))
        new_postal_code = st.text_input("Código Postal", value=st.session_state.edit_company_data.get("postal_code", ""))
        new_city = st.text_input("Cidade", value=st.session_state.edit_company_data.get("city", ""))
        new_country = st.text_input("País", value=st.session_state.edit_company_data.get("country", "Portugal"))

    with col2:
        new_billing_email = st.text_input("Email de Faturação", value=st.session_state.edit_company_data.get("billing_email", ""))
        new_phone = st.text_input("Telefone", value=st.session_state.edit_company_data.get("phone", ""))

        # Verificar se o valor atual de payment_method está nos métodos disponíveis
        current_payment = st.session_state.edit_company_data.get("payment_method", PAYMENT_METHODS[0])
        payment_index = PAYMENT_METHODS.index(current_payment) if current_payment in PAYMENT_METHODS else 0

        new_payment_method = st.selectbox("Método de Pagamento Preferido", PAYMENT_METHODS, index=payment_index)
        new_iban = st.text_input("IBAN (para transferências)", value=st.session_state.edit_company_data.get("iban", ""))
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

    # Criar dois botões - um normal e um para diagnóstico detalhado
    col1, col2, col3 = st.columns(3)
    with col1:
        submit = st.button("💾 Guardar Alterações", key=f"submit_edit_{comp['id']}")
    with col2:
        submit_debug = st.button("🔍 Guardar com Diagnóstico", key=f"submit_debug_{comp['id']}")
    with col3:
        cancel = st.button("❌ Cancelar", key=f"cancel_edit_{comp['id']}")

    if (submit or submit_debug) and not errors:
        # Preparar todos os dados para envio, incluindo valores originais para campos não alterados
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
            "iban": new_iban
        }

        # Se o logo foi atualizado, processar
        if new_logo:
            logo_relative_path = save_company_logo(comp['id'], new_logo)
            if logo_relative_path:
                update_data["logo_path"] = logo_relative_path

        # Modo de diagnóstico detalhado
        if submit_debug:
            st.write("### Diagnóstico de Atualização")
            success = update_company_direct(comp['id'], update_data)
            
            if success:
                st.success("✅ Empresa atualizada com sucesso!")
                # Limpar os estados de edição e recarregar a página
                if "edit_company_id" in st.session_state:
                    del st.session_state["edit_company_id"]
                if "edit_company_data" in st.session_state:
                    del st.session_state["edit_company_data"]
                st.rerun()
        else:
            # Modo de atualização normal
            try:
                # Usar a API diretamente em vez da função put_api_data
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                response = requests.put(
                    f"{API_URL}/companies/{comp['id']}",
                    headers=headers,
                    json=update_data
                )
                
                if response.status_code in [200, 201, 204]:
                    st.success("Empresa atualizada com sucesso!")
                    # Limpar estados de sessão relacionados à edição
                    if "edit_company_id" in st.session_state:
                        del st.session_state["edit_company_id"]
                    if "edit_company_data" in st.session_state:
                        del st.session_state["edit_company_data"]
                    st.rerun()
                else:
                    st.error(f"Erro ao atualizar empresa. Código: {response.status_code}")
                    st.error(f"Resposta: {response.text}")
                    st.info("Tente usar o botão 'Guardar com Diagnóstico' para mais detalhes.")
            except Exception as e:
                st.error(f"Erro ao comunicar com a API: {str(e)}")
                st.info("Tente usar o botão 'Guardar com Diagnóstico' para mais detalhes.")

    if cancel:
        # Limpar estados de sessão relacionados à edição
        if "edit_company_id" in st.session_state:
            del st.session_state["edit_company_id"]
        if "edit_company_data" in st.session_state:
            del st.session_state["edit_company_data"]
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

                    # Usar a função post_api_data em vez de requests diretamente
                    result = post_api_data("companies", company_data)
                    if result:
                        # Obter o ID da nova empresa - precisamos buscar pelo nome
                        companies = get_api_data("companies")
                        new_company = next((c for c in companies if c["name"] == company_name), None)
                        
                        if new_company:
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
                        st.error(f"Erro ao criar empresa.")
                    
                    if result.status_code in [200, 201]:
                        new_company = result.json()
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
                        st.error(f"Erro ao criar empresa: {result.text}")
        

def set_edit_state(company_id, company_data):
    """
    Função auxiliar para configurar o estado de edição com todos os dados da empresa.
    Lida com dados incompletos garantindo que todos os campos estejam presentes.
    """
    # Buscar dados completos da empresa diretamente da API
    full_company_data = get_api_data(f"companies/{company_id}")
    
    if not full_company_data:
        st.error(f"Não foi possível obter os dados completos da empresa ID {company_id}")
        full_company_data = company_data  # Usar os dados parciais se a requisição falhar
    
    # Garantir que todos os campos necessários existam com valores padrão
    complete_data = {
        "id": company_id,
        "name": full_company_data.get("name", ""),
        "address": full_company_data.get("address", ""),
        "tax_id": full_company_data.get("tax_id", ""),
        "postal_code": full_company_data.get("postal_code", ""),
        "city": full_company_data.get("city", ""),
        "country": full_company_data.get("country", "Portugal"),
        "billing_email": full_company_data.get("billing_email", ""),
        "phone": full_company_data.get("phone", ""),
        "payment_method": full_company_data.get("payment_method", ""),
        "iban": full_company_data.get("iban", ""),
        "logo_path": full_company_data.get("logo_path", "")
    }
    
    # Armazenar no estado da sessão
    st.session_state["edit_company_id"] = company_id
    st.session_state["edit_company_data"] = complete_data