import streamlit as st
import pandas as pd
import time
from datetime import datetime, date
from funcoes_auxiliares import conectar_mongo_ieb_selecao
from streamlit_sortables import sort_items


# Conectar google driva
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta ao MongoDB usando a função auxiliar
db = conectar_mongo_ieb_selecao()

# Define a coleção de editais
colecao_editais = db.editais



###########################################################################################################
# FUNÇÕES
###########################################################################################################



def ler_planilha_google_sheets(id_planilha):
    """
    Lê todas as linhas de uma planilha Google Sheets
    e retorna um DataFrame com os dados
    """

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )

    service = build("sheets", "v4", credentials=creds)

    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=id_planilha,
        range="A:ZZ"
    ).execute()

    values = result.get("values", [])

    if not values:
        return pd.DataFrame()

    # Primeira linha vira header
    df = pd.DataFrame(values[1:], columns=values[0])
    return df




def carregar_projetos(df_recebidos_sheet, colecao_projetos, codigo_edital):
    """
    Carrega projetos a partir do dataframe.
    Retorna lista de códigos que foram adicionados.
    """

    # Busca projetos já existentes desse edital
    existentes = {
        p["codigo_recebimento"]
        for p in colecao_projetos.find(
            {"codigo_edital": codigo_edital},
            {"codigo_recebimento": 1}
        )
    }

    adicionados = []

    for _, linha in df_recebidos_sheet.iterrows():

        codigo = linha.get("codigo_recebimento")

        if not codigo:
            continue

        # Se já existe, ignora
        if codigo in existentes:
            continue

        # Insere novo projeto
        colecao_projetos.insert_one({
            "codigo_recebimento": codigo,
            "codigo_edital": codigo_edital
        })

        adicionados.append(codigo)

    return adicionados








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

