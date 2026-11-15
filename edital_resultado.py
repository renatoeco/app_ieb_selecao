import streamlit as st






###########################################################################################################
# NAVEGAÇÃO
###########################################################################################################

st.logo("images/logo_selecao.png", size='large')

tipo_usuario = st.session_state["tipo_usuario"]

# Permite retornar à listagem original de editais.
with st.sidebar:
    if st.button(
        "Voltar para Editais",
        icon=":material/arrow_back:",
        type="secondary"
    ):

        if tipo_usuario == "admin":
        
            st.session_state["pagina_atual"] = "home_admin"

        elif tipo_usuario == "avaliador":
        
            st.session_state["pagina_atual"] = "home_avaliador"

        st.session_state.pop("edital_selecionado", None)
        st.rerun()





# ###########################################################################################################
# INTEFACE
# ###########################################################################################################

st.subheader("Resultado do Edital")