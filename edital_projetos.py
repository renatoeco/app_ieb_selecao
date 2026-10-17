import streamlit as st

###########################################################################################################
# NAVEGAÇÃO
###########################################################################################################

# Permite retornar à listagem original de editais.
with st.sidebar:
    if st.button(
        "Voltar para Editais",
        icon=":material/arrow_back:",
        type="secondary"
    ):
        st.session_state["pagina_atual"] = "home_admin"
        st.session_state.pop("edital_selecionado", None)
        st.rerun()

###########################################################################################################
# IDENTIFICAÇÃO DO EDITAL SELECIONADO
###########################################################################################################

edital = st.session_state.get("edital_selecionado")

if not edital:
    st.warning("Nenhum edital foi selecionado.")
    st.stop()

st.header("Projetos do edital")
st.subheader(
    f"{edital.get('codigo_edital', 'Não informado')} - "
    f"{edital.get('nome_edital', 'Edital sem nome')}"
)

st.divider()

###########################################################################################################
# LISTAGEM DE PROJETOS
###########################################################################################################

# Inserir aqui a consulta ao MongoDB e a interface de listagem dos projetos.