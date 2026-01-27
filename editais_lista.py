import streamlit as st
from funcoes_auxiliares import conectar_mongo_ieb_selecao
import pandas as pd




###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_ieb_selecao()

colecao_editais = db["editais"]





###########################################################################################################
# INTERFACE
###########################################################################################################


# Logo do sidebar
st.logo("images/logo_ieb.svg", size='large')

st.header('Editais')

# st.write('')
st.divider()



