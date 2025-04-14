# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import base64
import json
from datetime import datetime, timedelta
import plotly.express as px

API_URL = "http://127.0.0.1:8000"

def get_image_base64(image_path: str) -> str:
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Imagem n�o encontrada: {image_path}")
        return ""

# Configura��o do layout do Streamlit
st.set_page_config(page_title="FleetPilot",
                   layout="wide")

# Fun��es de API
def login_user(username, password):
    try:
        resp = requests.post(f"{API_URL}/auth/login", 
                           data={"username": username, "password": password})
        if resp.status_code == 200:
            data = resp.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["logged_in"] = True
            return True
    except requests.exceptions.ConnectionError:
        st.error("Erro de conex�o com a API. Verifique se o backend est� em execu��o.")
    except Exception as e:
        st.error(f"Erro ao fazer login: {str(e)}")
    return False

def get_api_data(endpoint):
    """Fun��o gen�rica para buscar dados da API"""
    if "token" not in st.session_state:
        return None
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.get(f"{API_URL}/{endpoint}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro ao obter dados: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro de comunica��o com a API: {str(e)}")
        return None

def post_api_data(endpoint, data):
    """Fun��o gen�rica para enviar dados para a API"""
    if "token" not in st.session_state:
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.post(f"{API_URL}/{endpoint}", 
                               headers=headers, 
                               json=data)
        if response.status_code in [200, 201]:
            return True
        else:
            st.error(f"Erro ao enviar dados: {response.status_code}")
            if response.text:
                st.error(response.text)
            return False
    except Exception as e:
        st.error(f"Erro de comunica��o com a API: {str(e)}")
        return False

# Inicializa��o de sess�o
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Tela de Login
if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>FleetPilot</h1>", unsafe_allow_html=True)
    
    logo_path = "frontend/images/logo.png"
    image_base64 = get_image_base64(logo_path)
    if image_base64:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center;">
                <img src="data:image/png;base64,{image_base64}" width="150" 
                     style="border-radius: 50%; border: 2px solid #ddd; 
                            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("<h4 style='text-align: center; color: gray;'>Gest�o Inteligente da Frota</h4>", unsafe_allow_html=True)

    # Form de login
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if login_user(username, password):
                st.success("Login realizado com sucesso!")
                st.experimental_rerun()
            else:
                st.error("Credenciais inv�lidas ou erro de conex�o.")
    st.stop()

# Menu da aplica��o (logado)
st.sidebar.image(logo_path, width=60)
st.sidebar.title("FleetPilot")
menu = st.sidebar.radio("Menu", 
                      ["Dashboard", "Empresas", "M�quinas", "Manuten��es", "Configura��es", "Sair"],
                      format_func=lambda x: f"?? {x}" if x == "Dashboard" 
                                 else f"?? {x}" if x == "Empresas"
                                 else f"?? {x}" if x == "M�quinas"
                                 else f"?? {x}" if x == "Manuten��es"
                                 else f"?? {x}" if x == "Configura��es"
                                 else f"?? {x}")

# Conte�do das p�ginas
if menu == "Dashboard":
    st.title("Dashboard da Frota")
    
    # M�tricas principais
    col1, col2, col3 = st.columns(3)
    
    # Buscar dados para m�tricas (em produ��o, use dados reais da API)
    maquinas = get_api_data("maquinas") or []
    manutencoes = get_api_data("manutencoes") or []
    
    # Calcular manutencoes pr�ximas (7 dias)
    hoje = datetime.now().date()
    proxima_semana = hoje + timedelta(days=7)
    manutencoes_proximas = [m for m in manutencoes 
                          if hoje <= datetime.strptime(m['data_prevista'], '%Y-%m-%d').date() <= proxima_semana]
    
    col1.metric("Total de M�quinas", len(maquinas))
    col2.metric("Manuten��es Pr�ximas", len(manutencoes_proximas))
    col3.metric("Empresas", "1")  # Em produ��o, use contagem real
    
    # Gr�fico de distribui��o de tipos de m�quinas
    if maquinas:
        tipos = {}
        for m in maquinas:
            tipo = m['tipo']
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        df_tipos = pd.DataFrame({
            'Tipo': list(tipos.keys()),
            'Quantidade': list(tipos.values())
        })
        
        fig = px.pie(df_tipos, values='Quantidade', names='Tipo', 
                   title='Distribui��o por Tipo de M�quina')
        st.plotly_chart(fig)
    
    # Tabela de manuten��es pr�ximas
    if manutencoes_proximas:
        st.subheader("Manuten��es Pr�ximas")
        df_manutencoes = pd.DataFrame(manutencoes_proximas)
        st.dataframe(df_manutencoes)
    else:
        st.info("N�o h� manuten��es agendadas para os pr�ximos 7 dias.")

elif menu == "Empresas":
    st.title("Gest�o de Empresas")
    
    # Formul�rio para adicionar empresa
    with st.form("nova_empresa"):
        st.subheader("Adicionar Nova Empresa")
        nome_empresa = st.text_input("Nome da Empresa")
        submitted = st.form_submit_button("Adicionar")
        
        if submitted and nome_empresa:
            if post_api_data("empresas", {"nome": nome_empresa}):
                st.success(f"Empresa '{nome_empresa}' adicionada com sucesso!")
    
    # Listagem de empresas existentes
    st.subheader("Empresas Cadastradas")
    empresas = get_api_data("empresas")
    
    if empresas:
        for empresa in empresas:
            st.write(f"**{empresa['nome']}** (ID: {empresa['id']})")
    else:
        st.info("Nenhuma empresa cadastrada.")

