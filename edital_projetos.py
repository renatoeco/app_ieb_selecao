import streamlit as st
import pandas as pd

from funcoes_auxiliares import (
    conectar_mongo_ieb_selecao,
    container_cinza,
    configurar_containers_cinza,
    renderizar_tag_css
)

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


configurar_containers_cinza()


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




###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS
###########################################################################################################

db = conectar_mongo_ieb_selecao()
col_pessoas = db["pessoas"]
col_projetos = db["projetos"]




###########################################################################################################
# FUNÇÕES AUXILIARES
###########################################################################################################


def renderizar_projeto(projeto, indice):
    """Renderiza o container individual de uma proposta recebida."""

    codigo = str(
        projeto.get("codigo_recebimento") or indice
    ).strip()

    chave_checkbox = f"selecionar_projeto_{codigo}"

    # Organiza o checkbox e o container do projeto na mesma linha.
    with st.container(horizontal=True, vertical_alignment="center"):

        # Exibe o checkbox somente no modo de seleção.
        if st.session_state.get("_modo_selecao_projetos") == "Selecionar":
            st.checkbox(
                "",
                key=chave_checkbox,
                label_visibility="collapsed"
            )

        with container_cinza():

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

            # Recupera estágio e tags diretamente do MongoDB.
            documento_projeto = col_projetos.find_one(
                {
                    "codigo_edital": edital.get("codigo_edital"),
                    "codigo_recebimento": codigo_recebimento
                },
                {
                    "_id": 0,
                    "estagio": 1,
                    "tags": 1
                }
            ) or {}



            with st.container(
                horizontal=True,
                horizontal_alignment="distribute",
                vertical_alignment="center"
            ):


                with st.container(horizontal=True, horizontal_alignment="left"):

                    # Exibe o estágio atual em letras maiúsculas.
                    estagio = documento_projeto.get("estagio")

                    if estagio:
                        st.markdown(f"{str(estagio).upper()}")

                    # Recupera os IDs das tags associadas ao projeto.
                    ids_tags_projeto = {
                        str(tag_id).strip()
                        for tag_id in (documento_projeto.get("tags") or [])
                        if tag_id is not None
                    }

                    # Renderiza as tags cadastradas no edital.
                    for tag in edital.get("tags", []):

                        tag_id = str(tag.get("id", "")).strip()

                        if tag_id in ids_tags_projeto:
                            renderizar_tag_css(tag)

                # Botão para abrir a página de detalhes do projeto.
                if st.button(
                    "Ver projeto",
                    key=f"ver_projeto_{codigo}",
                    icon=":material/visibility:",
                    type="primary"
                ):
                    st.session_state["projeto_atual"] = projeto
                    st.session_state["pagina_atual"] = "ver_projeto"
                    st.rerun()


# def renderizar_projeto(projeto, indice):
#     """Renderiza o container individual de uma proposta recebida."""

#     codigo = str(
#         projeto.get("codigo_recebimento") or indice
#     ).strip()

#     chave_checkbox = f"selecionar_projeto_{codigo}"

#     # Organiza o checkbox e o container do projeto na mesma linha.
#     with st.container(horizontal=True, vertical_alignment="center"):

#         # Exibe o checkbox somente no modo de seleção.
#         if st.session_state.get("_modo_selecao_projetos") == "Selecionar":
#             st.checkbox(
#                 "",
#                 key=chave_checkbox,
#                 label_visibility="collapsed"
#             )

#         with container_cinza():

#             # Identificação do projeto.
#             codigo_recebimento = projeto.get("codigo_recebimento", "Sem código")
#             sigla = projeto.get("Sigla da organização", "Sem sigla")
#             nome_org = projeto.get("Nome da organização", "Organização sem nome")

#             st.markdown(
#                 f'<span style="color: #2F5AA1; font-weight: bold;">{codigo_recebimento}</span> - '
#                 f'**{sigla}** - {nome_org}',
#                 unsafe_allow_html=True
#             )

