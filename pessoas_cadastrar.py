import streamlit as st
from funcoes_auxiliares import conectar_mongo_ieb_selecao # Funções personalizadas
import pandas as pd
import re
import time
import uuid
import datetime
import smtplib
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_ieb_selecao()

# Importa coleções e cria dataframes
col_pessoas = db["pessoas"]
df_pessoas = pd.DataFrame(list(col_pessoas.find()))

# col_projetos = db["projetos"]
# df_projetos = pd.DataFrame(list(col_projetos.find()))




###########################################################################################################
# FUNÇÕES
###########################################################################################################

def gerar_codigo_aleatorio():
    """Gera um código numérico aleatório de 6 dígitos como string."""
    return f"{random.randint(0, 999999):06d}"


def enviar_email_convite(nome_completo, email_destino, codigo):
    """
    Envia um e-mail de convite com código de 6 dígitos usando credenciais do st.secrets.
    Retorna True se enviado, False se falhou.
    """
    try:
        smtp_server = st.secrets["senhas"]["smtp_server"]
        port = st.secrets["senhas"]["port"]
        endereco_email = st.secrets["senhas"]["endereco_email"]
        senha_email = st.secrets["senhas"]["senha_email"]

        msg = MIMEMultipart()
        msg['From'] = endereco_email
        msg['To'] = email_destino
        msg['Subject'] = "Convite para a Plataforma CEPF"

        corpo_html = f"""
        <p>Olá {nome_completo},</p>
        <p>Você foi convidado para utilizar a <strong>Plataforma de Gestão de Projetos do CEPF</strong>.</p>
        <p>Para realizar seu cadastro, acesse o link abaixo e clique no botão <strong>"Primeiro acesso"</strong>:</p>
        <p><a href="https://cepf-ieb.streamlit.app/">Acesse aqui a Plataforma</a></p>
        <p>Insira o seu <strong>e-mail</strong> e o <strong>código</strong> que te enviamos abaixo:</p>
        <h2>{codigo}</h2>
        <p>Se tiver alguma dúvida, entre em contato com a equipe do CEPF.</p>
        """
        msg.attach(MIMEText(corpo_html, 'html'))

        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(endereco_email, senha_email)
        server.send_message(msg)
        server.quit()

        # st.success(f":material/mail: E-mail de convite enviado para {email_destino}.")
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail para {email_destino}: {e}")
        return False





