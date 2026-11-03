import streamlit as st
import pandas as pd

from funcoes_auxiliares import (
    conectar_mongo_ieb_selecao
)

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build




###########################################################################################################
# NAVEGAÇÃO
###########################################################################################################

st.logo("images/logo_ieb.svg", size='large')


# Permite retornar à listagem original de editais.
with st.sidebar:
    if st.button(
        "Voltar para Editais",
        icon=":material/arrow_back:",
        type="secondary"
    ):

        if st.session_state.tipo_usuario == "admin":
        
            st.session_state["pagina_atual"] = "home_admin"

        elif st.session_state.tipo_usuario == "avaliador":
        
            st.session_state["pagina_atual"] = "home_avaliador"

        st.session_state.pop("edital_selecionado", None)
        st.rerun()




###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS
###########################################################################################################

db = conectar_mongo_ieb_selecao()
col_pessoas = db["pessoas"]





###########################################################################################################
# FUNÇÕES AUXILIARES
###########################################################################################################

@st.fragment
def renderizar_projeto(projeto, indice):
    """Renderiza o container individual de uma proposta recebida."""

    with st.container(border=True):

        # Identificação do projeto.
        codigo_recebimento = projeto.get("codigo_recebimento", "Sem código")
        sigla = projeto.get("Sigla da organização", "Sem sigla")
        nome_org = projeto.get("Nome da organização", "Organização sem nome")

        st.markdown(
            f'<span style="color: #2F5AA1; font-weight: bold;">{codigo_recebimento}</span> - '
            f'**{sigla}** - {nome_org}',
            unsafe_allow_html=True
        )

        st.write(f"Projeto {projeto.get('Nome do projeto', 'Sem código')}")


@st.cache_data()
def ler_planilha_google_sheets(id_planilha):
    """Lê os dados de uma planilha Google Sheets e retorna um DataFrame."""

    # Configura as credenciais de acesso à API do Google Sheets.
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    credenciais = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    # Estabelece a conexão com a API.
    service = build("sheets", "v4", credentials=credenciais)

    # Recupera os dados da planilha.
    resultado = service.spreadsheets().values().get(
        spreadsheetId=id_planilha,
        range="A:ZZ"
    ).execute()

    valores = resultado.get("values", [])

    if not valores:
        return pd.DataFrame()

    # Utiliza a primeira linha como cabeçalho.
    df = pd.DataFrame(
        valores[1:],
        columns=valores[0]
    )

    return df







###########################################################################################################
# INTERFACE
###########################################################################################################


###########################################################################################################
# IDENTIFICAÇÃO DO EDITAL SELECIONADO
###########################################################################################################

edital = st.session_state.get("edital_selecionado")

if not edital:
    st.warning("Nenhum edital foi selecionado.")

else:
    st.subheader("Projetos do edital "
        f"{edital.get('codigo_edital', 'Não informado')} - "
        f"{edital.get('nome_edital', 'Edital sem nome')}"
    )

    st.write('')

    ###########################################################################################################
    # CARREGAMENTO DAS PROPOSTAS RECEBIDAS
    ###########################################################################################################


    id_planilha = edital.get("id_planilha_recebimento")

    if not id_planilha:
        st.warning("Este edital não possui uma planilha de recebimento cadastrada.")

    else:
        with st.spinner("Carregando propostas recebidas..."):
            try:
                df_propostas = ler_planilha_google_sheets(id_planilha)



                if df_propostas.empty:
                    st.info("Nenhuma proposta encontrada na planilha.")

                else:

                    ###########################################################################################################
                    # FILTRAGEM DE PROJETOS CONFORME O TIPO DE USUÁRIO
                    ###########################################################################################################

                    tipo_usuario = st.session_state.get("tipo_usuario", "")

                    # Administradores e equipe visualizam todos os projetos.
                    if tipo_usuario in ["admin", "equipe"]:
                        df_projetos = df_propostas.copy()

                    # Avaliadores visualizam somente os projetos atribuídos a eles.
                    elif tipo_usuario == "avaliador":

                        # Recupera o documento do avaliador.
                        pessoa = col_pessoas.find_one(
                            {"_id": st.session_state.get("id_usuario")},
                            {"editais": 1}
                        )

                        codigos_projetos = set()

                        if pessoa:

                            # Localiza o edital selecionado no documento da pessoa.
                            edital_pessoa = next(
                                (
                                    item for item in pessoa.get("editais", [])
                                    if item.get("codigo_edital") == edital.get("codigo_edital")
                                ),
                                None
                            )

                            if edital_pessoa:

                                # Recupera os códigos dos projetos atribuídos em todos os estágios.
                                for estagio in edital_pessoa.get("estagios", []):
                                    codigos_projetos.update(
                                        estagio.get("projetos", [])
                                    )

                        # Filtra a planilha pelos códigos atribuídos ao avaliador.
                        if "codigo_recebimento" in df_propostas.columns:

                            df_projetos = df_propostas[
                                df_propostas["codigo_recebimento"]
                                .astype(str)
                                .str.strip()
                                .isin(codigos_projetos)
                            ].copy()

                        else:
                            df_projetos = pd.DataFrame()

                    # Outros tipos de usuário não possuem acesso à listagem.
                    else:
                        df_projetos = pd.DataFrame()

                    ###########################################################################################################
                    # LISTAGEM DE PROJETOS
                    ###########################################################################################################

                    if df_projetos.empty:

                        if tipo_usuario == "avaliador":
                            st.info("Nenhum projeto está atribuído a este avaliador neste edital.")
                        else:
                            st.warning("Este usuário não possui permissão para visualizar os projetos.")

                    else:

                        st.markdown(
                            f"##### {len(df_projetos)} propostas recebidas"
                        )
                        st.write("")

                        # Converte os registros do DataFrame em uma lista de dicionários.
                        propostas = df_projetos.to_dict(orient="records")

                        # Renderiza um fragmento individual para cada proposta.
                        for indice, projeto in enumerate(propostas):
                            renderizar_projeto(projeto, indice)




            except Exception as e:
                st.error(f"Erro ao carregar a planilha de propostas: {e}")

