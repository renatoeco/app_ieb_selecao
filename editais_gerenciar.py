import streamlit as st
import pandas as pd
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
# CRIAÇÃO DAS ABAS
###########################################################################################################

tab_novo, tab_gerenciar = st.tabs(["Novo Edital", "Gerenciar Editais"])

###########################################################################################################
# ABA: NOVO EDITAL
###########################################################################################################
with tab_novo:
    st.subheader("Cadastro de Novo Edital")

    # Formulário de cadastro
    with st.form("form_novo_edital", clear_on_submit=False):

        # Campos obrigatórios
        codigo_edital = st.text_input("Código do Edital")
        nome_edital = st.text_input("Nome do Edital")
        data_lancamento = st.date_input(
            "Data de Lançamento",
            value=date.today(),
            format="DD/MM/YYYY"
        )

        # Campo opcional
        id_planilha_recebimento = st.text_input(
            "ID da Planilha de Recebimento (opcional)"
        )

        # Botão de salvar
        botao_salvar = st.form_submit_button(
            "Salvar Edital",
            type="primary",
            icon=":material/save:"
        )

        # Validação e salvamento
        if botao_salvar:
            if not codigo_edital or not nome_edital or not data_lancamento:
                st.error("Todos os campos são obrigatórios")
            else:
                # Documento a ser salvo no MongoDB
                documento = {
                    "codigo_edital": codigo_edital,
                    "nome_edital": nome_edital,
                    "data_lancamento": data_lancamento.strftime("%d/%m/%Y"),
                    "id_planilha_recebimento": id_planilha_recebimento
                }

                # Insere o documento na coleção
                colecao_editais.insert_one(documento)

                st.success("Edital salvo com sucesso.", icon=":material/check:")
                time.sleep(3)
                st.rerun()

###########################################################################################################
# ABA: GERENCIAR EDITAIS
###########################################################################################################
with tab_gerenciar:
    st.subheader("Gerenciar Edital")

    # Busca todos os editais cadastrados
    editais = list(colecao_editais.find())

    # Se não houver editais, mostra mensagem informativa
    if not editais:
        st.info("Nenhum edital cadastrado.")
    else:
        # Cria a lista de opções do selectbox
        # A primeira opção é vazia e será selecionada por padrão
        opcoes = [""] + [
            f"{e['codigo_edital']} - {e['nome_edital']}" for e in editais
        ]

        # Selectbox com opção vazia como padrão
        edital_selecionado_label = st.selectbox(
            "Selecione o edital para gerenciar",
            options=opcoes,
            index=0
        )

        st.write('')

        # Só carrega o formulário se um edital for selecionado
        if edital_selecionado_label != "":

            # Recupera o edital selecionado
            edital_selecionado = next(
                e for e in editais
                if f"{e['codigo_edital']} - {e['nome_edital']}" == edital_selecionado_label
            )

            # Converte a data salva em string para date
            data_edital = datetime.strptime(
                edital_selecionado["data_lancamento"], "%d/%m/%Y"
            ).date()

            # Recupera o campo opcional (pode não existir)
            id_planilha_atual = edital_selecionado.get(
                "id_planilha_recebimento", ""
            )

            # Formulário de edição
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

                # Campo opcional pré-carregado
                id_planilha_recebimento_edit = st.text_input(
                    "ID da Planilha de Recebimento (opcional)",
                    value=id_planilha_atual
                )

                botao_atualizar = st.form_submit_button(
                    "Salvar Alterações",
                    type="primary",
                    icon=":material/save:"
                )

                # Validação e atualização
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
