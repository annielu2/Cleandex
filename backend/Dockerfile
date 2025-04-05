# Usa uma imagem base do Python
FROM python:3.11

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos do backend para o container
COPY backend/ /app/
COPY ../requirements.txt /app/requirements.txt

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta usada pelo backend
EXPOSE 8503

# Comando para rodar o backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8503", "--reload"]
