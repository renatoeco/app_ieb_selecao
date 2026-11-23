
import streamlit as st
import pandas as pd
from bson import ObjectId
from datetime import datetime
import re

from email.utils import parseaddr



from funcoes_auxiliares import (
    conectar_mongo_ieb_selecao,
    sincronizar_conversas_gmail,
    consultar_conversas_gmail,
    recuperar_anexo_gmail,
    enviar_email_gmail,
    responder_email_gmail
)






###########################################################################################################
# CONEXÃO COM O MONGODB
###########################################################################################################

db_ieb_selecao = conectar_mongo_ieb_selecao()
col_projetos = db_ieb_selecao["projetos"]
col_pessoas = db_ieb_selecao["pessoas"]

###########################################################################################################
# NAVEGAÇÃO
###########################################################################################################

st.logo("images/logo_selecao.png", size="large")

with st.sidebar:
    if st.button("Voltar para Projetos", icon=":material/arrow_back:"):
        st.session_state["pagina_atual"] = "ver_projetos"
        st.rerun()


###########################################################################################################
# FUNÇÕES AUXILIARES
###########################################################################################################


@st.dialog("Enviar mensagem", width="medium")
def dialog_enviar_mensagem(projeto_id, projeto):

    # Recupera o e-mail da organização e remove espaços externos.
    email_organizacao = str(
        projeto.get("E-mail da organização", "") or ""
    ).strip()

    with st.form("form_enviar_mensagem"):

        destinatarios_texto = st.text_input(
            "Destinatários (endereços separados por vírgula)",
            value=email_organizacao,
            placeholder="email1@exemplo.com, email2@exemplo.com"
        )

        assunto = st.text_input(
            "Assunto",
            placeholder="Informe o assunto do e-mail"
        )

        texto_mensagem = st.text_area(
            "Mensagem",
            height=200,
            placeholder="Digite a mensagem..."
        )

        enviar = st.form_submit_button(
            "Enviar mensagem",
            type="primary",
            icon=":material/mail:"
        )

    if enviar:

        # Separa os endereços, remove espaços externos e duplicidades.
        lista_destinatarios = list(dict.fromkeys(
            endereco.strip()
            for endereco in destinatarios_texto.split(",")
            if endereco.strip()
        ))

        # Recupera o identificador do usuário responsável pelo envio.
        autor_id = st.session_state.get("id_usuario")

        # Valida os campos obrigatórios.
        if not lista_destinatarios:
            st.error("Informe pelo menos um destinatário.")

        elif not assunto.strip():
            st.error("Informe o assunto da mensagem.")

        elif not texto_mensagem.strip():
            st.error("Escreva o conteúdo da mensagem.")

        elif autor_id is None:
            st.error("Não foi possível identificar o usuário logado.")

        else:

            # Verifica o formato dos endereços informados.
            emails_invalidos = [
                endereco
                for endereco in lista_destinatarios
                if not re.fullmatch(
                    r"[^@\s]+@[^@\s]+\.[^@\s]+",
                    endereco
                )
            ]

            if emails_invalidos:

                st.error(
                    "Verifique os seguintes endereços de e-mail: "
                    + ", ".join(emails_invalidos)
                )

            else:

                with st.spinner("Enviando e-mail, aguarde..."):

                    resultado = enviar_email_gmail(
                        projeto_id=projeto_id,
                        destinatarios=lista_destinatarios,
                        assunto=assunto.strip(),
                        mensagem=texto_mensagem,
                        autor_id=autor_id
                    )

                if resultado["sucesso"]:

                    st.toast(
                        "Mensagem enviada com sucesso!",
                        icon=":material/check_circle:"
                    )

                    st.rerun()


                elif resultado["enviado"] and not resultado["registrado"]:

                    st.warning(
                        "O e-mail foi enviado, mas não foi possível "
                        "registrar a conversa no sistema."
                    )

                    st.error(resultado["erro"])

                else:

                    st.error("Não foi possível enviar o e-mail.")
                    st.caption(resultado["erro"])