#             st.write(f"Projeto {projeto.get('Nome do projeto', 'Sem código')}")

#             with st.container(
#                 horizontal=True,
#                 horizontal_alignment="right",
#                 vertical_alignment="center"
#             ):

#                 # Exibe o estágio atual em letras maiúsculas.
#                 estagio = projeto.get("estagio")

#                 if estagio:
#                     st.markdown(f"**{str(estagio).upper()}**")

#                 # Recupera os IDs das tags associadas ao projeto.
#                 ids_tags_projeto = {
#                     str(tag_id).strip()
#                     for tag_id in (projeto.get("tags") or [])
#                     if tag_id is not None
#                 }

#                 # Renderiza as tags cadastradas no edital.
#                 for tag in edital.get("tags", []):

#                     tag_id = str(tag.get("id", "")).strip()

#                     if tag_id in ids_tags_projeto:
#                         renderizar_tag_css(tag)

#                 # Botão para abrir a página de detalhes do projeto.
#                 if st.button(
#                     "Ver projeto",
#                     key=f"ver_projeto_{codigo}",
#                     icon=":material/visibility:",
#                     type="primary"
#                 ):
#                     st.session_state["projeto_atual"] = projeto
#                     st.session_state["pagina_atual"] = "ver_projeto"
#                     st.rerun()




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
    st.subheader(
        f"{edital.get('codigo_edital', 'Não informado')} - "
        f"{edital.get('nome_edital', 'Edital sem nome')}"
    )

    st.write('')


    # Inicializa o estado do toggle.
    if "_toggle_minhas_avaliacoes" not in st.session_state:
        st.session_state["_toggle_minhas_avaliacoes"] = False

    # Define o modo de visualização conforme o tipo de usuário.
    if tipo_usuario in ["admin", "equipe"]:
        if st.session_state["_toggle_minhas_avaliacoes"]:
            modo_projetos = "minhas_avaliacoes"
        else:
            modo_projetos = "todos_projetos"

    elif tipo_usuario == "avaliador":
        modo_projetos = "minhas_avaliacoes"

    else:
        modo_projetos = "sem_acesso"

    st.session_state["modo_projetos"] = modo_projetos






    ###########################################################################################################
    # CARREGAMENTO DAS PROPOSTAS RECEBIDAS
    ###########################################################################################################


    id_planilha = edital.get("id_planilha_recebimento")

    if not id_planilha:
        st.warning("Este edital não possui uma planilha de recebimento cadastrada.")

    else:
        try:
            df_propostas = ler_planilha_google_sheets(id_planilha)



            if df_propostas.empty:
                st.info("Nenhuma proposta encontrada na planilha.")

            else:



                ###########################################################################################################
                # FILTRAGEM DE PROJETOS CONFORME O MODO DE VISUALIZAÇÃO
                ###########################################################################################################

                # Todos os projetos do edital.
                if modo_projetos == "todos_projetos":

                    df_projetos = df_propostas.copy()

                # Somente projetos atribuídos ao usuário conectado.
                elif modo_projetos == "minhas_avaliacoes":

                    # Recupera o documento da pessoa conectada.
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
                                    str(codigo).strip()
                                    for codigo in estagio.get("projetos", [])
                                    if codigo is not None
                                )

                    # Filtra a planilha pelos códigos atribuídos à pessoa.
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




                # Exibe a quantidade de propostas e o toggle e minhas avaliações
                with st.container(horizontal=True, horizontal_alignment="distribute"):

                    st.markdown(
                        f"##### {len(df_projetos)} propostas recebidas"
                    )

                    # Apenas administradores e equipe podem alternar a visualização.
                    if tipo_usuario in ["admin", "equipe"]:
                        st.toggle(
                            "Minhas avaliações",
                            key="_toggle_minhas_avaliacoes"
                        )





                ###########################################################################################################
                # LISTAGEM DE PROJETOS
                ###########################################################################################################

                if df_projetos.empty:

                    if modo_projetos == "minhas_avaliacoes":
                        st.info("Nenhum projeto está atribuído a este usuário neste edital.")
                    else:
                        st.warning("Este usuário não possui permissão para visualizar os projetos.")

                else:





                    # Converte os registros do DataFrame em uma lista de dicionários.
                    propostas = df_projetos.to_dict(orient="records")






                    # #########################################################################################################
                    # LINHA DE BOTÕES DE AÇÃO
                    # #########################################################################################################

                    if tipo_usuario in ["admin", "equipe"] and modo_projetos == "todos_projetos":

                        # Inicializa o estado do modo de seleção.
                        if "_modo_selecao_projetos" not in st.session_state:
                            st.session_state["_modo_selecao_projetos"] = "Desativado"

                        # Exibe a confirmação de operações realizadas.
                        mensagem_acao = st.session_state.pop("_mensagem_acao_projetos", None)

                        if mensagem_acao:
                            st.toast(mensagem_acao, icon=":material/check_circle:", duration="long")


                        # Linha principal de ações.
                        with st.container(horizontal=True, horizontal_alignment="left"):

                            st.segmented_control(
                                "Modo de seleção",
                                options=["Filtros", "Selecionar"],
                                key="_modo_selecao_projetos",
                                width="stretch",
                                label_visibility="collapsed"
                            )


                        # Exibe as ações de seleção quando o modo estiver ativado.
                        if st.session_state.get("_modo_selecao_projetos") == "Selecionar":

                            with st.container(horizontal=True, horizontal_alignment="left"):

                                # Seleciona todos os projetos da listagem atual.
                                if st.button(
                                    "Selecionar todos",
                                    type="tertiary",
                                    key="selecionar_todos_projetos"
                                ):

                                    for indice, projeto in enumerate(propostas):

                                        codigo = str(
                                            projeto.get("codigo_recebimento") or indice
                                        ).strip()

                                        st.session_state[f"selecionar_projeto_{codigo}"] = True

                                # Limpa a seleção de todos os projetos da listagem atual.
                                if st.button(
                                    "Limpar seleção",
                                    type="tertiary",
                                    key="limpar_selecao_projetos"
                                ):

                                    for indice, projeto in enumerate(propostas):

                                        codigo = str(
                                            projeto.get("codigo_recebimento") or indice
                                        ).strip()

                                        st.session_state[f"selecionar_projeto_{codigo}"] = False


                            # Recupera os projetos selecionados.
                            projetos_selecionados = []
                            codigos_selecionados = []

                            for indice, projeto in enumerate(propostas):

                                codigo = str(
                                    projeto.get("codigo_recebimento") or indice
                                ).strip()

                                chave_checkbox = f"selecionar_projeto_{codigo}"

                                if st.session_state.get(chave_checkbox, False):

                                    projetos_selecionados.append(projeto)
                                    codigos_selecionados.append(codigo)


                            ###########################################################################################################
                            # PREPARAÇÃO DOS ESTÁGIOS
                            ###########################################################################################################

                            # Recupera os estágios cadastrados no edital.
                            estagios_edital = sorted(
                                edital.get("estagios", []),
                                key=lambda item: item.get("ordem_estagio", 999999)
                            )

                            # Garante que Banco seja sempre o último estágio.
                            estagios_edital = [
                                estagio for estagio in estagios_edital
                                if estagio.get("nome_estagio", "").strip().lower() != "banco"
                            ]

                            estagios_edital.append({
                                "nome_estagio": "Banco",
                                "ordem_estagio": 999999
                            })



                            ###########################################################################################################
                            # PREPARAÇÃO DAS TAGS
                            ###########################################################################################################

                            # Recupera as tags cadastradas no edital.
                            tags_edital = [
                                tag for tag in edital.get("tags", [])
                                if str(tag.get("id", "")).strip()
                            ]

                            ids_tags_edital = [
                                str(tag["id"]).strip()
                                for tag in tags_edital
                            ]

                            # Recupera novamente os documentos dos projetos selecionados no MongoDB.
                            documentos_selecionados = list(
                                col_projetos.find(
                                    {
                                        "codigo_edital": edital.get("codigo_edital"),
                                        "codigo_recebimento": {
                                            "$in": codigos_selecionados
                                        }
                                    },
                                    {
                                        "_id": 0,
                                        "codigo_recebimento": 1,
                                        "tags": 1
                                    }
                                )
                            ) if codigos_selecionados else []

                            # Recupera os conjuntos de IDs das tags de cada projeto.
                            conjuntos_tags_projetos = [
                                {
                                    str(tag_id).strip()
                                    for tag_id in (projeto.get("tags") or [])
                                    if tag_id is not None
                                }
                                for projeto in documentos_selecionados
                            ]

                            # Identifica as tags comuns a todos os projetos selecionados.
                            if conjuntos_tags_projetos:
                                tags_comuns = set.intersection(*conjuntos_tags_projetos)
                            else:
                                tags_comuns = set()

                            # Guarda as tags que estavam comuns antes das alterações no formulário.
                            tags_comuns_iniciais = set(tags_comuns)

                            # Inicializa os checkboxes sempre que a seleção ou as tags comuns mudarem.
                            assinatura_selecao_tags = (
                                tuple(sorted(codigos_selecionados)),
                                tuple(sorted(tags_comuns))
                            )

                            if st.session_state.get("_assinatura_selecao_tags") != assinatura_selecao_tags:

                                for tag_id in ids_tags_edital:

                                    chave_tag = f"checkbox_tag_{tag_id}"

                                    st.session_state[chave_tag] = tag_id in tags_comuns

                                st.session_state["_assinatura_selecao_tags"] = assinatura_selecao_tags



                            ###########################################################################################################
                            # CONTADOR E POPOVERS DE AÇÕES
                            ###########################################################################################################

                            quantidade_selecionados = len(codigos_selecionados)

                            texto_selecionados = (
                                "1 projeto selecionado"
                                if quantidade_selecionados == 1
                                else f"{quantidade_selecionados} projetos selecionados"
                            )

                            with st.container(
                                horizontal=True,
                                horizontal_alignment="distribute",
                                vertical_alignment="center"
                            ):

                                st.caption(texto_selecionados)

                                # Agrupa os popovers à direita.
                                with st.container(
                                    horizontal=True,
                                    horizontal_alignment="right",
                                    vertical_alignment="center"
                                ):

                                    ###########################################################################################################
                                    # POPOVER: MUDAR ESTÁGIO
                                    ###########################################################################################################

                                    with st.popover(
                                        "Mudar estágio",
                                        disabled=quantidade_selecionados == 0
                                    ):

                                        st.write("Selecione o novo estágio:")

                                        for indice_estagio, estagio in enumerate(estagios_edital):

                                            nome_estagio = estagio.get("nome_estagio", "").strip()

                                            if not nome_estagio:
                                                continue

                                            if st.button(
                                                nome_estagio,
                                                type="secondary",
                                                key=f"mudar_estagio_{indice_estagio}",
                                                width="stretch"
                                            ):

                                                # Atualiza somente o estágio dos projetos selecionados.
                                                resultado = col_projetos.update_many(
                                                    {
                                                        "codigo_edital": edital.get("codigo_edital"),
                                                        "codigo_recebimento": {
                                                            "$in": codigos_selecionados
                                                        }
                                                    },
                                                    {
                                                        "$set": {
                                                            "estagio": nome_estagio
                                                        }
                                                    }
                                                )

                                                st.session_state["_mensagem_acao_projetos"] = (
                                                    f"Estágio '**{nome_estagio}**' aplicado a "
                                                    f"{resultado.matched_count} projeto(s)."
                                                )

                                                st.session_state["_tipo_mensagem_acao_projetos"] = (
                                                    "success" if resultado.matched_count > 0 else "warning"
                                                )

                                                st.rerun()


                                    ###########################################################################################################
                                    # POPOVER: TAGS
                                    ###########################################################################################################

                                    with st.popover(
                                        "Tags",
                                        disabled=quantidade_selecionados == 0
                                    ):
                                        if not tags_edital:

                                            st.caption("Nenhuma tag cadastrada neste edital.")

                                        else:

                                            with st.form("form_alterar_tags_projetos"):

                                                # Apresenta cada tag com sua cor e respectivo checkbox.
                                                for tag in tags_edital:

                                                    tag_id = str(tag["id"]).strip()

                                                    with st.container(
                                                        horizontal=True,
                                                        horizontal_alignment="distribute",
                                                        vertical_alignment="center"
                                                    ):

                                                        renderizar_tag_css(tag)

                                                        st.checkbox(
                                                            f"Selecionar tag {tag.get('nome', '')}",
                                                            key=f"checkbox_tag_{tag_id}",
                                                            disabled=quantidade_selecionados == 0,
                                                            label_visibility="collapsed"
                                                        )

                                                st.write("")

                                                with st.container(horizontal=True, horizontal_alignment="right"):
                                                    # Salva as alterações das tags nos projetos selecionados.
                                                    salvar_tags = st.form_submit_button(
                                                        "Salvar",
                                                        type="primary",
                                                        disabled=quantidade_selecionados == 0
                                                    )

                                                if salvar_tags:

                                                    # Separa os IDs marcados e desmarcados.
                                                    ids_tags_marcadas = [
                                                        tag_id
                                                        for tag_id in ids_tags_edital
                                                        if st.session_state.get(f"checkbox_tag_{tag_id}", False)
                                                    ]

                                                    # Identifica somente as tags anteriormente comuns que foram desmarcadas.
                                                    ids_tags_desmarcadas = [
                                                        tag_id
                                                        for tag_id in tags_comuns_iniciais
                                                        if not st.session_state.get(f"checkbox_tag_{tag_id}", False)
                                                    ]

                                                    # Identifica os documentos dos projetos selecionados.
                                                    filtro_projetos = {
                                                        "codigo_edital": edital.get("codigo_edital"),
                                                        "codigo_recebimento": {
                                                            "$in": codigos_selecionados
                                                        }
                                                    }

                                                    total_projetos = col_projetos.count_documents(
                                                        filtro_projetos
                                                    )

                                                    # Adiciona as tags marcadas, sem duplicar IDs existentes.
                                                    if ids_tags_marcadas:

                                                        col_projetos.update_many(
                                                            filtro_projetos,
                                                            {
                                                                "$addToSet": {
                                                                    "tags": {
                                                                        "$each": ids_tags_marcadas
                                                                    }
                                                                }
                                                            }
                                                        )

                                                    # Remove as tags desmarcadas dos projetos selecionados.
                                                    if ids_tags_desmarcadas:

                                                        col_projetos.update_many(
                                                            filtro_projetos,
                                                            {
                                                                "$pull": {
                                                                    "tags": {
                                                                        "$in": ids_tags_desmarcadas
                                                                    }
                                                                }
                                                            }
                                                        )

                                                    st.session_state["_mensagem_acao_projetos"] = (
                                                        f"Tags atualizadas em {total_projetos} projeto(s)."
                                                    )

                                                    st.session_state["_tipo_mensagem_acao_projetos"] = (
                                                        "success" if total_projetos > 0 else "warning"
                                                    )

                                                    st.rerun()


                    # #########################################################################################################
                    # RENDERIZAÇÃO DOS PROJETOS
                    # #########################################################################################################

                    st.write("")

                    # Renderiza o container individual de cada proposta.
                    for indice, projeto in enumerate(propostas):
                        renderizar_projeto(projeto, indice)







        except Exception as e:
            st.error(f"Erro ao carregar a planilha de propostas: {e}")

