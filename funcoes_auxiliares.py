import streamlit as st
from pymongo import MongoClient
import re

from email.utils import formataddr


# Envio de e-mail
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr


import st_yled
from uuid import uuid4




def extrair_anexos_gmail(payload):
    """Identifica os anexos presentes na estrutura de uma mensagem Gmail."""

    anexos = []

    def percorrer_partes(parte):
        nome = parte.get("filename", "")
        corpo = parte.get("body", {})
        attachment_id = corpo.get("attachmentId")

        # Registra arquivos que possuem identificador de anexo no Gmail.
        if nome and attachment_id:
            anexos.append({
                "nome": nome,
                "mime_type": parte.get("mimeType", "application/octet-stream"),
                "attachment_id": attachment_id,
                "tamanho": corpo.get("size", 0)
            })

        # Percorre também as partes internas de mensagens multipart.
        for subparte in parte.get("parts", []):
            percorrer_partes(subparte)

    percorrer_partes(payload)

    return anexos





def recuperar_anexo_gmail(message_id, attachment_id):
    """Recupera o conteúdo de um anexo diretamente da API Gmail."""

    import base64

    try:
        gmail = conectar_gmail()

        resposta = gmail.users().messages().attachments().get(
            userId="me",
            messageId=message_id,
            id=attachment_id
        ).execute()

        dados = resposta.get("data", "")

        # Decodifica o conteúdo codificado em Base64 URL-safe.
        dados += "=" * (-len(dados) % 4)
        arquivo = base64.urlsafe_b64decode(dados)

        return {
            "sucesso": True,
            "arquivo": arquivo,
            "erro": None
        }

    except Exception as erro:
        return {
            "sucesso": False,
            "arquivo": None,
            "erro": str(erro)
        }






def remover_historico_resposta(texto):
    """Remove o histórico de mensagens anteriores de uma resposta."""

    import re

    linhas = texto.splitlines()
    linhas_filtradas = []

    for linha in linhas:

        linha_limpa = linha.strip()

        # Identifica os separadores mais comuns de mensagens citadas.
        if re.match(
            r"^(Em .+ escreveu:|On .+ wrote:)$",
            linha_limpa,
            flags=re.IGNORECASE
        ):
            break

        if linha_limpa.startswith("-----Mensagem original-----"):
            break

        if linha_limpa.startswith("---------- Forwarded message"):
            break

        linhas_filtradas.append(linha)

    return "\n".join(linhas_filtradas).strip()









def sincronizar_conversas_gmail(projeto_id):
    """Atualiza os identificadores das mensagens das conversas registradas."""

    try:
        # Recupera as conversas já registradas no projeto.
        db_ieb_selecao = conectar_mongo_ieb_selecao()
        col_projetos = db_ieb_selecao["projetos"]

        projeto = col_projetos.find_one(
            {"_id": projeto_id},
            {"conversas": 1}
        )

        if not projeto:
            return {
                "sucesso": False,
                "conversas_consultadas": 0,
                "mensagens_novas": 0,
                "erros": ["Projeto não encontrado no MongoDB."]
            }

        conversas_registradas = projeto.get("conversas", [])

        if not conversas_registradas:
            return {
                "sucesso": True,
                "conversas_consultadas": 0,
                "mensagens_novas": 0,
                "erros": []
            }

        gmail = conectar_gmail()

        conversas_consultadas = 0
        total_mensagens_novas = 0
        erros = []

        # Consulta exclusivamente as conversas já registradas.
        for conversa in conversas_registradas:

            thread_id = conversa.get("gmail_thread_id")

            if not thread_id:
                continue

            try:
                thread = gmail.users().threads().get(
                    userId="me",
                    id=thread_id,
                    format="minimal"
                ).execute()

                conversas_consultadas += 1

                # Identifica as mensagens já armazenadas no MongoDB.
                ids_registrados = set(
                    conversa.get("gmail_message_ids", [])
                )

                # Obtém os identificadores atuais da conversa no Gmail.
                ids_gmail = {
                    mensagem["id"]
                    for mensagem in thread.get("messages", [])
                    if mensagem.get("id")
                }

                # Mantém somente os identificadores ainda não registrados.
                ids_novos = ids_gmail - ids_registrados

                if ids_novos:
                    resultado = col_projetos.update_one(
                        {
                            "_id": projeto_id,
                            "conversas.gmail_thread_id": thread_id
                        },
                        {
                            "$addToSet": {
                                "conversas.$.gmail_message_ids": {
                                    "$each": list(ids_novos)
                                }
                            }
                        }
                    )

                    if resultado.matched_count:
                        total_mensagens_novas += len(ids_novos)
                    else:
                        erros.append(
                            f"Não foi possível atualizar a conversa {thread_id}."
                        )

            except Exception as erro_thread:
                erros.append(
                    f"Erro na conversa {thread_id}: {str(erro_thread)}"
                )

        return {
            "sucesso": len(erros) == 0,
            "conversas_consultadas": conversas_consultadas,
            "mensagens_novas": total_mensagens_novas,
            "erros": erros
        }

    except Exception as erro:
        return {
            "sucesso": False,
            "conversas_consultadas": 0,
            "mensagens_novas": 0,
            "erros": [str(erro)]
        }







