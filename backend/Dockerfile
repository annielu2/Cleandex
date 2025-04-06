FROM python:3.11

WORKDIR /app

# Copia os arquivos do backend
COPY . /app/
COPY ../requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8503

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8503", "--reload"]
