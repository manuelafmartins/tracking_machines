import streamlit as st
import pandas as pd
import io
import base64
from datetime import datetime, timedelta
import plotly.express as px
import requests
from frontend.utils.api import get_api_data, post_api_data, put_api_data, delete_api_data
from frontend.utils.auth import is_admin
from utils.ui import show_delete_button
import os
from dotenv import load_dotenv
import json
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# Carregar variáveis de ambiente
load_dotenv()

# Status da fatura para exibição em português
INVOICE_STATUS_DISPLAY = {
    "draft": "Rascunho",
    "sent": "Enviada",
    "paid": "Paga",
    "overdue": "Vencida",
    "canceled": "Cancelada"
}

# Status da fatura para cores
INVOICE_STATUS_COLORS = {
    "draft": "gray",
    "sent": "blue",
    "paid": "green",
    "overdue": "red",
    "canceled": "orange"
}

def generate_invoice_pdf(invoice_data):
    """Gera um PDF da fatura"""
    buffer = io.BytesIO()
    
    # Criar o documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Estilos para o PDF
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1))
    styles.add(ParagraphStyle(name='Right', alignment=2))
    
    # Lista para armazenar o conteúdo do PDF
    elements = []
    
    # Título da fatura
    elements.append(Paragraph(f"FATURA Nº {invoice_data['invoice_number']}", styles['Heading1']))
    elements.append(Spacer(1, 12))
    
    # Data de emissão e vencimento
    date_info = [
        ["Data de emissão:", invoice_data['issue_date']],
        ["Data de vencimento:", invoice_data['due_date']]
    ]
    date_table = Table(date_info, colWidths=[120, 120])
    date_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
    ]))
    elements.append(date_table)
    elements.append(Spacer(1, 20))
    
    # Informações da empresa
    company = invoice_data.get('company', {})
    company_data = [
        ["Empresa:", company.get('name', '')],
        ["NIF:", company.get('tax_id', '')],
        ["Morada:", company.get('address', '')],
        ["Código Postal:", company.get('postal_code', '')],
        ["Cidade:", company.get('city', '')],
        ["País:", company.get('country', '')],
    ]
    
    company_table = Table(company_data, colWidths=[120, 300])
    company_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 20))
    
    # Itens da fatura
    items = invoice_data.get('items', [])
    item_data = [['Descrição', 'Qtd', 'Preço Unit.', 'IVA %', 'Total']]
    
    for item in items:
        item_row = [
            item.get('description', ''),
            f"{item.get('quantity', 0):.2f}",
            f"{item.get('unit_price', 0):.2f} €",
            f"{item.get('tax_rate', 0):.0f}%",
            f"{item.get('total', 0):.2f} €"
        ]
        item_data.append(item_row)
    
    # Adicionar totais
    item_data.append(['', '', '', 'Subtotal:', f"{invoice_data.get('subtotal', 0):.2f} €"])
    item_data.append(['', '', '', 'IVA Total:', f"{invoice_data.get('tax_total', 0):.2f} €"])
    item_data.append(['', '', '', 'TOTAL:', f"{invoice_data.get('total', 0):.2f} €"])
    
    item_table = Table(item_data, colWidths=[200, 50, 80, 80, 80])
    item_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('INNERGRID', (0, 0), (-1, -4), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -4), 0.25, colors.black),
        ('LINEABOVE', (3, -3), (-1, -3), 1, colors.black),
        ('LINEABOVE', (3, -1), (-1, -1), 2, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (3, -3), (3, -1), 'Helvetica-Bold'),
        ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 20))
    
    # Informações de pagamento
    if invoice_data.get('payment_method'):
        elements.append(Paragraph(f"Método de Pagamento: {invoice_data['payment_method']}", styles['Normal']))
    
    if invoice_data.get('notes'):
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Notas:", styles['Normal']))
        elements.append(Paragraph(invoice_data['notes'], styles['Normal']))
    
    # Construir o PDF
    doc.build(elements)
    
    # Obter o conteúdo do buffer
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

def get_download_link(pdf_bytes, filename):
    """Cria um link para download do PDF"""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Baixar PDF</a>'
    return href

