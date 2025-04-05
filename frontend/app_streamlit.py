import streamlit as st
import pandas as pd
import requests
import json

st.title("📊 Cleandex - Índice de Confiabilidade de Dados")
opcao = st.radio("Escolha a origem dos dados:", ["CSV", "Banco de Dados", "API"])

if opcao == "CSV":
    uploaded_file = st.file_uploader("Selecione um arquivo CSV", type=["csv"])
    if uploaded_file:
        files = {"file": ("arquivo.csv", uploaded_file.getvalue(), "text/csv")}
        response = requests.post("http://localhost:8503/analisar/", files=files)
        if response.status_code == 200:
            st.success("✅ Análise concluída!")
            link = response.json()["relatorio"]
            st.markdown(f"[📥 Baixar Relatório](http://localhost:8503{link})", unsafe_allow_html=True)
        else:
            st.error("❌ Erro ao processar o arquivo.")

elif opcao == "Banco de Dados":
    st.subheader("🔗 Conectar ao Banco de Dados")

    banco_tipo = st.selectbox("Selecione o banco de dados", ["PostgreSQL", "MySQL"])
    host = st.text_input("Host do banco de dados", "localhost")
    port = st.text_input("Porta", "5432" if banco_tipo == "PostgreSQL" else "3306")
    database = st.text_input("Nome do Banco de Dados")
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    query = st.text_area("Consulta SQL", "SELECT * FROM sua_tabela LIMIT 100")

    if st.button("Executar e Analisar"):
        if host and database and user and password and query:
            dados_conexao = {
                "banco_tipo": banco_tipo,
                "host": host,
                "port": port,
                "database": database,
                "user": user,
                "password": password,
                "query": query
            }

            response = requests.post("http://localhost:8503/analisar/banco/", json=dados_conexao)

            if response.status_code == 200:
                st.success("✅ Análise concluída!")
                link = response.json()["relatorio"]
                st.markdown(f"[📥 Baixar Relatório](http://localhost:8503{link})", unsafe_allow_html=True)
            else:
                st.error("❌ Erro ao processar os dados do banco de dados.")
        else:
            st.warning("⚠️ Preencha todos os campos antes de continuar!")

elif opcao == "API":
    url = st.text_input("URL da API (que retorna JSON)")
    if st.button("Buscar e Analisar"):
        try:
            res = requests.get(url)
            data = res.json()
            df = pd.DataFrame(data)
            response = requests.post(
                "http://localhost:8503/analisar/dataframe/",
                json=json.loads(df.to_json(orient="records"))
            )
            if response.status_code == 200:
                st.success("✅ Análise concluída!")
                link = response.json()["relatorio"]
                st.markdown(f"[📥 Baixar Relatório](http://localhost:8503{link})", unsafe_allow_html=True)
            else:
                st.error("❌ Erro ao processar os dados da API.")
        except Exception as e:
            st.error(f"Erro ao acessar a API: {e}")
