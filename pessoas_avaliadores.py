import streamlit as st
from funcoes_auxiliares import conectar_mongo_ieb_selecao  # Função personalizada para conectar ao MongoDB
import pandas as pd
from bson import ObjectId
import time

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_ieb_selecao()

# Importa coleções e cria dataframes

# Pessoas
col_pessoas = db["pessoas"]

# Projetos
col_projetos = db["projetos"]


###########################################################################################################
# TRATAMENTO DOS DADOS
###########################################################################################################

# Busca todos os documentos, mas exclui o campo "senha"
df_pessoas = pd.DataFrame(list(col_pessoas.find({}, {"senha": 0})))

# Converte ObjectId para string
df_pessoas["_id"] = df_pessoas["_id"].astype(str)

# Renomeia as colunas
df_pessoas = df_pessoas.rename(columns={
    "nome_completo": "Nome",
    "tipo_usuario": "Tipo de usuário",
    "e_mail": "E-mail",
    "telefone": "Telefone",
    "status": "Status",
})

# Ordena por Nome
df_pessoas = df_pessoas.sort_values(by="Nome")

# # Projetos
# df_projetos = pd.DataFrame(list(col_projetos.find()))
# # Converte objectId para string
# df_projetos['_id'] = df_projetos['_id'].astype(str)





###########################################################################################################
# Funções
###########################################################################################################


# Diálogo para editar uma pessoa
@st.dialog("Editar Pessoa", width="medium")
def editar_pessoa(_id: str):
    """Abre o diálogo para editar uma pessoa"""
    
    pessoa = col_pessoas.find_one({"_id": ObjectId(_id)})
    if not pessoa:
        st.error("Pessoa não encontrada.")
        return

    # Inputs básicos
    nome = st.text_input("Nome", value=pessoa.get("nome_completo", ""))
    email = st.text_input("E-mail", value=pessoa.get("e_mail", ""))
    telefone = st.text_input("Telefone", value=pessoa.get("telefone", ""))

    # Tipo de usuário
    tipo_usuario_raw = pessoa.get("tipo_usuario", "")
    tipo_usuario_default = tipo_usuario_raw.strip() if isinstance(tipo_usuario_raw, str) else ""

    tipo_usuario = st.selectbox(
        "Tipo de usuário",
        options=["admin", "equipe", "avaliador", "visitante"],
        index=["admin", "equipe", "avaliador", "visitante"].index(tipo_usuario_default)
        if tipo_usuario_default in ["admin", "equipe", "avaliador", "visitante"]
        else 0
    )


    # Status
    status = st.selectbox(
        "Status",
        options=["ativo", "inativo"],
        index=0 if pessoa.get("status", "ativo") == "ativo" else 1
    )


    st.write("")

    # Botão de salvar
    if st.button("Salvar alterações", icon=":material/save:"):
        # Documento base
        update_data = {
            "nome_completo": nome,
            "e_mail": email,
            "telefone": telefone,
            "tipo_usuario": tipo_usuario,
            "status": status,
        }


        # Atualiza o registro
        col_pessoas.update_one({"_id": ObjectId(_id)}, {"$set": update_data})

        st.success("Pessoa atualizada com sucesso!", icon=":material/check:")
        time.sleep(3)
        st.rerun()





###########################################################################################################
# INTERFACE
###########################################################################################################


# Logo do sidebar
st.logo("images/logo_ieb.svg", size='large')

st.header('Avaliadores(as)')

st.divider()


# Separando só os avaliadores
df_benef = df_pessoas[
    df_pessoas["Tipo de usuário"] == "avaliador"
]

st.write('')

dist_colunas = [3, 4, 3, 2, 3, 2, 1]

# Colunas
col1, col2, col3, col4, col5, col6, col7 = st.columns(dist_colunas)

# Cabeçalho da lista
col1.write('**Nome**')
# col2.write('**Projetos**')
col3.write('**E-mail**')
col4.write('**Telefone**')
col5.write('**Tipo de usuário**')
col6.write('**Status**')
col7.write('')

st.write('')

# Pra cada linha, criar colunas para os dados
for _, row in df_benef.iterrows():
    col1, col2, col3, col4, col5, col6, col7 = st.columns(dist_colunas)

    # NOME -----------------
    col1.write(row["Nome"])


    # E-MAIL -----------------

    col3.write(row["E-mail"])

    # TELEFONE -----------------
    col4.write(row["Telefone"])


    # TIPO DE USUÁRIO -----------------
    tipo_usuario = row.get("Tipo de usuário", "").strip()


    col5.write(tipo_usuario)


    # STATUS -----------------       
    col6.write(row["Status"])

    # BOTÃO DE EDITAR -----------------
    col7.button(":material/edit:", key=row["_id"], on_click=editar_pessoa, args=(row["_id"],))
