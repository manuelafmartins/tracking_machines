# frontend.py
import streamlit as st
import requests
import base64

API_URL = "http://127.0.0.1:8000"

def get_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Configuração do layout do Streamlit
st.set_page_config(page_title="FleetPilot",
                   page_icon="frontend/images/logo_transparent.png",
                   layout="wide")

def login_user(username, password):
    resp = requests.post(f"{API_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    if resp.status_code == 200:
        data = resp.json()
        st.session_state["token"] = data["access_token"]
        st.session_state["logged_in"] = True
        return True
    return False


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>FILIPE DAVID FERREIRA</h1>", unsafe_allow_html=True)
    
    image_base64 = get_image_base64("frontend/images/logo.png")
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
    st.markdown("<h4 style='text-align: center; color: gray;'>Gestão Inteligente da Frota</h4>", unsafe_allow_html=True)

    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_user(username, password):
            st.success("Successfully logged in.")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

# Se chegou aqui, está logado:
st.sidebar.image("frontend/images/logo.png", width=60)
st.sidebar.markdown("### 🚚 FleetPilot")
menu = st.sidebar.radio("Navigation", ["🝠 Dashboard", "🚜 Machines", "🛠︝ Maintenance", "⚙︝ Settings", "🔓 Logout"])

headers = {"Authorization": f"Bearer {st.session_state['token']}"}

# --- Dashboard ---
if menu == "🝠 Dashboard":
    st.title("📊 Company Overview")
    st.markdown("Welcome to your company’s private dashboard.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Machines", "12")  # Exemplo fixo, trocar por valor real
    col2.metric("Upcoming Maintenances", "3")
    col3.metric("Alerts", "1")

# --- Machines ---
elif menu == "🚜 Machines":
    st.title("🚜 Manage Your Fleet")
    st.subheader("Register New Machine")

    name = st.text_input("Machine Name")
    type_ = st.selectbox("Machine Type", ["camiao", "fixa"])  # Ajuste para ficar igual ao seu enum
    if st.button("Register Machine"):
        r = requests.post(f"{API_URL}/maquinas/", headers=headers,
                          json={"nome": name, "tipo": type_, "empresa_id": 1})  # Ajuste "1" se for outro ID de empresa
        if r.status_code == 200 or r.status_code == 201:
            st.success("Machine registered successfully.")
        else:
            st.error("Error registering machine.")

    st.subheader("Existing Machines")
    lista = requests.get(f"{API_URL}/maquinas/", headers=headers)
    if lista.status_code == 200:
        for m in lista.json():
            st.markdown(f"- **{m['nome']}** ({m['tipo']})")
    else:
        st.error("Error fetching machines.")

# --- Maintenance ---
elif menu == "🛠︝ Maintenance":
    st.title("🛠︝ Maintenance Schedule")
    st.subheader("Upcoming Maintenance Tasks")

    manutencoes = requests.get(f"{API_URL}/manutencoes/", headers=headers)
    if manutencoes.status_code == 200:
        for m in manutencoes.json():
            st.write(f"{m['tipo']} scheduled for machine **{m['maquina_id']}** on **{m['data_prevista']}**")
    else:
        st.error("Error fetching maintenances.")

# --- Settings ---
elif menu == "⚙︝ Settings":
    st.title("⚙︝ Company Settings")
    st.info("Here you can edit your company profile, notification settings, and user access.")

# --- Logout ---
elif menu == "🔓 Logout":
    st.session_state.clear()
    st.success("You have been logged out.")
    st.experimental_rerun()
