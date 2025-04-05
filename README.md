# Cleandex - Índice de Confiabilidade de Dados

Este projeto permite analisar a qualidade de dados usando **FastAPI** para backend e **Streamlit** para frontend.

## 📂 Estrutura do Projeto

```
cleandex/
│── backend/                # API FastAPI
│   │── reports/            # Relatórios gerados
│   │── backend.py          # Código do backend
│   │── requirements.txt    # Dependências do backend
│
│── frontend/               # Dashboard Streamlit
│   │── frontend.py         # Código do frontend
│   │── requirements.txt    # Dependências do frontend
│
│── README.md               # Documentação
```

## 🚀 Como Rodar

### 1️⃣ Instalar dependências
```bash
cd backend
pip install -r requirements.txt

cd ../frontend
pip install -r requirements.txt
```

### 2️⃣ Rodar o Backend
```bash
cd backend
python backend.py
```

### 3️⃣ Rodar o Frontend
```bash
cd frontend
streamlit run frontend.py
```