def show_billing():
    st.title("Gestão de Faturação")
    
    # Inicializar estado para itens de fatura 
    if "invoice_items" not in st.session_state:
        st.session_state.invoice_items = []
    
    # Inicializar estado para o item a ser adicionado
    if "new_item_service_id" not in st.session_state:
        st.session_state.new_item_service_id = None
        st.session_state.new_item_quantity = 1.0
        st.session_state.new_item_price = 0.0
        st.session_state.new_item_machine_id = None
        st.session_state.new_item_description = ""
    
    # Criar tabs para organizar o módulo
    tab1, tab2, tab3 = st.tabs(["Faturas", "Serviços", "Relatórios"])
    
    # TAB 1: FATURAS
    with tab1:
        # Buscar empresas para o dropdown
        companies = get_api_data("companies") or []
        
        # Seção para criar nova fatura
        with st.expander("Criar Nova Fatura", expanded=False):
            # Formulário principal para criar fatura
            with st.form("new_invoice_form"):
                if not companies:
                    st.warning("Não existem empresas cadastradas. Cadastre uma empresa primeiro.")
                    st.form_submit_button("OK", disabled=True)
                    st.stop()
                
                # Selecionar empresa
                company_options = [c["id"] for c in companies]
                company_labels = [c["name"] for c in companies]
                
                selected_company_idx = st.selectbox(
                    "Empresa",
                    options=range(len(company_options)),
                    format_func=lambda idx: company_labels[idx],
                    key="invoice_company_select"
                )
                selected_company_id = company_options[selected_company_idx]
                
                # Buscar máquinas da empresa selecionada
                machines = get_api_data(f"machines/company/{selected_company_id}") or []
                
                # Datas da fatura
                col1, col2 = st.columns(2)
                with col1:
                    issue_date = st.date_input(
                        "Data de Emissão",
                        value=datetime.now().date()
                    )
                with col2:
                    due_date = st.date_input(
                        "Data de Vencimento",
                        value=datetime.now().date() + timedelta(days=30)
                    )
                
                # Método de pagamento
                payment_method = st.selectbox(
                    "Método de Pagamento",
                    ["Transferência Bancária", "Débito Direto", "Cartão de Crédito", "Outro"]
                )
                
                # Notas
                notes = st.text_area("Notas/Observações")
                
                # Exibir itens já adicionados (se existirem)
                if st.session_state.invoice_items:
                    st.subheader("Itens adicionados à fatura:")
                    
                    items_df = pd.DataFrame(st.session_state.invoice_items)
                    if not items_df.empty:
                        display_columns = ["description", "quantity", "unit_price", "tax_rate", "total"]
                        display_names = ["Descrição", "Qtd", "Preço Unit.", "IVA %", "Total"]
                        
                        # Se tiver máquinas, mostrar coluna adicional
                        if any(item.get("machine_id") for item in st.session_state.invoice_items):
                            display_columns.insert(1, "machine_name")
                            display_names.insert(1, "Máquina")
                        
                        # Formatar os valores para exibição
                        formatted_df = items_df.copy()
                        for col in ["unit_price", "subtotal", "tax_amount", "total"]:
                            if col in formatted_df.columns:
                                formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.2f} €")
                        
                        formatted_df["tax_rate"] = formatted_df["tax_rate"].apply(lambda x: f"{x:.0f}%")
                        
                        st.table(formatted_df[display_columns].rename(columns=dict(zip(display_columns, display_names))))
                        
                        # Calcular totais
                        subtotal = sum(item["subtotal"] for item in st.session_state.invoice_items)
                        tax_total = sum(item["tax_amount"] for item in st.session_state.invoice_items)
                        total = subtotal + tax_total
                        
                        st.write(f"**Subtotal:** {subtotal:.2f} €")
                        st.write(f"**IVA Total:** {tax_total:.2f} €")
                        st.write(f"**TOTAL:** {total:.2f} €")
                        
                        # Botão para limpar itens (dentro do formulário)
                        clear_items = st.form_submit_button("Limpar todos os itens")
                        if clear_items:
                            st.session_state.invoice_items = []
                            st.rerun()
                
                # Botões do formulário
                submit_button = st.form_submit_button("Criar Fatura")
                
                if submit_button:
                    if not st.session_state.invoice_items:
                        st.error("Adicione pelo menos um item à fatura.")
                    else:
                        # Preparar dados para envio
                        invoice_data = {
                            "company_id": selected_company_id,
                            "issue_date": issue_date.isoformat(),
                            "due_date": due_date.isoformat(),
                            "notes": notes,
                            "payment_method": payment_method,
                            "status": "draft",
                            "items": [
                                {
                                    "service_id": item["service_id"],
                                    "machine_id": item["machine_id"],
                                    "quantity": item["quantity"],
                                    "description": item["description"],
                                    "unit_price": item["unit_price"],
                                    "tax_rate": item["tax_rate"]
                                }
                                for item in st.session_state.invoice_items
                            ]
                        }
                        
                        # Enviar para a API
                        response = post_api_data("billing/invoices", invoice_data)
                        if response:
                            st.success("Fatura criada com sucesso!")
                            st.session_state.invoice_items = []
                            st.rerun()
            
            # Formulário para adicionar item (separado do formulário principal)
            services = get_api_data("billing/services?active_only=true") or []
            if services:
                st.subheader("Adicionar Item à Fatura")
                with st.form("add_item_form"):
                    service_options = [s["id"] for s in services]
                    service_labels = [f"{s['name']} ({s['unit_price']}€)" for s in services]
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        selected_service_idx = st.selectbox(
                            "Serviço",
                            options=range(len(service_options)),
                            format_func=lambda idx: service_labels[idx],
                            key="new_item_service_select"
                        )
                        selected_service_id = service_options[selected_service_idx]
                        selected_service = next((s for s in services if s["id"] == selected_service_id), None)
                    
                    with col2:
                        quantity = st.number_input("Quantidade", min_value=0.1, value=1.0, step=0.1, key="new_item_quantity_input")
                    
                    with col3:
                        unit_price = st.number_input(
                            "Preço Unit.",
                            min_value=0.0,
                            value=selected_service["unit_price"] if selected_service else 0.0,
                            step=0.01,
                            key="new_item_price_input"
                        )
                    
                    # Máquina associada (opcional)
                    if machines:
                        machine_options = [0] + [m["id"] for m in machines]
                        machine_labels = ["Nenhuma"] + [m["name"] for m in machines]
                        
                        selected_machine_idx = st.selectbox(
                            "Máquina (opcional)",
                            options=range(len(machine_options)),
                            format_func=lambda idx: machine_labels[idx],
                            key="new_item_machine_select"
                        )
                        selected_machine_id = machine_options[selected_machine_idx] if selected_machine_idx > 0 else None
                    else:
                        selected_machine_id = None
                    
                    # Descrição personalizada
                    custom_description = st.text_input(
                        "Descrição Personalizada (opcional)",
                        value=selected_service["name"] if selected_service else "",
                        key="new_item_description_input"
                    )
                    
                    # Botão para adicionar item à lista - usando form_submit_button
                    submitted = st.form_submit_button("Adicionar Item")
                    
                    if submitted:
                        tax_rate = selected_service["tax_rate"] if selected_service else 23.0
                        subtotal = quantity * unit_price
                        tax_amount = subtotal * (tax_rate / 100)
                        total = subtotal + tax_amount
                        
                        new_item = {
                            "service_id": selected_service_id,
                            "machine_id": selected_machine_id,
                            "quantity": quantity,
                            "unit_price": unit_price,
                            "tax_rate": tax_rate,
                            "description": custom_description,
                            "subtotal": subtotal,
                            "tax_amount": tax_amount,
                            "total": total,
                            # Campos extras para exibição na UI
                            "service_name": selected_service["name"] if selected_service else "",
                            "machine_name": next((m["name"] for m in machines if m["id"] == selected_machine_id), "") if selected_machine_id else ""
                        }
                        
                        st.session_state.invoice_items.append(new_item)
                        st.success("Item adicionado!")
                        st.rerun()
            else:
                st.warning("Não existem serviços cadastrados. Cadastre um serviço primeiro na aba 'Serviços'.")
        
        # Lista de faturas existentes
        st.subheader("Faturas Existentes")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["Todos", "Rascunho", "Enviada", "Paga", "Vencida", "Cancelada"],
                key="invoice_status_filter"
            )
        with col2:
            # Filtro de data
            date_range = st.selectbox(
                "Período",
                ["Todos", "Este mês", "Último mês", "Este ano", "Personalizado"],
                key="invoice_date_filter"
            )
        with col3:
            # Filtro de empresa (só para admin)
            if is_admin():
                company_options = ["Todas"] + [c["name"] for c in companies]
                company_filter = st.selectbox(
                    "Empresa",
                    company_options,
                    key="invoice_company_filter"
                )
        
        # Datas personalizadas se selecionado
        if date_range == "Personalizado":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Data Inicial", value=datetime.now().date() - timedelta(days=30))
            with col2:
                end_date = st.date_input("Data Final", value=datetime.now().date())
        
        # Buscar as faturas
        invoices = get_api_data("billing/invoices") or []
        
        # Aplicar filtros
        if invoices:
            filtered_invoices = invoices.copy()
            
            # Filtro de status
            if status_filter != "Todos":
                status_map = {
                    "Rascunho": "draft",
                    "Enviada": "sent",
                    "Paga": "paid",
                    "Vencida": "overdue",
                    "Cancelada": "canceled"
                }
                filtered_invoices = [inv for inv in filtered_invoices if inv["status"] == status_map.get(status_filter, "")]
            
            # Filtro de data
            today = datetime.now().date()
            if date_range == "Este mês":
                month_start = datetime(today.year, today.month, 1).date()
                filtered_invoices = [
                    inv for inv in filtered_invoices 
                    if datetime.strptime(inv["issue_date"], "%Y-%m-%d").date() >= month_start
                ]
            elif date_range == "Último mês":
                last_month = today.month - 1 if today.month > 1 else 12
                last_month_year = today.year if today.month > 1 else today.year - 1
                month_start = datetime(last_month_year, last_month, 1).date()
                if last_month == 12:
                    month_end = datetime(last_month_year + 1, 1, 1).date() - timedelta(days=1)
                else:
                    month_end = datetime(last_month_year, last_month + 1, 1).date() - timedelta(days=1)
                
                filtered_invoices = [
                    inv for inv in filtered_invoices 
                    if month_start <= datetime.strptime(inv["issue_date"], "%Y-%m-%d").date() <= month_end
                ]
            elif date_range == "Este ano":
                year_start = datetime(today.year, 1, 1).date()
                filtered_invoices = [
                    inv for inv in filtered_invoices 
                    if datetime.strptime(inv["issue_date"], "%Y-%m-%d").date() >= year_start
                ]
            elif date_range == "Personalizado":
                filtered_invoices = [
                    inv for inv in filtered_invoices 
                    if start_date <= datetime.strptime(inv["issue_date"], "%Y-%m-%d").date() <= end_date
                ]
            
            # Filtro de empresa (admin)
            if is_admin() and company_filter != "Todas":
                company_id = next((c["id"] for c in companies if c["name"] == company_filter), None)
                if company_id:
                    filtered_invoices = [inv for inv in filtered_invoices if inv["company_id"] == company_id]
            
            # Exibir faturas filtradas
            if filtered_invoices:
                # Adicionar nomes de empresas
                for inv in filtered_invoices:
                    company = next((c for c in companies if c["id"] == inv["company_id"]), None)
                    inv["company_name"] = company["name"] if company else "Desconhecida"
                
                # Ordenar por data (mais recentes primeiro)
                filtered_invoices = sorted(
                    filtered_invoices,
                    key=lambda x: datetime.strptime(x["issue_date"], "%Y-%m-%d"),
                    reverse=True
                )
                
                # Inicialização de estado para PDF e ações
                if "current_pdf_invoice" not in st.session_state:
                    st.session_state.current_pdf_invoice = None
                    
                # Inicializar dicionário de estados para cada fatura
                if "invoice_actions" not in st.session_state:
                    st.session_state.invoice_actions = {}
                
                # Exibir cada fatura em um expander
                for invoice in filtered_invoices:
                    invoice_id = invoice['id']
                    status_display = INVOICE_STATUS_DISPLAY.get(invoice["status"], invoice["status"])
                    status_color = INVOICE_STATUS_COLORS.get(invoice["status"], "gray")
                    
                    # Inicializar estado específico para essa fatura se não existir
                    if invoice_id not in st.session_state.invoice_actions:
                        st.session_state.invoice_actions[invoice_id] = {
                            'show_pdf': False
                        }
                    
                    with st.expander(f"Fatura {invoice['invoice_number']} - {invoice['company_name']} - {status_display} - {invoice['issue_date']}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Empresa:** {invoice['company_name']}")
                            st.write(f"**Número:** {invoice['invoice_number']}")
                            st.write(f"**Data de Emissão:** {invoice['issue_date']}")
                            st.write(f"**Data de Vencimento:** {invoice['due_date']}")
                            st.write(f"**Status:** <span style='color:{status_color};font-weight:bold;'>{status_display}</span>", unsafe_allow_html=True)
                            
                            if invoice.get("payment_date"):
                                st.write(f"**Data de Pagamento:** {invoice['payment_date']}")
                            
                            st.write(f"**Método de Pagamento:** {invoice.get('payment_method', 'Não especificado')}")
                            
                            if invoice.get("notes"):
                                st.write(f"**Notas:** {invoice['notes']}")
                            
                            st.write(f"**Subtotal:** {invoice['subtotal']:.2f} €")
                            st.write(f"**IVA Total:** {invoice['tax_total']:.2f} €")
                            st.write(f"**TOTAL:** {invoice['total']:.2f} €")
                        
                        with col2:
                            # Usamos um formulário separado para cada ação de fatura
                            # Botão para gerar PDF
                            if st.button("Gerar PDF", key=f"pdf_btn_{invoice['id']}"):
                                # Buscar detalhes da empresa para o PDF
                                company = get_api_data(f"companies/{invoice['company_id']}")
                                if company:
                                    invoice['company'] = company
                                
                                pdf_bytes = generate_invoice_pdf(invoice)
                                filename = f"fatura_{invoice['invoice_number']}.pdf"
                                
                                # Salvar o PDF na sessão
                                st.session_state.invoice_actions[invoice_id]['pdf_bytes'] = pdf_bytes
                                st.session_state.invoice_actions[invoice_id]['pdf_filename'] = filename
                                st.session_state.invoice_actions[invoice_id]['show_pdf'] = True
                                st.rerun()
                            
                            # Mostrar link para download se o PDF foi gerado
                            if st.session_state.invoice_actions[invoice_id].get('show_pdf'):
                                pdf_bytes = st.session_state.invoice_actions[invoice_id].get('pdf_bytes')
                                filename = st.session_state.invoice_actions[invoice_id].get('pdf_filename')
                                st.markdown(get_download_link(pdf_bytes, filename), unsafe_allow_html=True)
                            
                            # Ações conforme o status - Cada ação em seu próprio formulário
                            if invoice["status"] == "draft":
                                with st.form(key=f"draft_actions_{invoice['id']}"):
                                    send_btn = st.form_submit_button("Marcar como Enviada")
                                    if send_btn:
                                        if put_api_data(f"billing/invoices/{invoice['id']}/status", {"status": "sent"}):
                                            st.success("Fatura marcada como enviada!")
                                            st.rerun()
                                
                                # Excluir (apenas rascunhos) - Isso precisa estar fora do formulário
                                show_delete_button("invoice", invoice["id"], "Excluir", f"Tem certeza que deseja excluir a fatura {invoice['invoice_number']}?")
                            
                            elif invoice["status"] == "sent":
                                with st.form(key=f"sent_actions_{invoice['id']}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        pay_btn = st.form_submit_button("Marcar como Paga")
                                    with col2:
                                        overdue_btn = st.form_submit_button("Marcar como Vencida")
                                    
                                    if pay_btn:
                                        payment_date = datetime.now().date().isoformat()
                                        if put_api_data(f"billing/invoices/{invoice['id']}/status", {"status": "paid", "payment_date": payment_date}):
                                            st.success("Fatura marcada como paga!")
                                            st.rerun()
                                    
                                    if overdue_btn:
                                        if put_api_data(f"billing/invoices/{invoice['id']}/status", {"status": "overdue"}):
                                            st.success("Fatura marcada como vencida!")
                                            st.rerun()
                            
                            # Qualquer fatura pode ser cancelada se não estiver já cancelada
                            if invoice["status"] != "canceled":
                                with st.form(key=f"cancel_action_{invoice['id']}"):
                                    cancel_btn = st.form_submit_button("Cancelar Fatura")
                                    if cancel_btn:
                                        if put_api_data(f"billing/invoices/{invoice['id']}/status", {"status": "canceled"}):
                                            st.success("Fatura cancelada!")
                                            st.rerun()
                        
                        # Itens da fatura
                        if invoice.get("items"):
                            st.subheader("Itens da Fatura")
                            items_df = pd.DataFrame(invoice["items"])
                            
                            # Formatar os valores para exibição
                            display_df = items_df.copy()
                            
                            # Formatar os valores para exibição
                            formatted_cols = ["unit_price", "subtotal", "tax_amount", "total"]
                            for col in formatted_cols:
                                if col in display_df.columns:
                                    display_df[col] = display_df[col].apply(lambda x: f"{x:.2f} €")
                            
                            if "tax_rate" in display_df.columns:
                                display_df["tax_rate"] = display_df["tax_rate"].apply(lambda x: f"{x:.0f}%")
                            
                            # Selecionar e renomear colunas para exibição
                            display_columns = ["description", "quantity", "unit_price", "tax_rate", "total"]
                            display_names = ["Descrição", "Qtd", "Preço Unit.", "IVA %", "Total"]
                            
                            st.table(display_df[display_columns].rename(columns=dict(zip(display_columns, display_names))))
            else:
                st.info("Nenhuma fatura encontrada com os filtros selecionados.")
        else:
            st.info("Nenhuma fatura cadastrada.")
    
    # TAB 2: SERVIÇOS
    with tab2:
        st.subheader("Gestão de Serviços")
        
        # Formulário para adicionar novo serviço
        with st.form("new_service_form"):
            st.write("Adicionar Novo Serviço")
            service_name = st.text_input("Nome do Serviço")
            service_description = st.text_area("Descrição")
            
            col1, col2 = st.columns(2)
            with col1:
                unit_price = st.number_input("Preço Unitário (€)", min_value=0.0, step=0.01)
            with col2:
                tax_rate = st.number_input("Taxa de IVA (%)", min_value=0.0, value=23.0, step=0.5)
            
            service_active = st.checkbox("Ativo", value=True)
            
            submit_service = st.form_submit_button("Adicionar Serviço")
            
            if submit_service and service_name and unit_price >= 0:
                service_data = {
                    "name": service_name,
                    "description": service_description,
                    "unit_price": unit_price,
                    "tax_rate": tax_rate,
                    "is_active": service_active
                }
                
                if post_api_data("billing/services", service_data):
                    st.success(f"Serviço '{service_name}' adicionado com sucesso!")
                    st.rerun()
        
        # Lista de serviços existentes
        services = get_api_data("billing/services") or []
        
        if services:
            st.subheader("Serviços Cadastrados")
            
            # Opção para mostrar inativos
            show_inactive = st.checkbox("Mostrar serviços inativos", value=False)
            
            # Filtrar serviços ativos/inativos
            if not show_inactive:
                services = [s for s in services if s.get("is_active", True)]
            
            for service in services:
                status = "Ativo" if service.get("is_active", True) else "Inativo"
                status_color = "green" if service.get("is_active", True) else "red"
                
                # Criar o título com formatação HTML
                service_title = f"{service['name']} - {service['unit_price']}€ - {status}"
                
                # Usar o expander sem o parâmetro unsafe_allow_html
                with st.expander(service_title, expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Nome:** {service['name']}")
                        st.write(f"**Preço Unitário:** {service['unit_price']}€")
                        st.write(f"**Taxa de IVA:** {service['tax_rate']}%")
                        
                        # Mostrar status com cor usando markdown
                        st.markdown(f"**Status:** <span style='color:{status_color};'>{status}</span>", unsafe_allow_html=True)
                        
                        if service.get("description"):
                            st.write(f"**Descrição:** {service['description']}")
                    
                    with col2:
                        # Formulário para o botão de edição
                        with st.form(key=f"edit_btn_form_{service['id']}", clear_on_submit=False):
                            edit_submitted = st.form_submit_button("Editar")
                            if edit_submitted:
                                st.session_state.edit_service = service
                                st.rerun()
                        
                        # Formulário para o botão de ativação/desativação
                        if service.get("is_active", True):
                            with st.form(key=f"deactivate_form_{service['id']}", clear_on_submit=False):
                                deactivate_submitted = st.form_submit_button("Desativar")
                                if deactivate_submitted:
                                    if put_api_data(f"billing/services/{service['id']}", {"is_active": False}):
                                        st.success(f"Serviço '{service['name']}' desativado!")
                                        st.rerun()
                        else:
                            with st.form(key=f"activate_form_{service['id']}", clear_on_submit=False):
                                activate_submitted = st.form_submit_button("Ativar")
                                if activate_submitted:
                                    if put_api_data(f"billing/services/{service['id']}", {"is_active": True}):
                                        st.success(f"Serviço '{service['name']}' ativado!")
                                        st.rerun()
            
            # Formulário de edição
            if hasattr(st.session_state, "edit_service"):
                service = st.session_state.edit_service
                
                with st.form(f"edit_service_{service['id']}"):
                    st.subheader(f"Editar Serviço: {service['name']}")
                    
                    new_name = st.text_input("Nome do Serviço", value=service['name'])
                    new_description = st.text_area("Descrição", value=service.get('description', ''))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        new_price = st.number_input("Preço Unitário (€)", min_value=0.0, value=service['unit_price'], step=0.01)
                    with col2:
                        new_tax_rate = st.number_input("Taxa de IVA (%)", min_value=0.0, value=service.get('tax_rate', 23.0), step=0.5)
                    
                    new_active = st.checkbox("Ativo", value=service.get('is_active', True))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_button = st.form_submit_button("Atualizar")
                    with col2:
                        cancel_button = st.form_submit_button("Cancelar")
                    
                    if update_button and new_name and new_price >= 0:
                        update_data = {
                            "name": new_name,
                            "description": new_description,
                            "unit_price": new_price,
                            "tax_rate": new_tax_rate,
                            "is_active": new_active
                        }
                        
                        if put_api_data(f"billing/services/{service['id']}", update_data):
                            st.success(f"Serviço '{new_name}' atualizado com sucesso!")
                            del st.session_state.edit_service
                            st.rerun()
                    
                    if cancel_button:
                        del st.session_state.edit_service
                        st.rerun()
        else:
            st.info("Nenhum serviço cadastrado. Adicione um serviço para começar.")
    
    # TAB 3: RELATÓRIOS
    with tab3:
        st.subheader("Relatórios de Faturação")
        
        # Filtros para relatórios
        col1, col2 = st.columns(2)
        with col1:
            report_period = st.selectbox(
                "Período",
                ["Este ano", "Último ano", "Este mês", "Último mês", "Personalizado"],
                key="report_period"
            )
        with col2:
            if is_admin():
                companies = get_api_data("companies") or []
                report_company_options = ["Todas"] + [c["name"] for c in companies]
                report_company = st.selectbox(
                    "Empresa",
                    report_company_options,
                    key="report_company"
                )
        
        # Datas personalizadas
        if report_period == "Personalizado":
            col1, col2 = st.columns(2)
            with col1:
                report_start_date = st.date_input("Data Inicial", value=datetime.now().date() - timedelta(days=365))
            with col2:
                report_end_date = st.date_input("Data Final", value=datetime.now().date())
        
        # Buscar faturas para relatório
        invoices = get_api_data("billing/invoices") or []
        
        if invoices:
            # Filtrar por período
            today = datetime.now().date()
            if report_period == "Este ano":
                year_start = datetime(today.year, 1, 1).date()
                filtered_invoices = [
                    inv for inv in invoices 
                    if datetime.strptime(inv["issue_date"], "%Y-%m-%d").date() >= year_start
                ]
            elif report_period == "Último ano":
                last_year_start = datetime(today.year - 1, 1, 1).date()
                last_year_end = datetime(today.year - 1, 12, 31).date()
                filtered_invoices = [
                    inv for inv in invoices 
                    if last_year_start <= datetime.strptime(inv["issue_date"], "%Y-%m-%d").date() <= last_year_end
                ]
            elif report_period == "Este mês":
                month_start = datetime(today.year, today.month, 1).date()
                filtered_invoices = [
                    inv for inv in invoices 
                    if datetime.strptime(inv["issue_date"], "%Y-%m-%d").date() >= month_start
                ]
            elif report_period == "Último mês":
                last_month = today.month - 1 if today.month > 1 else 12
                last_month_year = today.year if today.month > 1 else today.year - 1
                month_start = datetime(last_month_year, last_month, 1).date()
                if last_month == 12:
                    month_end = datetime(last_month_year + 1, 1, 1).date() - timedelta(days=1)
                else:
                    month_end = datetime(last_month_year, last_month + 1, 1).date() - timedelta(days=1)
                
                filtered_invoices = [
                    inv for inv in invoices 
                    if month_start <= datetime.strptime(inv["issue_date"], "%Y-%m-%d").date() <= month_end
                ]
            elif report_period == "Personalizado":
                filtered_invoices = [
                    inv for inv in invoices 
                    if report_start_date <= datetime.strptime(inv["issue_date"], "%Y-%m-%d").date() <= report_end_date
                ]
            
            # Filtrar por empresa se necessário
            if is_admin() and report_company != "Todas":
                company_id = next((c["id"] for c in companies if c["name"] == report_company), None)
                if company_id:
                    filtered_invoices = [inv for inv in filtered_invoices if inv["company_id"] == company_id]
            
            # Adicionar nomes de empresas
            for inv in filtered_invoices:
                company = next((c for c in companies if c["id"] == inv["company_id"]), None)
                inv["company_name"] = company["name"] if company else "Desconhecida"
            
            # Métricas gerais
            if filtered_invoices:
                # Totais
                # Totais
                total_invoiced = sum(inv["total"] for inv in filtered_invoices)
                total_paid = sum(inv["total"] for inv in filtered_invoices if inv["status"] == "paid")
                total_pending = sum(inv["total"] for inv in filtered_invoices if inv["status"] in ["draft", "sent"])
                total_overdue = sum(inv["total"] for inv in filtered_invoices if inv["status"] == "overdue")
                
                # Contadores
                count_total = len(filtered_invoices)
                count_paid = len([inv for inv in filtered_invoices if inv["status"] == "paid"])
                count_pending = len([inv for inv in filtered_invoices if inv["status"] in ["draft", "sent"]])
                count_overdue = len([inv for inv in filtered_invoices if inv["status"] == "overdue"])
                
                # Exibir métricas
                st.subheader("Resumo Financeiro")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Faturado", f"{total_invoiced:.2f} €")
                with col2:
                    st.metric("Total Pago", f"{total_paid:.2f} €")
                with col3:
                    st.metric("Pendente", f"{total_pending:.2f} €")
                with col4:
                    st.metric("Vencido", f"{total_overdue:.2f} €")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Nº Faturas", count_total)
                with col2:
                    st.metric("Faturas Pagas", count_paid)
                with col3:
                    st.metric("Faturas Pendentes", count_pending)
                with col4:
                    st.metric("Faturas Vencidas", count_overdue)
                
                # Gráficos
                st.subheader("Análise Gráfica")
                
                # Preparar dados para gráficos
                # Status breakdown
                status_counts = {
                    "Rascunho": len([inv for inv in filtered_invoices if inv["status"] == "draft"]),
                    "Enviada": len([inv for inv in filtered_invoices if inv["status"] == "sent"]),
                    "Paga": len([inv for inv in filtered_invoices if inv["status"] == "paid"]),
                    "Vencida": len([inv for inv in filtered_invoices if inv["status"] == "overdue"]),
                    "Cancelada": len([inv for inv in filtered_invoices if inv["status"] == "canceled"])
                }
                
                status_df = pd.DataFrame({
                    'Status': list(status_counts.keys()),
                    'Quantidade': list(status_counts.values())
                })
                
                # Gráfico de pizza para status
                fig_status = px.pie(
                    status_df, 
                    values='Quantidade', 
                    names='Status', 
                    title='Distribuição de Faturas por Status',
                    color='Status',
                    color_discrete_map={
                        'Rascunho': 'gray',
                        'Enviada': 'blue',
                        'Paga': 'green',
                        'Vencida': 'red',
                        'Cancelada': 'orange'
                    }
                )
                st.plotly_chart(fig_status)
                
                # Dados para gráfico por empresa
                if is_admin():
                    company_totals = {}
                    for inv in filtered_invoices:
                        company_name = inv.get("company_name", "Desconhecida")
                        if company_name not in company_totals:
                            company_totals[company_name] = 0
                        company_totals[company_name] += inv["total"]
                    
                    company_df = pd.DataFrame({
                        'Empresa': list(company_totals.keys()),
                        'Total': list(company_totals.values())
                    })
                    
                    # Ordenar por total
                    company_df = company_df.sort_values('Total', ascending=False)
                    
                    # Gráfico de barras por empresa
                    fig_company = px.bar(
                        company_df,
                        x='Empresa',
                        y='Total',
                        title='Faturação por Empresa',
                        color='Empresa',
                        labels={'Total': 'Total (€)'}
                    )
                    st.plotly_chart(fig_company)
                
                # Dados para gráfico mensal
                monthly_totals = {}
                for inv in filtered_invoices:
                    date = datetime.strptime(inv["issue_date"], "%Y-%m-%d")
                    month_key = f"{date.year}-{date.month:02d}"
                    month_name = f"{date.strftime('%b')}/{date.year}"
                    
                    if month_name not in monthly_totals:
                        monthly_totals[month_name] = 0
                    monthly_totals[month_name] += inv["total"]
                
                # Ordenar por mês
                sorted_months = sorted(monthly_totals.keys(), key=lambda x: datetime.strptime(x.split('/')[0], '%b').month + int(x.split('/')[1])*12)
                monthly_df = pd.DataFrame({
                    'Mês': sorted_months,
                    'Total': [monthly_totals[month] for month in sorted_months]
                })
                
                # Gráfico de linha para evolução mensal
                fig_monthly = px.line(
                    monthly_df,
                    x='Mês',
                    y='Total',
                    title='Evolução Mensal da Faturação',
                    markers=True,
                    labels={'Total': 'Total (€)'}
                )
                st.plotly_chart(fig_monthly)
                
                # Tabela detalhada
                st.subheader("Detalhamento de Faturas")
                
                # Converter para DataFrame para facilitar manipulação
                invoices_df = pd.DataFrame(filtered_invoices)
                
                # Colunas a exibir
                display_cols = ['invoice_number', 'company_name', 'issue_date', 'due_date', 'status', 'total']
                display_names = ['Nº Fatura', 'Empresa', 'Data Emissão', 'Vencimento', 'Status', 'Total (€)']
                
                # Se houver data de pagamento, incluir
                if 'payment_date' in invoices_df.columns:
                    display_cols.append('payment_date')
                    display_names.append('Data Pagamento')
                
                # Formatar o status
                if 'status' in invoices_df.columns:
                    invoices_df['status'] = invoices_df['status'].apply(lambda x: INVOICE_STATUS_DISPLAY.get(x, x))
                
                # Formatar valores monetários
                if 'total' in invoices_df.columns:
                    invoices_df['total'] = invoices_df['total'].apply(lambda x: f"{x:.2f} €")
                
                # Exibir tabela
                st.dataframe(invoices_df[display_cols].rename(columns=dict(zip(display_cols, display_names))))
                
                # Exportação
                st.subheader("Exportar Dados")
                
                # Opções de exportação
                export_format = st.radio("Formato de exportação:", ["CSV", "Excel", "PDF"])
                
                if st.button("Exportar Relatório"):
                    if export_format == "CSV":
                        # Gerar CSV
                        csv_data = invoices_df[display_cols].to_csv(index=False)
                        
                        # Link para download
                        b64 = base64.b64encode(csv_data.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="relatorio_faturacao.csv">Baixar arquivo CSV</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    elif export_format == "Excel":
                        # Gerar Excel
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            invoices_df[display_cols].to_excel(writer, index=False, sheet_name='Faturas')
                        
                        # Link para download
                        b64 = base64.b64encode(output.getvalue()).decode()
                        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="relatorio_faturacao.xlsx">Baixar arquivo Excel</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    elif export_format == "PDF":
                        # PDF mais elaborado com relatório completo
                        buffer = io.BytesIO()
                        
                        # Criar o documento PDF
                        doc = SimpleDocTemplate(
                            buffer,
                            pagesize=A4,
                            rightMargin=72,
                            leftMargin=72,
                            topMargin=72,
                            bottomMargin=72
                        )
                        
                        # Estilos para o PDF
                        styles = getSampleStyleSheet()
                        styles.add(ParagraphStyle(name='Center', alignment=1))
                        
                        # Lista para armazenar o conteúdo do PDF
                        elements = []
                        
                        # Título do relatório
                        title_text = "Relatório de Faturação"
                        period_text = ""
                        
                        if report_period == "Este ano":
                            period_text = f"Ano: {today.year}"
                        elif report_period == "Último ano":
                            period_text = f"Ano: {today.year - 1}"
                        elif report_period == "Este mês":
                            period_text = f"Mês: {today.strftime('%B/%Y')}"
                        elif report_period == "Último mês":
                            last_month_date = today.replace(day=1) - timedelta(days=1)
                            period_text = f"Mês: {last_month_date.strftime('%B/%Y')}"
                        elif report_period == "Personalizado":
                            period_text = f"Período: {report_start_date.strftime('%d/%m/%Y')} a {report_end_date.strftime('%d/%m/%Y')}"
                        
                        elements.append(Paragraph(title_text, styles['Heading1']))
                        elements.append(Paragraph(period_text, styles['Heading2']))
                        elements.append(Spacer(1, 20))
                        
                        # Resumo financeiro
                        elements.append(Paragraph("Resumo Financeiro", styles['Heading2']))
                        
                        financial_data = [
                            ["Métrica", "Valor"],
                            ["Total Faturado", f"{total_invoiced:.2f} €"],
                            ["Total Pago", f"{total_paid:.2f} €"],
                            ["Pendente", f"{total_pending:.2f} €"],
                            ["Vencido", f"{total_overdue:.2f} €"],
                            ["Nº Faturas", str(count_total)],
                            ["Faturas Pagas", str(count_paid)],
                            ["Faturas Pendentes", str(count_pending)],
                            ["Faturas Vencidas", str(count_overdue)]
                        ]
                        
                        financial_table = Table(financial_data, colWidths=[200, 100])
                        financial_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ]))
                        elements.append(financial_table)
                        elements.append(Spacer(1, 20))
                        
                        # Lista detalhada de faturas
                        elements.append(Paragraph("Detalhamento de Faturas", styles['Heading2']))
                        
                        # Dados da tabela de faturas
                        invoice_data = [display_names]  # Cabeçalho
                        
                        # Adicionar linhas de faturas (limitado para não sobrecarregar o PDF)
                        for _, row in invoices_df[display_cols].head(100).iterrows():
                            invoice_data.append([str(val) for val in row.values])
                        
                        # Criar tabela de faturas
                        invoice_table = Table(invoice_data, colWidths=[60, 80, 60, 60, 60, 60, 60])
                        invoice_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ]))
                        elements.append(invoice_table)
                        
                        # Data do relatório
                        elements.append(Spacer(1, 20))
                        elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
                        
                        # Construir o PDF
                        doc.build(elements)
                        
                        # Link para download
                        pdf_bytes = buffer.getvalue()
                        b64 = base64.b64encode(pdf_bytes).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_faturacao.pdf">Baixar Relatório PDF</a>'
                        st.markdown(href, unsafe_allow_html=True)
            else:
                st.info("Nenhuma fatura encontrada para o período selecionado.")
        else:
            st.info("Nenhuma fatura cadastrada para gerar relatórios.")

def add_to_menu():
    """Função para adicionar o módulo de faturação ao menu principal"""
    return True