def preparar_anexo_callback(message_id, attachment_id, chave_anexo):
    """Recupera um anexo do Gmail e armazena o resultado na sessão."""

    chave_log = f"log_{chave_anexo}"

    st.session_state[chave_log] = [
        "Callback iniciado.",
        f"Message ID: {message_id}",
        f"Attachment ID: {attachment_id}"
    ]

    try:
        st.session_state[chave_log].append(
            "Executando recuperação do anexo."
        )

        resultado = recuperar_anexo_gmail(
            message_id,
            attachment_id
        )

        if resultado["sucesso"]:
            st.session_state[chave_anexo] = resultado["arquivo"]
            st.session_state[f"status_{chave_anexo}"] = "sucesso"

            st.session_state[chave_log].append(
                f"Arquivo armazenado: {len(resultado['arquivo'])} bytes."
            )

        else:
            st.session_state[f"status_{chave_anexo}"] = resultado["erro"]

            st.session_state[chave_log].append(
                f"Erro: {resultado['erro']}"
            )

    except Exception as erro:
        st.session_state[f"status_{chave_anexo}"] = str(erro)

        st.session_state[chave_log].append(
            f"Exceção: {type(erro).__name__}: {erro}"
        )





# def preparar_anexo_callback(message_id, attachment_id, chave_anexo):
#     """Recupera um anexo do Gmail e registra cada etapa da execução."""

#     chave_log = f"log_{chave_anexo}"

#     # Inicializa o registro de execução.
#     st.session_state[chave_log] = [
#         "Callback iniciado.",
#         f"Message ID recebido: {message_id}",
#         f"Attachment ID recebido: {attachment_id}"
#     ]

#     try:
#         st.session_state[chave_log].append(
#             "Chamando recuperar_anexo_gmail()."
#         )

#         resultado = recuperar_anexo_gmail(
#             message_id,
#             attachment_id
#         )

#         st.session_state[chave_log].append(
#             f"Retorno recebido: sucesso={resultado.get('sucesso')}"
#         )

#         if resultado["sucesso"]:
#             st.session_state[chave_anexo] = resultado["arquivo"]
#             st.session_state[f"status_{chave_anexo}"] = "sucesso"

#             st.session_state[chave_log].append(
#                 f"Arquivo armazenado: {len(resultado['arquivo'])} bytes."
#             )

#         else:
#             st.session_state[f"status_{chave_anexo}"] = resultado["erro"]

#             st.session_state[chave_log].append(
#                 f"Erro retornado pelo Gmail: {resultado['erro']}"
#             )

#     except Exception as erro:
#         st.session_state[f"status_{chave_anexo}"] = str(erro)

#         st.session_state[chave_log].append(
#             f"Exceção no callback: {type(erro).__name__}: {erro}"
#         )













###########################################################################################################
# IDENTIFICAÇÃO DO USUÁRIO
###########################################################################################################

# Recupera o identificador do usuário logado.
id_usuario = st.session_state.get("id_usuario")

if isinstance(id_usuario, str):
    resultado_id = re.search(r"[0-9a-fA-F]{24}", id_usuario)

    if resultado_id:
        id_usuario = ObjectId(resultado_id.group())
    else:
        id_usuario = None

tipo_usuario = st.session_state.get("tipo_usuario", "")


###########################################################################################################
# RECUPERAÇÃO DO PROJETO
###########################################################################################################

# Recupera os dados do projeto carregados no session_state.
projeto = st.session_state.get("projeto_atual")

if not projeto:

    st.warning("Nenhum projeto foi selecionado.")

