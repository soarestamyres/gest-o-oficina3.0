import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sistema Mecânica do Bigode", layout="centered", page_icon="🔧")

# 2. SISTEMA DE LOGIN (PROTEÇÃO PROFISSIONAL)
def check_password():
    def password_entered():
        if st.session_state["password"] == "bigode2026": # SENHA DE ACESSO
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Acesso Restrito")
        st.text_input("Digite a senha da oficina", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Senha incorreta. Tente novamente:", type="password", on_change=password_entered, key="password")
        st.error("😕 Senha inválida.")
        return False
    else:
        return True

# SÓ EXECUTA O SISTEMA SE A SENHA ESTIVER CORRETA
if check_password():
    
    # 3. CONEXÃO COM O GOOGLE SHEETS
    # Usamos st.connection para integrar com a planilha do Google
    conn = st.connection("gsheets", type="gsheets", spreadsheet="https://docs.google.com/spreadsheets/d/16miIATA1kuth-RpfA9s7wGMf7r02ZXFScOwYYLj2o2k/edit?usp=sharing")

    # Título Principal
    st.title("🔧 Mecânica do Bigode - Gestão")

    # Menu Lateral
    menu = st.sidebar.selectbox("Menu de Navegação", ["Novo Cadastro", "Histórico de O.S."])

    # --- LER DADOS DO GOOGLE SHEETS ---
    try:
        # ttl=0 é fundamental para que o Streamlit não guarde dados antigos em cache
        dados_atuais = conn.read(ttl=0)
    except Exception:
        # Caso a planilha esteja vazia ou ocorra erro de conexão inicial, criamos a estrutura
        dados_atuais = pd.DataFrame(columns=["O.S.", "Data", "Placa", "Cliente", "KM", "Serviço", "Valor"])

    if menu == "Novo Cadastro":
        st.header("📝 Abrir Nova Ordem de Serviço")
        
        # Sugestão do número da próxima O.S. baseada na quantidade de linhas
        proxima_os_num = len(dados_atuais) + 1
        st.info(f"Número da Próxima O.S.: {proxima_os_num:03d}")

        with st.form("form_oficina", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                placa = st.text_input("Placa do Veículo").upper().strip()
                cliente = st.text_input("Nome do Cliente")
            with col2:
                data = st.date_input("Data do Serviço", datetime.now())
                km = st.text_input("Quilometragem (KM)")

            servico = st.text_area("Descrição Detalhada do Serviço e Peças")
            valor = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
            
            btn_salvar = st.form_submit_button("Finalizar e Salvar na Nuvem")

        if btn_salvar:
            if placa and cliente and servico:
                # Criando a nova linha de dados
                nova_os = pd.DataFrame([{
                    "O.S.": f"{proxima_os_num:03d}",
                    "Data": data.strftime("%d/%m/%Y"),
                    "Placa": placa,
                    "Cliente": cliente,
                    "KM": km,
                    "Serviço": servico,
                    "Valor": valor
                }])

                # Concatena os dados antigos com o novo registro
                # Convertemos para string para evitar conflitos de tipos no Google Sheets
                df_final = pd.concat([dados_atuais, nova_os], ignore_index=True).astype(str)
                
                # Envia a atualização para o Google Sheets
                conn.update(data=df_final)
                
                st.success(f"✅ O.S. {proxima_os_num:03d} salva com sucesso!")
                st.balloons()
                
                # Recarrega a página para atualizar o contador e limpar campos
                st.rerun()
            else:
                st.warning("⚠️ Por favor, preencha a Placa, o Cliente e o Serviço.")

    elif menu == "Histórico de O.S.":
        st.header("📊 Consulta de Serviços")
        
        # Criamos uma cópia para aplicar os filtros de busca sem alterar o original
        df_historico = dados_atuais.copy()
        
        # Filtro de busca por placa
        busca = st.text_input("🔍 Buscar pela Placa").upper().strip()
        if busca:
            # Filtra garantindo que não dê erro com valores vazios (na=False)
            df_historico = df_historico[df_historico['Placa'].str.contains(busca, na=False)]

        # Exibe a tabela formatada
        st.dataframe(df_historico, use_container_width=True)
        
        # Opção de Download para Backup local em CSV
        csv = df_historico.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Backup (CSV)",
            data=csv,
            file_name=f'backup_bigode_{datetime.now().strftime("%d_%m_%Y")}.csv',
            mime='text/csv',
        )

# RODAPÉ - SIDEBAR
st.sidebar.markdown("---")
st.sidebar.write("💻 Desenvolvido por Tamyres Monteiro")
st.sidebar.caption("Projeto Voluntário - Faculdade")
