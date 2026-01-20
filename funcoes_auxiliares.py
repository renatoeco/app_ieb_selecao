import streamlit as st
from pymongo import MongoClient
# import datetime
# import pandas as pd
# import io
from email.utils import formataddr

# Google Drive API
# from google.oauth2.service_account import Credentials
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaIoBaseUpload

# Envio de e-mail
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText







@st.cache_resource
def conectar_mongo_ieb_selecao():
    # CONEXÃO LOCAL
    cliente = MongoClient(st.secrets["senhas"]["senha_mongo_ieb_selecao"])
    db_ieb_selecao = cliente["ieb_selecao"] 
    return db_ieb_selecao







# ###########################################################################################

def enviar_email(
    corpo_html: str,
    destinatarios: list[str],
    assunto: str,
    nome_remetente: str = "IEB - Seleção de Projetos"
):
    """
    Envia e-mail em HTML usando configurações do st.secrets
    """

    smtp_server = st.secrets["senhas"]["smtp_server"]
    port = st.secrets["senhas"]["port"]
    endereco_email = st.secrets["senhas"]["endereco_email"]
    senha_email = st.secrets["senhas"]["senha_email"]

    msg = MIMEMultipart()
    msg["From"] = formataddr((nome_remetente, endereco_email))
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = assunto

    msg.attach(MIMEText(corpo_html, "html"))

    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(endereco_email, senha_email)
            server.send_message(msg)
        return True

    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False