def enviar_email_gmail(projeto_id, destinatario, assunto, mensagem):
    """Envia um e-mail pelo Gmail e registra os identificadores no projeto, usando Gmail API, para o chat de mensagens do projeto."""

    import base64
    from email.mime.text import MIMEText

    try:
        # Obtém o serviço autenticado do Gmail.
        gmail = conectar_gmail()

        # Monta a mensagem no formato aceito pela API Gmail.
        email = MIMEText(mensagem, "html", "utf-8")
        email["To"] = destinatario
        email["Subject"] = assunto

        mensagem_codificada = base64.urlsafe_b64encode(
            email.as_bytes()
        ).decode("utf-8")

        # Envia a mensagem pela conta institucional.
        resposta = gmail.users().messages().send(
            userId="me",
            body={"raw": mensagem_codificada}
        ).execute()

        thread_id = resposta.get("threadId")
        message_id = resposta.get("id")

        if not thread_id or not message_id:
            return {
                "sucesso": False,
                "enviado": True,
                "registrado": False,
                "erro": "O Gmail não retornou os identificadores esperados."
            }

    except Exception as erro:
        return {
            "sucesso": False,
            "enviado": False,
            "registrado": False,
            "erro": str(erro)
        }

    try:
        # Registra somente os identificadores da conversa no projeto.
        db_ieb_selecao = conectar_mongo_ieb_selecao()
        col_projetos = db_ieb_selecao["projetos"]

        resultado = col_projetos.update_one(
            {"_id": projeto_id},
            {
                "$push": {
                    "conversas": {
                        "gmail_thread_id": thread_id,
                        "gmail_message_ids": [message_id]
                    }
                }
            }
        )

        if resultado.matched_count == 0:
            return {
                "sucesso": False,
                "enviado": True,
                "registrado": False,
                "erro": "E-mail enviado, mas o projeto não foi encontrado no MongoDB."
            }

        return {
            "sucesso": True,
            "enviado": True,
            "registrado": True,
            "gmail_thread_id": thread_id,
            "gmail_message_id": message_id
        }

    except Exception as erro:
        return {
            "sucesso": False,
            "enviado": True,
            "registrado": False,
            "gmail_thread_id": thread_id,
            "gmail_message_id": message_id,
            "erro": str(erro)
        }





def consultar_conversas_gmail(projeto_id):
    """Consulta no Gmail as conversas registradas no documento do projeto."""

    import base64

    from email.utils import parsedate_to_datetime

    def extrair_corpo(payload):
        """Extrai o conteúdo textual de uma mensagem, sem processar anexos."""

        mime_type = payload.get("mimeType", "")
        body = payload.get("body", {})
        dados = body.get("data")

        if dados and mime_type in ("text/plain", "text/html"):
            conteudo = base64.urlsafe_b64decode(dados).decode(
                "utf-8",
                errors="replace"
            )
            return mime_type, conteudo

        partes = payload.get("parts", [])

        # Prioriza conteúdo em texto simples.
        for parte in partes:
            if parte.get("mimeType") == "text/plain":
                resultado = extrair_corpo(parte)
                if resultado:
                    return resultado

        # Utiliza HTML quando não houver conteúdo em texto simples.
        for parte in partes:
            if parte.get("mimeType") == "text/html":
                resultado = extrair_corpo(parte)
                if resultado:
                    return resultado

        # Percorre estruturas multipart aninhadas.
        for parte in partes:
            if parte.get("mimeType", "").startswith("multipart/"):
                resultado = extrair_corpo(parte)
                if resultado:
                    return resultado

        return None, ""

    try:
        # Recupera os identificadores das conversas no MongoDB.
        db_ieb_selecao = conectar_mongo_ieb_selecao()
        col_projetos = db_ieb_selecao["projetos"]

        projeto = col_projetos.find_one(
            {"_id": projeto_id},
            {"conversas": 1}
        )

        if not projeto:
            return {
                "sucesso": False,
                "conversas": [],
                "erro": "Projeto não encontrado no MongoDB."
            }

        conversas_registradas = projeto.get("conversas", [])

        if not conversas_registradas:
            return {
                "sucesso": True,
                "conversas": [],
                "erro": None
            }

        gmail = conectar_gmail()
        conversas = []

        # Consulta exclusivamente as conversas previamente registradas.
        for conversa_registrada in conversas_registradas:

            thread_id = conversa_registrada.get("gmail_thread_id")

            if not thread_id:
                continue

            thread = gmail.users().threads().get(
                userId="me",
                id=thread_id,
                format="full"
            ).execute()

            mensagens = []

            for mensagem in thread.get("messages", []):

                payload = mensagem.get("payload", {})
                headers = {
                    item["name"].lower(): item["value"]
                    for item in payload.get("headers", [])
                }

                mime_type, corpo = extrair_corpo(payload)

                data_mensagem = mensagem.get("internalDate")

                if data_mensagem:
                    from datetime import datetime, timezone

                    data_mensagem = datetime.fromtimestamp(
                        int(data_mensagem) / 1000,
                        tz=timezone.utc
                    ).astimezone().strftime("%d/%m/%Y %H:%M")
                else:
                    data_mensagem = headers.get("date", "")

                # Remove o histórico citado quando o conteúdo é texto simples.
                if mime_type == "text/plain":
                    corpo = remover_historico_resposta(corpo)


                mensagens.append({
                    "gmail_message_id": mensagem.get("id"),
                    "remetente": headers.get("from", ""),
                    "destinatario": headers.get("to", ""),
                    "assunto": headers.get("subject", ""),
                    "data_mensagem": data_mensagem,
                    "corpo": corpo,
                    "tipo_conteudo": mime_type,
                    "anexos": extrair_anexos_gmail(payload)
                })


            conversas.append({
                "gmail_thread_id": thread_id,
                "mensagens": mensagens
            })

        return {
            "sucesso": True,
            "conversas": conversas,
            "erro": None
        }

    except Exception as erro:
        return {
            "sucesso": False,
            "conversas": [],
            "erro": str(erro)
        }