tabs = st.tabs(["Editar", "Estágios", "Carregar"])

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
                value=edital_selecionado["codigo_edital"],
                disabled=True
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

    if edital_selecionado_label == "":
        st.caption("Selecione um edital para gerenciar os estágios.")
    else:
        codigo_edital = edital_selecionado_label.split(" - ")[0]
        edital = colecao_editais.find_one({"codigo_edital": codigo_edital})

        estagios = sorted(
            edital.get("estagios", []),
            key=lambda x: x.get("ordem_estagio", 999)
        )

        ###################################################################################################
        # POPOVER PARA CRIAR NOVO ESTÁGIO
        ###################################################################################################

        with st.popover("Novo estágio", icon=":material/add:"):
            nome_estagio = st.text_input("Nome do estágio")
            ordem_estagio = st.number_input(
                "Ordem do estágio",
                min_value=1,
                value=len(estagios) + 1,
                step=1
            )

            if st.button("Criar estágio", type="primary", icon=":material/save:"):
                if not nome_estagio.strip():
                    st.error("O nome do estágio é obrigatório.")
                elif ordem_estagio in [e["ordem_estagio"] for e in estagios]:
                    st.error("Já existe um estágio com essa ordem.")
                else:
                    colecao_editais.update_one(
                        {"_id": edital["_id"]},
                        {"$push": {
                            "estagios": {
                                "nome_estagio": nome_estagio.strip(),
                                "ordem_estagio": ordem_estagio,
                                "perguntas_estagio": []
                            }
                        }}
                    )
                    st.success("Estágio criado com sucesso.", icon=":material/check:")
                    time.sleep(3)
                    st.rerun()

        st.write("")


        ###########################################################################################################
        # LISTAGEM DOS ESTÁGIOS 
        ###########################################################################################################

        if not estagios:
            st.caption("Nenhum estágio cadastrado.")
        else:
            for estagio in estagios:

                perguntas = sorted(
                    estagio.get("perguntas_estagio", []),
                    key=lambda x: x.get("ordem", 9999)
                )

                titulo_expander = (
                    f"{str(estagio['ordem_estagio'])} - "
                    f"{estagio['nome_estagio']} "
                    f"({str(len(perguntas))} perguntas)"
                )

                with st.expander(titulo_expander, expanded=False):

                    ###################################################################################################
                    # SEGMENTED CONTROL DE AÇÕES 
                    ###################################################################################################

                    key_acao = f"acao_{codigo_edital}_{estagio['ordem_estagio']}"

                    if key_acao not in st.session_state:
                        st.session_state[key_acao] = "Ver perguntas"


                    acao = st.segmented_control(
                        "",
                        [
                            "Ver perguntas",
                            "Nova pergunta",
                            "Editar pergunta",
                            "Reordenar perguntas",
                            "Selecionar avaliadores",
                            "Distribuir projetos"
                        ],
                        width="stretch",
                        key=f"acao_{codigo_edital}_{estagio['nome_estagio']}"
                    )






                    ###################################################################################################
                    # SE NENHUMA AÇÃO SELECIONADA → MOSTRA PERGUNTAS
                    ###################################################################################################

                    if acao == "Ver perguntas":

                        if not perguntas:
                            st.caption("Nenhuma pergunta cadastrada.")
                        else:
                            for p in perguntas:

                                tipo_legivel = {
                                    "texto_curto": "resposta curta",
                                    "texto_longo": "resposta longa",
                                    "numero": "número",
                                    "multipla_escolha": "múltipla escolha",
                                    "escolha_unica": "escolha única",
                                    "titulo": "título",
                                    "subtitulo": "subtítulo",
                                    "paragrafo": "parágrafo"
                                }.get(p["tipo"], p["tipo"])

                                # Renderização conforme tipo
                                if p["tipo"] == "titulo":
                                    st.markdown(f"### {p['pergunta']} *( {tipo_legivel} )*")
                                elif p["tipo"] == "subtitulo":
                                    st.markdown(f"#### {p['pergunta']} *( {tipo_legivel} )*")
                                else:
                                    st.write(
                                        f"{str(p['ordem'])}. **{p['pergunta']}** "
                                        f"*( {tipo_legivel} )*"
                                    )

                    ###################################################################################################
                    # EDITAR ESTÁGIO
                    ###################################################################################################

                    elif acao == "Editar estágio":

                        base_key = f"{codigo_edital}_{estagio['ordem_estagio']}_estagio"

                        novo_nome = st.text_input(
                            "Nome do estágio",
                            value=estagio["nome_estagio"],
                            key=f"{base_key}_nome"
                        )

                        nova_ordem = st.number_input(
                            "Ordem do estágio",
                            min_value=1,
                            value=estagio["ordem_estagio"],
                            step=1,
                            key=f"{base_key}_ordem"
                        )

                        if st.button(
                            "Salvar estágio",
                            type="primary",
                            icon=":material/save:",
                            key=f"{base_key}_salvar"
                        ):
                            ordens_existentes = [
                                e["ordem_estagio"] for e in estagios
                                if e["ordem_estagio"] != estagio["ordem_estagio"]
                            ]

                            if nova_ordem in ordens_existentes:
                                st.error("Já existe um estágio com essa ordem.")
                            elif not novo_nome.strip():
                                st.error("O nome do estágio é obrigatório.")
                            else:
                                colecao_editais.update_one(
                                    {"_id": edital["_id"]},
                                    {"$set": {
                                        "estagios.$[e].nome_estagio": novo_nome.strip(),
                                        "estagios.$[e].ordem_estagio": nova_ordem
                                    }},
                                    array_filters=[
                                        {"e.ordem_estagio": estagio["ordem_estagio"]}
                                    ]
                                )

                                st.success(
                                    "Estágio atualizado com sucesso.",
                                    icon=":material/check:"
                                )
                                time.sleep(3)
                                st.rerun()

                    ###################################################################################################
                    # NOVA PERGUNTA
                    ###################################################################################################

                    elif acao == "Nova pergunta":

                        base_key = f"{codigo_edital}_{estagio['ordem_estagio']}_nova"

                        texto = st.text_input(
                            "Texto da pergunta",
                            key=f"{base_key}_texto"
                        )

                        tipo = st.selectbox(
                            "Tipo",
                            [
                                "texto_curto", "texto_longo", "numero",
                                "multipla_escolha", "escolha_unica",
                                "titulo", "subtitulo", "paragrafo"
                            ],
                            key=f"{base_key}_tipo"
                        )

                        opcoes = []
                        if tipo in ["multipla_escolha", "escolha_unica"]:
                            opcoes = st.text_area(
                                "Opções (uma por linha)",
                                key=f"{base_key}_opcoes"
                            ).split("\n")

                        if st.button(
                            "Salvar pergunta",
                            type="primary",
                            icon=":material/save:",
                            key=f"{base_key}_salvar"
                        ):
                            if not texto.strip():
                                st.error("O texto é obrigatório.")
                            elif tipo in ["multipla_escolha", "escolha_unica"] and not any(o.strip() for o in opcoes):
                                st.error("Informe pelo menos uma opção.")
                            else:
                                nova = {
                                    "ordem": len(perguntas) + 1,
                                    "tipo": tipo,
                                    "pergunta": texto.strip()
                                }

                                if tipo in ["multipla_escolha", "escolha_unica"]:
                                    nova["opcoes"] = [o.strip() for o in opcoes if o.strip()]

                                colecao_editais.update_one(
                                    {"_id": edital["_id"]},
                                    {"$push": {
                                        "estagios.$[e].perguntas_estagio": nova
                                    }},
                                    array_filters=[
                                        {"e.ordem_estagio": estagio["ordem_estagio"]}
                                    ]
                                )

                                st.success(
                                    "Pergunta criada com sucesso.",
                                    icon=":material/check:"
                                )
                                time.sleep(3)
                                st.rerun()


                    ###################################################################################################
                    # EDITAR PERGUNTA
                    ###################################################################################################

                    elif acao == "Editar pergunta":

                        if not perguntas:
                            st.caption("Nenhuma pergunta cadastrada.")
                        else:
                            # Mapa para seleção
                            mapa_perguntas = {
                                f"{str(p['ordem'])}. {p['pergunta']}": p
                                for p in perguntas
                            }

                            selecionada = st.selectbox(
                                "Selecione a pergunta",
                                list(mapa_perguntas.keys()),
                                key=f"{codigo_edital}_{estagio['ordem_estagio']}_pergunta_editar"
                            )

                            pergunta_atual = mapa_perguntas[selecionada]

                            st.divider()

                            # ------------------------------------------------------
                            # TIPO ATUAL
                            # ------------------------------------------------------

                            mapa_tipo_inv = {
                                "texto_curto": "Resposta curta",
                                "texto_longo": "Resposta longa",
                                "numero": "Número",
                                "multipla_escolha": "Múltipla escolha",
                                "escolha_unica": "Escolha única",
                                "titulo": "Título",
                                "subtitulo": "Subtítulo",
                                "paragrafo": "Parágrafo"
                            }

                            tipo_legivel = mapa_tipo_inv.get(pergunta_atual["tipo"], pergunta_atual["tipo"])

                            tipo = st.selectbox(
                                "Tipo de pergunta",
                                list(mapa_tipo_inv.values()),
                                index=list(mapa_tipo_inv.values()).index(tipo_legivel),
                                key=f"{codigo_edital}_{estagio['ordem_estagio']}_{pergunta_atual['ordem']}_tipo"
                            )

                            # ------------------------------------------------------
                            # CAMPOS DINÂMICOS
                            # ------------------------------------------------------

                            mapa_tipo = {
                                "Resposta curta": "texto_curto",
                                "Resposta longa": "texto_longo",
                                "Número": "numero",
                                "Múltipla escolha": "multipla_escolha",
                                "Escolha única": "escolha_unica",
                                "Título": "titulo",
                                "Subtítulo": "subtitulo",
                                "Parágrafo": "paragrafo"
                            }

                            tipo_db = mapa_tipo[tipo]

                            label_texto = "Texto da pergunta"
                            if tipo_db == "titulo":
                                label_texto = "Texto do título"
                            elif tipo_db == "subtitulo":
                                label_texto = "Texto do subtítulo"
                            elif tipo_db == "paragrafo":
                                label_texto = "Texto do parágrafo"

                            if tipo_db == "paragrafo":
                                texto = st.text_area(
                                    label_texto,
                                    value=pergunta_atual.get("pergunta", ""),
                                    key=f"{codigo_edital}_{estagio['ordem_estagio']}_{pergunta_atual['ordem']}_texto_area"
                                )
                            else:
                                texto = st.text_input(
                                    label_texto,
                                    value=pergunta_atual.get("pergunta", ""),
                                    key=f"{codigo_edital}_{estagio['ordem_estagio']}_{pergunta_atual['ordem']}_texto"
                                )

                            opcoes = []
                            if tipo_db in ["multipla_escolha", "escolha_unica"]:
                                opcoes = st.text_area(
                                    "Opções (uma por linha)",
                                    value="\n".join(pergunta_atual.get("opcoes", [])),
                                    key=f"{codigo_edital}_{estagio['ordem_estagio']}_{pergunta_atual['ordem']}_opcoes"
                                ).split("\n")

                            st.write("")

                            # ------------------------------------------------------
                            # BOTÕES DE AÇÃO
                            # ------------------------------------------------------

                            col_salvar, col_excluir = st.columns(2)

                            # -------- SALVAR --------
                            if col_salvar.button(
                                "Salvar alterações",
                                type="primary",
                                icon=":material/save:",
                                key=f"{codigo_edital}_{estagio['ordem_estagio']}_{pergunta_atual['ordem']}_salvar"
                            ):
                                if not texto.strip():
                                    st.error("O texto não pode ficar vazio.")
                                elif tipo_db in ["multipla_escolha", "escolha_unica"] and not any(o.strip() for o in opcoes):
                                    st.error("Informe pelo menos uma opção.")
                                else:
                                    nova = {
                                        "tipo": tipo_db,
                                        "ordem": pergunta_atual["ordem"],
                                        "pergunta": texto.strip()
                                    }

                                    if tipo_db in ["multipla_escolha", "escolha_unica"]:
                                        nova["opcoes"] = [o.strip() for o in opcoes if o.strip()]

                                    perguntas_atualizadas = [
                                        nova if p == pergunta_atual else p
                                        for p in perguntas
                                    ]

                                    colecao_editais.update_one(
                                        {"_id": edital["_id"]},
                                        {"$set": {
                                            "estagios.$[e].perguntas_estagio": perguntas_atualizadas
                                        }},
                                        array_filters=[
                                            {"e.ordem_estagio": estagio["ordem_estagio"]}
                                        ]
                                    )

                                    st.success(
                                        "Pergunta atualizada com sucesso.",
                                        icon=":material/check:"
                                    )
                                    time.sleep(3)
                                    st.rerun()

                            # -------- EXCLUIR --------
                            if col_excluir.button(
                                "Excluir pergunta",
                                icon=":material/delete:",
                                key=f"{codigo_edital}_{estagio['ordem_estagio']}_{pergunta_atual['ordem']}_excluir"
                            ):
                                perguntas_filtradas = [
                                    p for p in perguntas if p != pergunta_atual
                                ]

                                colecao_editais.update_one(
                                    {"_id": edital["_id"]},
                                    {"$set": {
                                        "estagios.$[e].perguntas_estagio": perguntas_filtradas
                                    }},
                                    array_filters=[
                                        {"e.ordem_estagio": estagio["ordem_estagio"]}
                                    ]
                                )

                                st.success(
                                    "Pergunta excluída com sucesso.",
                                    icon=":material/check:"
                                )
                                time.sleep(3)
                                st.rerun()




                    ###################################################################################################
                    # REORDENAR PERGUNTAS
                    ###################################################################################################

                    elif acao == "Reordenar pergunta":

                        if not perguntas:
                            st.caption("Nenhuma pergunta para reordenar.")
                        else:
                            nova_ordem = sort_items(
                                items=[p["pergunta"] for p in perguntas],
                                direction="vertical"
                            )

                            if st.button(
                                "Salvar nova ordem",
                                type="primary",
                                icon=":material/save:",
                                key=f"{codigo_edital}_{estagio['ordem_estagio']}_reordenar"
                            ):
                                novas = []
                                for i, texto in enumerate(nova_ordem, start=1):
                                    p = next(p for p in perguntas if p["pergunta"] == texto)
                                    p["ordem"] = i
                                    novas.append(p)

                                colecao_editais.update_one(
                                    {"_id": edital["_id"]},
                                    {"$set": {
                                        "estagios.$[e].perguntas_estagio": novas
                                    }},
                                    array_filters=[
                                        {"e.ordem_estagio": estagio["ordem_estagio"]}
                                    ]
                                )

                                st.success(
                                    "Ordem atualizada com sucesso.",
                                    icon=":material/check:"
                                )
                                time.sleep(3)
                                st.rerun()




                    ###############################################################################################
                    # SELECIONAR AVALIADORES DO ESTÁGIO
                    ###############################################################################################
                    elif acao == "Selecionar avaliadores":

                        st.write('')

                        st.markdown("##### Selecione as pessoas que irão avaliar este estágio:")

                        # Busca pessoas ativas
                        pessoas_ativas = list(
                            db.pessoas.find(
                                {"status": "ativo"},
                                {"nome_completo": 1, "editais": 1}
                            )
                        )

                        if not pessoas_ativas:
                            st.caption("Nenhuma pessoa ativa encontrada.")
                        else:
                            selecao_ui = {}

                            for pessoa in pessoas_ativas:
                                pessoa_id = str(pessoa["_id"])

                                # Verifica se a pessoa já está vinculada ao estágio
                                editais_pessoa = pessoa.get("editais", [])

                                edital_pessoa = next(
                                    (e for e in editais_pessoa if e["codigo_edital"] == codigo_edital),
                                    None
                                )

                                estagios_pessoa = edital_pessoa.get("estagios", []) if edital_pessoa else []

                                ja_vinculado = any(
                                    e["nome_estagio"] == estagio["nome_estagio"]
                                    for e in estagios_pessoa
                                )

                                key_checkbox = f"dist_{pessoa_id}_{codigo_edital}_{estagio['nome_estagio']}"

                                marcado = st.checkbox(
                                    pessoa["nome_completo"],
                                    value=ja_vinculado,
                                    key=key_checkbox
                                )

                                selecao_ui[pessoa_id] = {
                                    "marcado": marcado,
                                    "marcado_inicial": ja_vinculado,
                                    "_id": pessoa["_id"]
                                }

                            st.write("")

                            if st.button(
                                "Salvar avaliadores(as)",
                                type="primary",
                                icon=":material/save:",
                                key=f"salvar_avaliadores_{codigo_edital}_{estagio['nome_estagio']}"
                            ):
                                for pessoa_id, dados in selecao_ui.items():

                                    marcado = dados["marcado"]
                                    marcado_inicial = dados["marcado_inicial"]
                                    pessoa_mongo_id = dados["_id"]

                                    # Marcado agora → adiciona
                                    if marcado and not marcado_inicial:

                                        # Garante edital
                                        db.pessoas.update_one(
                                            {
                                                "_id": pessoa_mongo_id,
                                                "editais.codigo_edital": {"$ne": codigo_edital}
                                            },
                                            {"$push": {
                                                "editais": {
                                                    "codigo_edital": codigo_edital,
                                                    "estagios": []
                                                }
                                            }}
                                        )

                                        # Adiciona estágio
                                        db.pessoas.update_one(
                                            {
                                                "_id": pessoa_mongo_id,
                                                "editais.codigo_edital": codigo_edital,
                                                "editais.estagios.nome_estagio": {"$ne": estagio["nome_estagio"]}
                                            },
                                            {"$push": {
                                                "editais.$.estagios": {
                                                    "nome_estagio": estagio["nome_estagio"],
                                                    "projetos": []
                                                }
                                            }}
                                        )

                                    # Desmarcado agora → remove
                                    if not marcado and marcado_inicial:
                                        db.pessoas.update_one(
                                            {"_id": pessoa_mongo_id},
                                            {"$pull": {
                                                "editais.$[e].estagios": {
                                                    "nome_estagio": estagio["nome_estagio"]
                                                }
                                            }},
                                            array_filters=[
                                                {"e.codigo_edital": codigo_edital}
                                            ]
                                        )

                                st.success(
                                    "Avaliadores(as) atualizados com sucesso.",
                                    icon=":material/check:"
                                )








                    ###############################################################################################
                    # DISTRIBUIR PROJETOS DO ESTÁGIO
                    ###############################################################################################
                    elif acao == "Distribuir projetos":

                        st.write('')

                        ###################################################################################################
                        # BUSCA TODOS OS PROJETOS DO EDITAL
                        ###################################################################################################
                        projetos = list(
                            db.projetos.find(
                                {"codigo_edital": codigo_edital},
                                {"codigo_recebimento": 1}
                            )
                        )

                        lista_projetos = sorted(
                            [p["codigo_recebimento"] for p in projetos]
                        )

                        ###################################################################################################
                        # BUSCA TODAS AS PESSOAS SELECIONADAS PARA ESSE ESTÁGIO
                        ###################################################################################################
                        pessoas_estagio = list(
                            db.pessoas.find(
                                {
                                    "editais.codigo_edital": codigo_edital,
                                    "editais.estagios.nome_estagio": estagio["nome_estagio"]
                                },
                                {"nome_completo": 1, "editais": 1}
                            )
                        )

                        if not pessoas_estagio:
                            st.caption("Nenhum avaliador selecionado para este estágio.")
                        else:
                            ################################################################################################
                            # COLUNAS PRINCIPAIS
                            ################################################################################################
                            col1, col2, col3 = st.columns([4, 2, 2])

                            ################################################################################################
                            # COLUNA 1 — DISTRIBUIÇÃO POR PESSOA
                            ################################################################################################
                            with col1:
                                st.write("##### Distribuição de projetos")

                                # Guarda seleção atual para atualizar placares
                                distribuicao_atual = {}

                                for pessoa in pessoas_estagio:

                                    st.write('')

                                    nome = pessoa["nome_completo"]
                                    pessoa_id = pessoa["_id"]

                                    # Busca projetos já atribuídos
                                    edital_pessoa = next(
                                        e for e in pessoa["editais"]
                                        if e["codigo_edital"] == codigo_edital
                                    )

                                    estagio_pessoa = next(
                                        e for e in edital_pessoa["estagios"]
                                        if e["nome_estagio"] == estagio["nome_estagio"]
                                    )

                                    projetos_atual = estagio_pessoa.get("projetos", [])

                                

                                    # Multiselect
                                    selecionados = st.multiselect(
                                        f"{nome}",
                                        options=lista_projetos,
                                        default=projetos_atual,
                                        key=f"multi_{pessoa_id}_{estagio['nome_estagio']}"
                                    )

                                    # Botão salvar por pessoa
                                    if st.button(
                                        "Salvar",
                                        icon=":material/save:",
                                        # type="tertiary",
                                        key=f"salvar_proj_{pessoa_id}_{estagio['nome_estagio']}"
                                    ):
                                        # Atualiza projetos da pessoa
                                        db.pessoas.update_one(
                                            {"_id": pessoa_id},
                                            {"$set": {
                                                "editais.$[e].estagios.$[s].projetos": selecionados
                                            }},
                                            array_filters=[
                                                {"e.codigo_edital": codigo_edital},
                                                {"s.nome_estagio": estagio["nome_estagio"]}
                                            ]
                                        )

                                        # Placeholder para mensagem temporária
                                        msg = st.empty()

                                        msg.success(
                                            f"Projetos salvos para {nome}.",
                                            icon=":material/check:"
                                        )

                                        time.sleep(2)
                                        msg.empty()


                                    # Guarda para placar
                                    distribuicao_atual[nome] = selecionados

                            ################################################################################################
                            # FUNÇÕES AUXILIARES DE PLACAR (em memória)
                            ################################################################################################
                            def calcular_placar_projetos(distrib):
                                placar = {p: 0 for p in lista_projetos}
                                for projetos in distrib.values():
                                    for p in projetos:
                                        placar[p] += 1
                                return placar

                            def calcular_placar_pessoas(distrib):
                                return {
                                    nome: len(projetos)
                                    for nome, projetos in distrib.items()
                                }

                            ################################################################################################
                            # COLUNA 2 — PLACAR DE PROJETOS
                            ################################################################################################
                            with col2:
                                st.write("##### Avaliadores(as) por Projeto")

                                placar_projetos = calcular_placar_projetos(distribuicao_atual)

                                for codigo, total in placar_projetos.items():

                                    # Sempre cria 2 subcolunas por linha
                                    sub1, sub2 = st.columns([3, 1])

                                    # Código do projeto
                                    sub1.write(codigo)

                                    # Total de avaliadores
                                    sub2.write(str(total))



                            ################################################################################################
                            # COLUNA 3 — PLACAR DE AVALIADORES(AS)
                            ################################################################################################
                            with col3:
                                st.write("##### Projetos por Avaliador(a)")

                                placar_pessoas = calcular_placar_pessoas(distribuicao_atual)

                                # Ordena do maior para o menor
                                placar_ordenado = sorted(
                                    placar_pessoas.items(),
                                    key=lambda x: x[1],
                                    reverse=True
                                )

                                for nome, total in placar_ordenado:

                                    # Sempre cria 2 subcolunas por linha
                                    sub1, sub2 = st.columns([3, 1])

                                    # Nome da pessoa
                                    sub1.write(nome)

                                    # Total de projetos atribuídos
                                    sub2.write(str(total))






