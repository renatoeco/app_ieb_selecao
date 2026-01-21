import streamlit as st
import time
from datetime import datetime, date
from funcoes_auxiliares import conectar_mongo_ieb_selecao

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta ao MongoDB usando a função auxiliar
db = conectar_mongo_ieb_selecao()

# Define a coleção de editais
colecao_editais = db.editais

###########################################################################################################
# INTERFACE PRINCIPAL
###########################################################################################################

st.logo("images/logo_ieb.svg", size='large')
st.header('Gerenciar Editais')

###########################################################################################################
# CONTAINER SUPERIOR COM SELECT E BOTÃO NOVO
###########################################################################################################

# Busca todos os editais cadastrados
editais = list(colecao_editais.find())

# Mapeia os editais para o selectbox
opcoes_editais = [""] + [
    f"{e['codigo_edital']} - {e['nome_edital']}" for e in editais
]

with st.container(horizontal=True, horizontal_alignment="distribute"):

    # Selectbox de escolha do edital
    edital_selecionado_label = st.selectbox(
        "Selecione o edital",
        options=opcoes_editais,
        index=0,
        width=600
    )

    # Botão para abrir o dialog de novo edital
    abrir_dialog = st.button(
        "Novo Edital",
        type="secondary",
        icon=":material/add:",
        width=200
    )


###########################################################################################################
# DIALOG PARA CADASTRO DE NOVO EDITAL
###########################################################################################################

@st.dialog("Cadastrar Novo Edital")
def dialog_novo_edital():
    with st.form("form_novo_edital_dialog", clear_on_submit=False):

        codigo_edital = st.text_input("Código do Edital")
        nome_edital = st.text_input("Nome do Edital")
        data_lancamento = st.date_input(
            "Data de Lançamento",
            value=date.today(),
            format="DD/MM/YYYY"
        )
        id_planilha_recebimento = st.text_input("ID da Planilha de Recebimento")

        botao_salvar = st.form_submit_button(
            "Salvar Edital",
            type="primary",
            icon=":material/save:"
        )

        if botao_salvar:
            if not codigo_edital or not nome_edital or not data_lancamento:
                st.error("Todos os campos são obrigatórios")
            else:
                documento = {
                    "codigo_edital": codigo_edital,
                    "nome_edital": nome_edital,
                    "data_lancamento": data_lancamento.strftime("%d/%m/%Y"),
                    "id_planilha_recebimento": id_planilha_recebimento
                }

                colecao_editais.insert_one(documento)

                st.success("Edital salvo com sucesso.", icon=":material/check:")
                time.sleep(3)
                st.rerun()

# Abre o dialog ao clicar no botão
if abrir_dialog:
    dialog_novo_edital()

###########################################################################################################
# ABAS PRINCIPAIS
###########################################################################################################

tabs = st.tabs(["Editar", "Estágios", "Distribuição", "Carregar"])

###########################################################################################################
# ABA EDITAR
###########################################################################################################
with tabs[0]:

    if edital_selecionado_label == "":
        st.caption("Selecione um edital para editar.")
    else:
        edital_selecionado = next(
            e for e in editais
            if f"{e['codigo_edital']} - {e['nome_edital']}" == edital_selecionado_label
        )

        data_edital = datetime.strptime(
            edital_selecionado["data_lancamento"], "%d/%m/%Y"
        ).date()

        with st.form("form_editar_edital", clear_on_submit=False):

            codigo_edital_edit = st.text_input(
                "Código do Edital",
                value=edital_selecionado["codigo_edital"]
            )

            nome_edital_edit = st.text_input(
                "Nome do Edital",
                value=edital_selecionado["nome_edital"]
            )

            data_lancamento_edit = st.date_input(
                "Data de Lançamento",
                value=data_edital,
                format="DD/MM/YYYY"
            )

            id_planilha_recebimento_edit = st.text_input(
                "ID da Planilha de Recebimento",
                value=edital_selecionado.get("id_planilha_recebimento", "")
            )

            botao_atualizar = st.form_submit_button(
                "Salvar Alterações",
                type="primary",
                icon=":material/save:"
            )

            if botao_atualizar:
                if not codigo_edital_edit or not nome_edital_edit or not data_lancamento_edit:
                    st.error("Todos os campos são obrigatórios")
                else:
                    colecao_editais.update_one(
                        {"_id": edital_selecionado["_id"]},
                        {"$set": {
                            "codigo_edital": codigo_edital_edit,
                            "nome_edital": nome_edital_edit,
                            "data_lancamento": data_lancamento_edit.strftime("%d/%m/%Y"),
                            "id_planilha_recebimento": id_planilha_recebimento_edit
                        }}
                    )

                    st.success(
                        "Edital atualizado com sucesso.",
                        icon=":material/check:"
                    )
                    time.sleep(3)
                    st.rerun()

###########################################################################################################
# ABA ESTÁGIOS
###########################################################################################################
with tabs[1]:
    st.caption("Conteúdo da aba Estágios")

###########################################################################################################
# ABA DISTRIBUIÇÃO
###########################################################################################################
with tabs[2]:
    st.caption("Conteúdo da aba Distribuição")

###########################################################################################################
# ABA CARREGAR
###########################################################################################################
with tabs[3]:
    st.caption("Conteúdo da aba Carregar")