else:

    ###########################################################################################################
    # IDENTIFICAÇÃO DO DOCUMENTO NO MONGODB
    ###########################################################################################################

    codigo_recebimento = projeto.get("codigo_recebimento")

    if not codigo_recebimento:

        st.error("Não foi possível identificar o código de recebimento do projeto.")

    else:

        # Localiza o documento no MongoDB utilizando o código de recebimento.
        documento_mongo = col_projetos.find_one(
            {"codigo_recebimento": codigo_recebimento},
            {"_id": 1}
        )

        if not documento_mongo:

            st.error("Projeto não encontrado no MongoDB.")

        else:

            # O identificador do MongoDB será utilizado nas operações seguintes.
            projeto_id = documento_mongo["_id"]


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
            # DIÁLOGO DE CADASTRO E EDIÇÃO DE ANOTAÇÕES
            ###########################################################################################################

            @st.dialog("Anotação", width="small")
            def dialog_anotacao(anotacao=None):

                editando = anotacao is not None

                id_anotacao = (
                    anotacao.get("_id_anotacao")
                    if editando else None
                )

                # Utiliza chaves independentes para os campos de cadastro e edição.
                chave_texto = (
                    f"campo_texto_anotacao_{id_anotacao}"
                    if editando else "campo_texto_anotacao_nova"
                )

                texto_atual = (
                    anotacao.get("texto_anotacao", "")
                    if editando else ""
                )

                texto = st.text_area(
                    "Texto da anotação",
                    value=texto_atual,
                    height=180,
                    key=chave_texto
                )

                if st.button(
                    "Salvar",
                    type="primary",
                ):

                    if not texto.strip():

                        st.warning("Informe o texto da anotação.")

                    elif not id_usuario:

                        st.error("Não foi possível identificar o usuário logado.")

                    else:

                        # Define os dados atualizados da anotação.
                        dados_anotacao = {
                            "texto_anotacao": texto.strip(),
                            "data_anotacao": datetime.now().strftime("%d/%m/%Y"),
                            "autor_anotacao": id_usuario
                        }

                        if editando:

                            # Restringe a edição ao administrador ou ao autor da anotação.
                            if tipo_usuario == "admin":

                                filtro_edicao = {
                                    "_id": projeto_id,
                                    "anotacoes._id_anotacao": id_anotacao
                                }

                            else:

                                filtro_edicao = {
                                    "_id": projeto_id,
                                    "anotacoes": {
                                        "$elemMatch": {
                                            "_id_anotacao": id_anotacao,
                                            "autor_anotacao": id_usuario
                                        }
                                    }
                                }

                            # Atualiza somente os campos da anotação selecionada.
                            resultado = col_projetos.update_one(
                                filtro_edicao,
                                {
                                    "$set": {
                                        "anotacoes.$.texto_anotacao": dados_anotacao["texto_anotacao"],
                                        "anotacoes.$.data_anotacao": dados_anotacao["data_anotacao"],
                                        "anotacoes.$.autor_anotacao": dados_anotacao["autor_anotacao"]
                                    }
                                }
                            )

                            if resultado.matched_count > 0:

                                st.toast(
                                    "Anotação atualizada com sucesso!",
                                    icon=":material/check_circle:"
                                )
                                st.rerun()

                            else:

                                st.error("Não foi possível atualizar a anotação. Verifique as permissões.")

                        else:

                            # Cria uma nova anotação com identificador próprio.
                            nova_anotacao = {
                                "_id_anotacao": ObjectId(),
                                **dados_anotacao
                            }

                            # Adiciona a anotação sem substituir os registros existentes.
                            resultado = col_projetos.update_one(
                                {"_id": projeto_id},
                                {
                                    "$push": {
                                        "anotacoes": nova_anotacao
                                    }
                                }
                            )

                            if resultado.modified_count > 0:

                                st.toast(
                                    "Anotação adicionada com sucesso!",
                                    icon=":material/check_circle:"
                                )
                                st.rerun()

                            else:

                                st.error("Não foi possível salvar a anotação.")


            ###########################################################################################################
            # DIÁLOGO DE CONFIRMAÇÃO DE EXCLUSÃO
            ###########################################################################################################

            @st.dialog("Excluir anotação", width="small")
            def dialog_excluir_anotacao(id_anotacao, autor_anotacao):

                st.write("Tem certeza?")

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "Sim, excluir",
                        type="primary",
                        width="stretch"
                    ):

                        # Restringe a exclusão ao administrador ou ao autor da anotação.
                        if tipo_usuario == "admin":

                            filtro_exclusao = {
                                "_id": projeto_id
                            }

                        else:

                            filtro_exclusao = {
                                "_id": projeto_id,
                                "anotacoes": {
                                    "$elemMatch": {
                                        "_id_anotacao": id_anotacao,
                                        "autor_anotacao": id_usuario
                                    }
                                }
                            }

                        # Remove exclusivamente a anotação selecionada.
                        resultado = col_projetos.update_one(
                            filtro_exclusao,
                            {
                                "$pull": {
                                    "anotacoes": {
                                        "_id_anotacao": id_anotacao
                                    }
                                }
                            }
                        )

                        if resultado.modified_count > 0:

                            st.toast(
                                "Anotação excluída com sucesso!",
                                icon=":material/check_circle:"
                            )
                            st.rerun()

                        else:

                            st.error("Não foi possível excluir a anotação.")

                with col2:

                    if st.button(
                        "Cancelar",
                        width="stretch"
                    ):
                        st.rerun()


            ###########################################################################################################
            # ABAS
            ###########################################################################################################

            aba_projeto, aba_anotacoes, aba_mensagens = st.tabs(
                [
                    ":material/description: Projeto",
                    ":material/edit_note: Anotações",
                    ":material/forum: Mensagens"
                ],
                key="abas_projeto",
                on_change="rerun"
            )





            ###########################################################################################################
            # ABA 1 - PROJETO
            ###########################################################################################################

            with aba_projeto:

                # Campos já apresentados no cabeçalho.
                campos_cabecalho = [
                    "codigo_recebimento",
                    "Sigla da organização",
                    "Nome da organização",
                    "Nome do projeto"
                ]

                # Exibe os demais campos carregados do Google Sheets.
                campos_projeto = [
                    (campo, valor)
                    for campo, valor in projeto.items()
                    if campo not in campos_cabecalho
                    and valor is not None
                    and str(valor).strip().lower() not in ["", "nan", "none"]
                ]

                for campo, valor in campos_projeto:
                    st.write(f"**{campo}**: {valor}")


            ###########################################################################################################
            # ABA 2 - ANOTAÇÕES
            ###########################################################################################################

            with aba_anotacoes:

                st.write('')

                # Botão para cadastrar uma nova anotação.
                with st.container(
                    horizontal=True,
                    horizontal_alignment="left"
                ):

                    if st.button(
                        "Nova anotação",
                        icon=":material/add:",
                        type="primary"
                    ):

                        # Limpa o conteúdo anterior do formulário de cadastro.
                        st.session_state.pop(
                            "campo_texto_anotacao_nova",
                            None
                        )

                        dialog_anotacao()


                st.write('')

                # Consulta somente as anotações do documento selecionado.
                documento_anotacoes = col_projetos.find_one(
                    {"_id": projeto_id},
                    {"anotacoes": 1}
                )

                anotacoes = (
                    documento_anotacoes.get("anotacoes", [])
                    if documento_anotacoes else []
                )

                # Apresenta as anotações mais recentes primeiro.
                anotacoes = list(reversed(anotacoes))

                if not anotacoes:

                    st.caption("Nenhuma anotação registrada para este projeto.")

                else:

                    # Recupera os nomes dos autores das anotações.
                    ids_autores = list({
                        anotacao.get("autor_anotacao")
                        for anotacao in anotacoes
                        if isinstance(anotacao.get("autor_anotacao"), ObjectId)
                    })

                    pessoas = col_pessoas.find(
                        {"_id": {"$in": ids_autores}},
                        {"nome_completo": 1}
                    )

                    nomes_autores = {
                        str(pessoa["_id"]): pessoa.get("nome_completo", "Usuário não identificado")
                        for pessoa in pessoas
                    }



                    for anotacao in anotacoes:

                        id_anotacao = anotacao.get("_id_anotacao")
                        texto_anotacao = anotacao.get("texto_anotacao", "")
                        data_anotacao = anotacao.get("data_anotacao", "")
                        autor_anotacao = anotacao.get("autor_anotacao")

                        # Normaliza o identificador do autor.
                        if isinstance(autor_anotacao, str):

                            resultado_autor = re.search(
                                r"[0-9a-fA-F]{24}",
                                autor_anotacao
                            )

                            if resultado_autor:
                                try:
                                    autor_anotacao = ObjectId(resultado_autor.group())
                                except Exception:
                                    autor_anotacao = None

                        nome_autor = nomes_autores.get(
                            str(autor_anotacao),
                            "Usuário não identificado"
                        )

                        # Verifica as permissões de edição e exclusão.
                        pode_editar = (
                            tipo_usuario == "admin"
                            or (
                                id_usuario is not None
                                and autor_anotacao == id_usuario
                            )
                        )





                        # Container individual da anotação.
                        with st.container(border=True):

                            # Primeira linha: texto da anotação.
                            st.write(texto_anotacao)

                            # Segunda linha: identificação do autor e ações disponíveis.
                            col1, col2 = st.columns(2)

                            with col1:
                                st.caption(f"{data_anotacao} - {nome_autor}")

                            with col2:

                                if pode_editar and id_anotacao is not None:

                                    with st.container(
                                        horizontal=True,
                                        horizontal_alignment="right",
                                        gap="small"
                                    ):

                                        if st.button(
                                            "Editar",
                                            icon=":material/edit:",
                                            key=f"editar_anotacao_{id_anotacao}",
                                            type="tertiary"
                                        ):

                                            # Prepara o formulário com o conteúdo atual.
                                            chave_texto = f"campo_texto_anotacao_{id_anotacao}"
                                            st.session_state[chave_texto] = texto_anotacao

                                            dialog_anotacao(anotacao)

                                        if st.button(
                                            "Excluir",
                                            icon=":material/delete:",
                                            key=f"excluir_anotacao_{id_anotacao}",
                                            type="tertiary"
                                        ):

                                            dialog_excluir_anotacao(
                                                id_anotacao,
                                                autor_anotacao
                                            )





            ###########################################################################################################
            # ABA 3 - MENSAGENS
            ###########################################################################################################

            if aba_mensagens.open:

                with aba_mensagens:

                    st.write('')

                    # Exibe o botão de envio somente para usuários que não são visitantes.
                    if st.session_state.get("tipo_usuario") != "visitante":

                        if st.button(
                            "Enviar mensagem",
                            icon=":material/mail:",
                            type="primary"
                        ):
                            dialog_enviar_mensagem(
                                projeto_id,
                                st.session_state.get("projeto_atual", {})
                            )

                    st.write('')

                    # Controla a sincronização inicial por projeto durante a sessão.
                    chave_sincronizacao = f"gmail_sincronizado_{projeto_id}"

                    if not st.session_state.get(chave_sincronizacao, False):

                        resultado_sync = sincronizar_conversas_gmail(projeto_id)

                        # Evita repetir a sincronização em atualizações da página.
                        st.session_state[chave_sincronizacao] = True

                        if not resultado_sync["sucesso"]:
                            for erro in resultado_sync["erros"]:
                                st.warning(erro)

                    # Recupera o conteúdo das conversas diretamente do Gmail.
                    resultado_consulta = consultar_conversas_gmail(projeto_id)

                    if not resultado_consulta["sucesso"]:

                        st.error(
                            "Não foi possível carregar as mensagens: "
                            + str(resultado_consulta["erro"])
                        )

                    elif not resultado_consulta["conversas"]:

                        st.info(
                            "Este projeto ainda não possui conversas registradas."
                        )

                    else:

                        email_organizacao = str(
                            projeto.get("E-mail da organização", "")
                        ).strip().lower()

                        # Exibe cada conversa em um container independente.
                        for conversa in resultado_consulta["conversas"]:

                            with st.container(border=True):

                                mensagens = conversa.get("mensagens", [])

                                assunto = (
                                    mensagens[0].get("assunto", "Conversa")
                                    if mensagens
                                    else "Conversa"
                                )

                                st.markdown(f"**{assunto}**")

                                st.caption(
                                    f"{len(mensagens)} "
                                    f"{'mensagem' if len(mensagens) == 1 else 'mensagens'}"
                                )

                                # Exibe as mensagens na ordem retornada pelo Gmail.
                                for mensagem in mensagens:

                                    remetente = parseaddr(
                                        mensagem.get("remetente", "")
                                    )[1].lower()

                                    # Identifica as mensagens enviadas pela organização.
                                    tipo_chat = (
                                        "user"
                                        if remetente == email_organizacao
                                        else "assistant"
                                    )

                                    with st.chat_message(tipo_chat):


                                        # Prioriza o nome do usuário registrado no MongoDB para a mensagem original.
                                        autor_exibicao = (
                                            mensagem.get("autor_nome")
                                            or mensagem.get("remetente", "")
                                        )

                                        st.markdown(f"**{autor_exibicao}**")

                                        # Exibe a data, a hora e todos os destinatários da mensagem.
                                        data_mensagem = mensagem.get("data_mensagem", "")
                                        destinatarios = mensagem.get("destinatarios", "")

                                        if destinatarios:
                                            st.caption(
                                                f"{data_mensagem} · Para: {destinatarios}"
                                            )
                                        else:
                                            st.caption(data_mensagem)



                                        # Exibe o conteúdo da mensagem conforme o formato retornado pelo Gmail.
                                        if mensagem.get("corpo"):

                                            if mensagem.get("tipo_conteudo") == "text/plain":

                                                # Preserva as quebras de linha do texto original.
                                                st.text(mensagem["corpo"])

                                            elif mensagem.get("tipo_conteudo") == "text/html":

                                                # Renderiza o conteúdo HTML original do e-mail.
                                                st.html(mensagem["corpo"])

                                        else:
                                            st.caption("Mensagem sem conteúdo textual.")






                                        anexos = mensagem.get("anexos", [])

                                        if anexos:

                                            for indice, anexo in enumerate(anexos):

                                                # A chave utiliza o projeto, a mensagem e a posição do anexo.
                                                chave_anexo = (
                                                    f"anexo_{projeto_id}_"
                                                    f"{mensagem['gmail_message_id']}_"
                                                    f"{indice}"
                                                )

                                                status_anexo = st.session_state.get(
                                                    f"status_{chave_anexo}"
                                                )

                                                arquivo_anexo = st.session_state.get(chave_anexo)

                                                # Organiza as informações e ações do anexo em quatro colunas.
                                                col1, col2, col3 = st.columns([1, 3, 2])

                                                with col1:
                                                    if indice == 0:
                                                        st.markdown("**Anexos:**")

                                                with col2:
                                                    tamanho = anexo.get("tamanho", 0)

                                                    if tamanho < 1024:
                                                        tamanho_formatado = f"{tamanho} B"
                                                    elif tamanho < 1024 * 1024:
                                                        tamanho_formatado = f"{tamanho / 1024:.1f} KB"
                                                    else:
                                                        tamanho_formatado = f"{tamanho / (1024 * 1024):.1f} MB"

                                                    st.markdown(
                                                        f"{anexo['nome']} ({tamanho_formatado})"
                                                    )

                                                with col3:

                                                    with st.container(horizontal="True", horizontal_alignment="right"):

                                                        st.button(
                                                            "Preparar download",
                                                            key=f"preparar_{chave_anexo}",
                                                            type="secondary",
                                                            on_click=preparar_anexo_callback,
                                                            args=(
                                                                mensagem["gmail_message_id"],
                                                                anexo["attachment_id"],
                                                                chave_anexo
                                                            )
                                                        )

                                                        if status_anexo == "sucesso" and arquivo_anexo is not None:

                                                            st.download_button(
                                                                label="Baixar anexo",
                                                                data=arquivo_anexo,
                                                                file_name=anexo["nome"],
                                                                mime=anexo["mime_type"],
                                                                key=f"download_{chave_anexo}",
                                                                type="primary"
                                                            )

                                                        elif status_anexo:
                                                            st.error(f"Erro: {status_anexo}")


                                # Permite responder somente a usuários que não são visitantes.
                                if st.session_state.get("tipo_usuario") != "visitante":

                                    # Formulário para responder à conversa existente.
                                    with st.form(
                                        key=f"form_resposta_{conversa['gmail_thread_id']}",
                                        border=False,
                                        clear_on_submit=True
                                    ):

                                        texto_resposta = st.text_area(
                                            "Responder à conversa",
                                            height=120,
                                            placeholder="Escreva sua resposta..."
                                        )

                                        enviar_resposta = st.form_submit_button(
                                            "Enviar e-mail",
                                            type="primary",
                                            icon=":material/mail:"
                                        )

                                    if enviar_resposta:

                                        autor_id = st.session_state.get("id_usuario")

                                        if not texto_resposta.strip():

                                            st.warning(
                                                "Escreva uma mensagem antes de enviar."
                                            )

                                        elif autor_id is None:

                                            st.error(
                                                "Não foi possível identificar o usuário logado."
                                            )

                                        else:

                                            # Envia a resposta na conversa existente.
                                            resultado_resposta = responder_email_gmail(
                                                projeto_id=projeto_id,
                                                thread_id=conversa["gmail_thread_id"],
                                                mensagem=texto_resposta,
                                                autor_id=autor_id
                                            )

                                            if resultado_resposta["sucesso"]:

                                                st.toast(
                                                    "Resposta enviada e registrada com sucesso!",
                                                    icon=":material/check_circle:"
                                                )

                                                st.rerun()

                                            elif (
                                                resultado_resposta["enviado"]
                                                and not resultado_resposta["registrado"]
                                            ):

                                                st.warning(
                                                    "A resposta foi enviada, mas não "
                                                    "foi possível registrar no sistema."
                                                )

                                                st.error(
                                                    resultado_resposta["erro"]
                                                )

                                            else:

                                                st.error(
                                                    "Não foi possível enviar a resposta."
                                                )

                                                st.caption(
                                                    resultado_resposta["erro"]
                                                )