###########################################################################################################
# ABA CARREGAR
###########################################################################################################
with tabs[2]:

    if edital_selecionado_label == "":
        st.caption("Selecione um edital para carregar os dados.")
    else:
        edital = next(
            e for e in editais
            if f"{e['codigo_edital']} - {e['nome_edital']}" == edital_selecionado_label
        )

        codigo_edital = edital["codigo_edital"]

        if not edital.get("id_planilha_recebimento"):
            st.caption("Este edital não possui ID de planilha configurado.")
        else:
            # Contagem inicial
            total_inicial = db.projetos.count_documents(
                {"codigo_edital": codigo_edital}
            )

            # Inicializa estados
            if "total_projetos_exibido" not in st.session_state:
                st.session_state.total_projetos_exibido = total_inicial

            if "carregou_projetos" not in st.session_state:
                st.session_state.carregou_projetos = False

            # Botão
            label_botao = (
                "Atualizar projetos"
                if total_inicial > 0
                else "Carregar projetos"
            )

            if st.button(
                label_botao,
                icon=":material/download:",
                type="primary"
            ):
                df_recebidos_sheet = ler_planilha_google_sheets(
                    edital["id_planilha_recebimento"]
                )

                if df_recebidos_sheet.empty:
                    st.warning("A planilha não possui dados.")
                else:
                    adicionados = carregar_projetos(
                        df_recebidos_sheet,
                        db.projetos,
                        codigo_edital
                    )

                    # Atualiza contagem exibida
                    st.session_state.total_projetos_exibido = (
                        total_inicial + len(adicionados)
                    )

                    st.session_state.carregou_projetos = True

                    # Mensagens
                    if not adicionados:
                        st.success(
                            "Nenhum projeto novo foi encontrado na planilha.",
                            icon=":material/check:"
                        )
                    else:
                        st.success(
                            f"{str(len(adicionados))} projetos recebidos e cadastrados no sistema.",
                            icon=":material/check:"
                        )

                        st.write("Projetos adicionados:")
                        for i, codigo in enumerate(adicionados, start=1):
                            st.write(f"{i} - {codigo}")

            # EXIBE CONTAGEM (apenas uma vez)
            st.write(
                f"**{str(st.session_state.total_projetos_exibido)} "
                "projetos cadastrados neste edital.**"
            )


