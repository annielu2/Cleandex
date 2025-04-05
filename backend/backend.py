import io
import os
import time
import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from ydata_profiling import ProfileReport
import uvicorn

# Criando a API
app = FastAPI()

# Criar diretório para relatórios
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

@app.post("/analisar/")
async def analisar_dados(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    profile = ProfileReport(df, minimal=True)
    report_path = os.path.join(REPORTS_DIR, f"relatorio_{file.filename}.html")
    profile.to_file(report_path)
    return {"mensagem": "Análise concluída", "relatorio": f"/baixar/{file.filename}"}

@app.post("/analisar/dataframe/")
async def analisar_dataframe(data: dict):
    df = pd.DataFrame(data)
    timestamp = int(time.time())
    report_path = os.path.join(REPORTS_DIR, f"relatorio_{timestamp}.html")
    profile = ProfileReport(df, minimal=True)
    profile.to_file(report_path)
    return {"mensagem": "Análise concluída", "relatorio": f"/baixar/{timestamp}"}

@app.get("/baixar/{filename}")
async def baixar_relatorio(filename: str):
    file_path = os.path.join(REPORTS_DIR, f"relatorio_{filename}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"relatorio_{filename}.html")
    return {"erro": "Arquivo não encontrado"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8503)
