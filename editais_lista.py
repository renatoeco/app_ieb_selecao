
import streamlit as st
from funcoes_auxiliares import (
    conectar_mongo_ieb_selecao,
    formatar_valor_brasileiro
)


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Estabelece a conexão com o banco de dados de seleção.
db = conectar_mongo_ieb_selecao()

colecao_editais = db["editais"]


###########################################################################################################
# FUNÇÕES AUXILIARES
###########################################################################################################

def renderizar_estagios(estagios):
    """Apresenta os nomes dos estágios cadastrados no edital."""

    if not estagios:
        st.caption("Nenhum estágio cadastrado.")
        return

    estagios_ordenados = sorted(
        estagios,
        key=lambda estagio: estagio.get("ordem_estagio", 0)
    )

    for estagio in estagios_ordenados:
        nome = estagio.get("nome_estagio", "Estágio sem nome")
        st.markdown(f"- {nome}")


def renderizar_tags(tags):
    """Apresenta as tags do edital com suas cores e descrições."""

    if not tags:
        st.caption("Nenhuma tag cadastrada.")
        return

    for tag in tags:
        nome = tag.get("nome", "")
        descricao = tag.get("descricao", "")
        cor = tag.get("cor", "#808080")

        with st.container(horizontal=True, horizontal_alignment="left", vertical_alignment="center"):

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

            st.caption(descricao)




###########################################################################################################
# INTERFACE
###########################################################################################################

# Apresenta a logo na barra lateral.
st.logo("images/logo_ieb.svg", size="large")

st.header("Editais")


###########################################################################################################
# LISTAGEM DE EDITAIS
###########################################################################################################

# Recupera os editais sem incluir o identificador interno do MongoDB.
editais = list(
    colecao_editais.find(
        {},
        {"_id": 0}
    ).sort("data_lancamento", -1)
)

if not editais:
    st.info("Nenhum edital cadastrado.")

else:

    # Apresenta a quantidade de editais com concordância de número.
    quantidade_editais = len(editais)
    texto_editais = "edital cadastrado" if quantidade_editais == 1 else "editais cadastrados"
    st.write(f"{quantidade_editais} {texto_editais}.")


    for edital in editais:

        # Organiza as informações de cada edital em um container com borda.
        with st.container(border=True):

            # Apresenta o código e o nome do edital em um único título.
            st.markdown(
                f"#### {edital.get('codigo_edital', 'Não informado')} - "
                f"{edital.get('nome_edital', 'Edital sem nome')}"
            )

            # Distribui as informações do edital em duas colunas.
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"**Data de lançamento:** "
                    f"{edital.get('data_lancamento', 'Não informada')}"
                )

                valor_edital = edital.get("valor_edital")

                if valor_edital is None:
                    valor_formatado = "Não informado"
                else:
                    valor_formatado = (
                        f"R$ {formatar_valor_brasileiro(valor_edital)}"
                    )

                st.markdown(
                    f"**Valor do edital:** {valor_formatado}"
                )

                # Disponibiliza os estágios e as tags em popovers.
                col_estagios, col_tags = st.columns(2)

                with col_estagios:
                    estagios = edital.get("estagios", [])

                    with st.popover(
                        f"Estágios ({len(estagios)})",
                        type="tertiary"
                    ):
                        renderizar_estagios(estagios)

                with col_tags:
                    tags = edital.get("tags", [])

                    with st.popover(
                        f"Tags ({len(tags)})",
                        type="tertiary"
                    ):
                        renderizar_tags(tags)

            with col2:
                st.markdown(
                    f"**Data de encerramento:** "
                    f"{edital.get('data_encerramento', 'Não informada')}"
                )


            # Botão para abrir edital e ver projetos
            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button(
                    "Ver projetos",
                    key=f"ver_projetos_{edital.get('codigo_edital', 'sem_codigo')}",
                    type="primary"
                ):
                    st.session_state["edital_selecionado"] = edital
                    st.session_state["pagina_atual"] = "ver_projetos"
                    st.rerun()