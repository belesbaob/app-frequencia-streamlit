import streamlit as st
from utils.database import USERS, setup_files
import os

# Configurações iniciais
st.set_page_config(
    page_title="Gestão de Frequência Escolar",
    layout="wide",
)

# Cria os arquivos de dados se eles não existirem
setup_files()

# Função para realizar o login
def check_login(username, password):
    if username in USERS and USERS[username]["password"] == password:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.session_state["role"] = USERS[username]["role"]
        st.success(f"Bem-vindo, {username}!")
    else:
        st.error("Usuário ou senha inválidos.")

# Tela de login
def login_page():
    st.title("Sistema de Gestão de Frequência")
    st.subheader("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        check_login(username, password)

# Função para logout
def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None
    st.rerun()

# Roteamento de páginas
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_page()
else:
    st.sidebar.title(f"Bem-vindo, {st.session_state['username']}!")
    st.sidebar.button("Logout", on_click=logout)

    # A navegação entre as páginas é feita automaticamente pelo Streamlit
    # através da pasta `pages/`.