def df_index1(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    df2.index = range(1, len(df2) + 1)
    return df2


# Regex para validar e-mail
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
def validar_email(email):
    if not email:
        return False
    return bool(re.match(EMAIL_REGEX, str(email).strip()))






###########################################################################################################
# TRATAMENTO DE DADOS   
###########################################################################################################

tipo_usuario = st.session_state.get("tipo_usuario", "")



# projetos = df_projetos["codigo"].unique().tolist()

###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################


# Logo do sidebar
st.logo("images/logo_ieb.svg", size='large')

# Título da página
st.header("Convidar pessoa")


# opcao_cadastro = st.radio("", ["Convite individual", "Convite em massa"], key="opcao_cadastro", horizontal=True)

st.divider()





# --------------------------
# FORMULÁRIO DE CADASTRO
# --------------------------
# if opcao_cadastro == "Convite individual":

# --- campos do formulário que vamos controlar ---
CAMPOS_FORM_PESSOA = {
    "nome_completo_novo": "",
    "tipo_novo_usuario": "",
    # "tipo_beneficiario": "",   # string; só usado quando beneficiário
    "e_mail": "",
    "telefone": "",
    # "projetos_escolhidos": []  # multiselect espera lista
}

# --- limpeza no topo: se o flag estiver setado, reseta APENAS esses campos ---
if st.session_state.get("limpar_form_pessoa", False):
    for k, default in CAMPOS_FORM_PESSOA.items():
        st.session_state[k] = default
    # remove o flag para não ficar em loop
    st.session_state.pop("limpar_form_pessoa", None)
    # re-renderiza com campos zerados (não necessário sempre, mas seguro)
    st.rerun()



# --- Inputs com keys que coincidem com as chaves do session_state ---
nome_completo_novo = st.text_input("Nome completo", key="nome_completo_novo")

# depende do tipo de usuário logado (ex.: tipo_usuario vem do login)
if tipo_usuario == "equipe":
    tipo_novo_usuario = st.selectbox(
        "Tipo de usuário", ["", "avaliador", "visitante"], key="tipo_novo_usuario"
    )
elif tipo_usuario == "admin":
    tipo_novo_usuario = st.selectbox(
        "Tipo de usuário", ["", "admin", "equipe", "avaliador", "visitante"], key="tipo_novo_usuario"
    )

# # mostra apenas se selecionado beneficiário
# if st.session_state.get("tipo_novo_usuario") == "beneficiario":
#     tipo_beneficiario = st.selectbox(
#         "Tipo de beneficiário", ["", "técnico", "financeiro"], key="tipo_beneficiario"
#     )
# else:
#     # garante que o key exista (útil para limpeza/validação)
#     if "tipo_beneficiario" not in st.session_state:
#         st.session_state["tipo_beneficiario"] = ""

e_mail = st.text_input("E-mail", key="e_mail")
e_mail = e_mail.strip()

telefone = st.text_input("Telefone", key="telefone")

# # Garante que a key exista com lista vazia caso ainda não exista
# if "projetos_escolhidos" not in st.session_state:
#     st.session_state["projetos_escolhidos"] = []

# # Agora cria o multiselect sem passar default
# projetos_escolhidos = st.multiselect(
#     "Projetos",
#     projetos,
#     key="projetos_escolhidos"
# )



st.write("")
submit_button = st.button("Salvar", icon=":material/save:", type="primary", width=150)



if submit_button:
    # 1) Validações
    if not st.session_state["nome_completo_novo"] or not st.session_state["tipo_novo_usuario"] \
    or not st.session_state["e_mail"] or not st.session_state["telefone"]:
        st.error(":material/error: Todos os campos obrigatórios devem ser preenchidos.")
        st.stop()

    # if st.session_state["tipo_novo_usuario"] == "beneficiario" and not st.session_state.get("tipo_beneficiario"):
    #     st.error(":material/error: O campo 'Tipo de beneficiário' é obrigatório para beneficiários.")
    #     st.stop()

    if not validar_email(st.session_state["e_mail"]):
        st.error(":material/error: E-mail inválido.")
        st.stop()

    if col_pessoas.find_one({"e_mail": st.session_state["e_mail"]}):
        st.error(f":material/error: O e-mail '{st.session_state['e_mail']}' já está cadastrado.")
        st.stop()

    # 2) Gera código de 6 dígitos
    codigo_6_digitos = gerar_codigo_aleatorio()

    # 3) Monta documento a inserir no MongoDB
    novo_doc = {
        "nome_completo": st.session_state["nome_completo_novo"],
        "tipo_usuario": st.session_state["tipo_novo_usuario"],
        "e_mail": st.session_state["e_mail"],
        "telefone": st.session_state["telefone"],
        "status": "convidado",
        # "projetos": st.session_state.get("projetos_escolhidos", []),
        "data_convite": datetime.datetime.now().strftime("%d/%m/%Y"),
        "senha": None,
        "codigo_convite": codigo_6_digitos
    }

    # if st.session_state["tipo_novo_usuario"] == "beneficiario":
    #     novo_doc["tipo_beneficiario"] = st.session_state.get("tipo_beneficiario")

    # 4) Inserir no banco
    col_pessoas.insert_one(novo_doc)

    with st.spinner("Cadastrando pessoa... aguarde..."):

        time.sleep(2)

        st.success("Pessoa cadastrada com sucesso no banco de dados!", icon=":material/check:")

        # 5) Envio do e-mail de convite
        enviado = enviar_email_convite(
            nome_completo=st.session_state["nome_completo_novo"],
            email_destino=st.session_state["e_mail"],
            codigo=codigo_6_digitos
        )



        # 6) Limpar campos do formulário e rerun
        st.session_state["limpar_form_pessoa"] = True
        time.sleep(6)
        st.rerun()