@st.cache_resource
def conectar_gmail():
    """Estabelece a conexão autenticada com a API Gmail."""

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    configuracao = st.secrets["gmail"]

    escopos = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ]

    credenciais = Credentials(
        token=None,
        refresh_token=configuracao["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=configuracao["client_id"],
        client_secret=configuracao["client_secret"],
        scopes=escopos,
    )

    credenciais.refresh(Request())

    servico = build(
        "gmail",
        "v1",
        credentials=credenciais,
        cache_discovery=False,
    )

    return servico





def enviar_email(destinatarios: list[str], assunto: str, mensagem: str) -> bool:
    """
    Envia um e-mail em formato HTML utilizando as configurações SMTP
    armazenadas em st.secrets.

    Parâmetros:
        destinatarios (list[str]): Lista de endereços de e-mail destinatários.
        assunto (str): Assunto do e-mail.
        mensagem (str): Conteúdo do e-mail em HTML.

    Retorno:
        bool: True quando o envio é realizado com sucesso; False em caso de erro.
    """

    # Recupera as configurações de acesso ao servidor SMTP.
    smtp_server = st.secrets["senhas"]["smtp_server"]
    port = st.secrets["senhas"]["port"]
    endereco_email = st.secrets["senhas"]["endereco_email"]
    senha_email = st.secrets["senhas"]["senha_email"]

    # Prepara a mensagem de e-mail.
    msg = MIMEMultipart()
    msg["From"] = formataddr(("Sistema de Gestão de Projetos", endereco_email))
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = assunto

    msg.attach(MIMEText(mensagem, "html", "utf-8"))

    # Realiza o envio pelo servidor SMTP.
    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(endereco_email, senha_email)
            server.send_message(msg)

        return True

    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False










def renderizar_tag_css(tag):
    """Renderiza uma tag individual com sua cor cadastrada."""

    nome = tag.get("nome", "")
    cor = tag.get("cor", "#808080")

    st.markdown(
        f"""
        <span style="
            display: inline-block;
            background-color: {cor};
            color: #FFFFFF;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.875rem;
            font-weight: 500;
            white-space: nowrap;
        ">
            {nome}
        </span>
        """,
        unsafe_allow_html=True
    )





def configurar_containers_cinza():
    """
    Configura o arredondamento e o espaçamento interno dos containers.
    """

    st.markdown("""
        <style>
            /* Containers personalizados */
            div[data-testid="stVerticalBlock"][class*="st-key-container_cinza"] {
                border-radius: 0.5rem !important;
                padding: 1rem !important;
                box-sizing: border-box;
                box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.1);
                # box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.1), 0 6px 20px 0 rgba(0, 0, 0, 0.1);

            }
        </style>
    """, unsafe_allow_html=True)

def container_cinza(width="stretch"):
    """
    Cria um container com fundo personalizado, borda e largura configurável.
    """

    return st_yled.container(
        key=f"container_cinza_{uuid4().hex}",
        width=width,
        background_color="#fefefe",
        border_style="solid",
        border_color="#d0d0d0",
        border_width="1px",
    )




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