elif menu == "M�quinas":
    st.title("Gest�o de M�quinas")
    
    # Formul�rio para adicionar m�quina
    empresas = get_api_data("empresas") or []
    
    with st.form("nova_maquina"):
        st.subheader("Adicionar Nova M�quina")
        nome_maquina = st.text_input("Nome da M�quina")
        tipo_maquina = st.selectbox("Tipo", ["camiao", "fixa"])
        empresa_id = st.selectbox("Empresa", 
                                options=[e['id'] for e in empresas],
                                format_func=lambda x: next((e['nome'] for e in empresas if e['id'] == x), str(x)))
        
        submitted = st.form_submit_button("Adicionar")
        
        if submitted and nome_maquina and empresa_id:
            if post_api_data("maquinas", {
                "nome": nome_maquina,
                "tipo": tipo_maquina,
                "empresa_id": empresa_id
            }):
                st.success(f"M�quina '{nome_maquina}' adicionada com sucesso!")
    
    # Listagem de m�quinas existentes
    st.subheader("M�quinas Cadastradas")
    maquinas = get_api_data("maquinas")
    
    if maquinas:
        # Criar dataframe para melhor visualiza��o
        df_maquinas = pd.DataFrame(maquinas)
        
        # Adicionar nome da empresa
        df_maquinas['empresa_nome'] = df_maquinas['empresa_id'].apply(
            lambda x: next((e['nome'] for e in empresas if e['id'] == x), "Desconhecida")
        )
        
        st.dataframe(df_maquinas[['id', 'nome', 'tipo', 'empresa_nome']])
    else:
        st.info("Nenhuma m�quina cadastrada.")

elif menu == "Manuten��es":
    st.title("Agendamento de Manuten��es")
    
    # Buscar m�quinas para o formul�rio
    maquinas = get_api_data("maquinas") or []
    
    # Formul�rio para agendar manuten��o
    with st.form("nova_manutencao"):
        st.subheader("Agendar Nova Manuten��o")
        
        maquina_id = st.selectbox("M�quina", 
                               options=[m['id'] for m in maquinas],
                               format_func=lambda x: next((f"{m['nome']} ({m['tipo']})" 
                                                        for m in maquinas if m['id'] == x), str(x)))
        
        tipo_manutencao = st.selectbox("Tipo de Manuten��o", 
                                     ["Troca de �leo", "Revis�o Completa", "Filtros", "Pneus", "Outro"])
        
        if tipo_manutencao == "Outro":
            tipo_custom = st.text_input("Especifique o tipo de manuten��o")
            tipo_final = tipo_custom if tipo_custom else tipo_manutencao
        else:
            tipo_final = tipo_manutencao
            
        data_manutencao = st.date_input("Data Prevista", 
                                      min_value=datetime.now().date(),
                                      value=datetime.now().date() + timedelta(days=7))
        
        submitted = st.form_submit_button("Agendar")
        
        if submitted and maquina_id:
            if post_api_data("manutencoes", {
                "maquina_id": maquina_id,
                "tipo": tipo_final,
                "data_prevista": data_manutencao.isoformat()
            }):
                st.success(f"Manuten��o agendada com sucesso para {data_manutencao}!")
    
    # Listagem de manuten��es existentes
    st.subheader("Manuten��es Agendadas")
    manutencoes = get_api_data("manutencoes")
    
    if manutencoes:
        # Criar dataframe para melhor visualiza��o
        df_manutencoes = pd.DataFrame(manutencoes)
        
        # Adicionar nome da m�quina
        df_manutencoes['maquina_nome'] = df_manutencoes['maquina_id'].apply(
            lambda x: next((m['nome'] for m in maquinas if m['id'] == x), "Desconhecida")
        )
        
        # Ordenar por data
        df_manutencoes['data_prevista'] = pd.to_datetime(df_manutencoes['data_prevista'])
        df_ordenado = df_manutencoes.sort_values('data_prevista')
        
        # Destacar pr�ximas manuten��es
        hoje = datetime.now().date()
        
        # Fun��o para estilizar baseado na data
        def highlight_proximas(row):
            data = row['data_prevista'].date()
            if data <= hoje:
                return ['background-color: #ffcccc'] * len(row)  # Vermelho claro (atrasada)
            elif (data - hoje).days <= 7:
                return ['background-color: #ffffcc'] * len(row)  # Amarelo claro (pr�xima)
            else:
                return [''] * len(row)
                
        # Exibir com estilo
        st.dataframe(df_ordenado.style.apply(highlight_proximas, axis=1))
        
    else:
        st.info("Nenhuma manuten��o agendada.")

elif menu == "Configura��es":
    st.title("Configura��es do Sistema")
    
    st.subheader("Configura��es de Notifica��o")
    st.write("Configure os n�meros de telefone para receber alertas SMS sobre manuten��es.")
    
    telefone = st.text_input("N�mero de Telefone (com c�digo do pa�s)", value="351911234567")
    if st.button("Salvar Configura��es"):
        # Em produ��o, salvar na base de dados
        st.success("Configura��es salvas com sucesso!")
    
    st.subheader("Perfil da Empresa")
    nome_empresa = st.text_input("Nome da Empresa", value="Minha Empresa")
    email_contato = st.text_input("Email de Contato", value="contato@minhaempresa.com")
    
    if st.button("Atualizar Perfil"):
        # Em produ��o, salvar na base de dados
        st.success("Perfil atualizado com sucesso!")

elif menu == "Sair":
    # Limpar sess�o e fazer logout
    if st.button("Confirmar Logout"):
        st.session_state.clear()
        st.experimental_rerun()