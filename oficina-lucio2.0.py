import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sistema Mecânica do Bigode", layout="centered", page_icon="🔧")

# 2. SISTEMA DE LOGIN (PROTEÇÃO PROFISSIONAL)
def check_password():
    def password_entered():
        # Dica: Use letras minúsculas para facilitar o login no celular
        if st.session_state["password"] == "bigode2026": 
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
    # AJUSTE 1: Deixamos a conexão limpa. O link deve ir preferencialmente no "Secrets" do Streamlit Cloud
    # Mas se quiser manter aqui, certifique-se de que a biblioteca está atualizada.
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Título Principal
    st.title("🔧 Mecânica do Bigode - Gestão")

    # Menu Lateral
        menu = st.sidebar.selectbox("Menu de Navegação", ["Novo Cadastro", "Histórico de O.S."])
    
       # --- LER DADOS DO GOOGLE SHEETS ---
    try:
        # A linha abaixo lê a planilha e cria a variável dados_atuais
        dados_atuais = conn.read(spreadsheet=st.secrets["spreadsheet_url"], worksheet="Página1", ttl=0)
    except Exception:
        # Se der erro na leitura, ele cria um banco de dados vazio para não travar
        dados_atuais = pd.DataFrame(columns=["O.S.", "Data", "Placa", "Cliente", "KM", "Serviço", "Valor"])
    if menu == "Novo Cadastro":
        st.header("📝 Abrir Nova Ordem de Serviço")
        
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
                nova_os = pd.DataFrame([{
                    "O.S.": f"{proxima_os_num:03d}",
                    "Data": data.strftime("%d/%m/%Y"),
                    "Placa": placa,
                    "Cliente": cliente,
                    "KM": km,
                    "Serviço": servico,
                    "Valor": str(valor) # Convertemos para string para manter padrão na planilha
                }])
    
                # AJUSTE 3: Comando de update revisado. 
                # É crucial passar o worksheet e a URL novamente no comando de escrita
                df_final = pd.concat([dados_atuais, nova_os], ignore_index=True)
                
                try:
                    conn.update(spreadsheet=st.secrets["spreadsheet_url"], worksheet="Página1", data=df_final)
                    st.success(f"✅ O.S. {proxima_os_num:03d} salva com sucesso!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
                    st.info("Dica: Verifique se os 'Secrets' no Streamlit Cloud possuem o link da planilha.")
            else:
                st.warning("⚠️ Por favor, preencha a Placa, o Cliente e o Serviço.")
    
    elif menu == "Histórico de O.S.":
        st.header("📊 Consulta de Serviços")
        df_historico = dados_atuais.copy()
        
        busca = st.text_input("🔍 Buscar pela Placa").upper().strip()
        if busca:
            df_historico = df_historico[df_historico['Placa'].str.contains(busca, na=False)]
    
        st.dataframe(df_historico, use_container_width=True)
        
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
