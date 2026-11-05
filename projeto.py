import streamlit as st


###########################################################################################################
# NAVEGAÇÃO
###########################################################################################################

st.logo("images/selecao.png", size="large")

with st.sidebar:
    if st.button("Voltar para Projetos", icon=":material/arrow_back:"):
        st.session_state["pagina_atual"] = "ver_projetos"
        st.rerun()


# Recupera o projeto selecionado
projeto = st.session_state.get("projeto_atual")

if not projeto:

    st.warning("Nenhum projeto foi selecionado.")


else:





    ###########################################################################################################
    # IDENTIFICAÇÃO DO PROJETO
    ###########################################################################################################

    codigo = projeto.get("codigo_recebimento", "")
    sigla = projeto.get("Sigla da organização", "")
    organizacao = projeto.get("Nome da organização", "")
    nome_projeto = projeto.get("Nome do projeto", "")

    st.markdown(
        f"""
        <h2>
            <span style="color: #1e5aa6;">{codigo}</span> {sigla}
        </h2>
        """,
        unsafe_allow_html=True
    )

    if organizacao:
        st.markdown(
            f"<h3 style='color: #1e5aa6;'>{organizacao}</h3>",
            unsafe_allow_html=True
        )

    if nome_projeto:
        st.write(f"**{nome_projeto}**")


    ###########################################################################################################
    # DEMAIS INFORMAÇÕES DO PROJETO
    ###########################################################################################################


    st.subheader("Informações do projeto")

    # Campos já apresentados no cabeçalho
    campos_cabecalho = [
        "codigo_recebimento",
        "Sigla da organização",
        "Nome da organização",
        "Nome do projeto"
    ]

    # Exibe os demais campos da planilha
    campos_projeto = [
        (campo, valor)
        for campo, valor in projeto.items()
        if campo not in campos_cabecalho
        and valor is not None
        and str(valor).strip().lower() not in ["", "nan", "none"]
    ]

    for campo in campos_projeto:

        st.write(f"**{campo[0]}**: {campo[1]}")
