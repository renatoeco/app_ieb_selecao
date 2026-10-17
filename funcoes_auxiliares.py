import streamlit as st
from pymongo import MongoClient
import re

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





def formatar_valor_brasileiro(valor):
    """
    Formata um valor numérico no padrão brasileiro, com duas casas decimais.
    """

    valor = float(valor or 0)

    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def converter_valor_brasileiro(valor_texto):
    """
    Converte um valor monetário no padrão brasileiro para float.
    Aceita valores como 1234,56 e 1.234,56.
    """

    valor_texto = valor_texto.strip()

    if not valor_texto:
        raise ValueError("Informe o valor do edital.")

    # Valida o padrão brasileiro, com até duas casas decimais
    padrao = r"^(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,2})?$"

    if not re.fullmatch(padrao, valor_texto):
        raise ValueError(
            "Informe um valor válido. Insira somente números."
        )

    valor = float(
        valor_texto.replace(".", "").replace(",", ".")
    )

    # Garante duas casas decimais na precisão monetária
    return round(valor, 2)







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
