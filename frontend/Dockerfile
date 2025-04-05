# Usa uma imagem base do Python
FROM python:3.11

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos do frontend para o container
COPY frontend/ /app/
COPY ../requirements.txt /app/requirements.txt

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta usada pelo frontend
EXPOSE 8501

# Comando para rodar o frontend
CMD ["streamlit", "run", "app_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
