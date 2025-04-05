import io
import os
import time
import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from ydata_profiling import ProfileReport
import uvicorn

# Criando a API
app = FastAPI()

# Criar diretório para relatórios, se não existir
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

@app.post("/analisar/")
async def analisar_dados(file: UploadFile = File(...)):
    """Recebe um arquivo CSV e gera um relatório de análise de dados."""
    async with file as f:
        contents = await f.read()
    df = pd.read_csv(io.BytesIO(contents))

    # Gerar relatório
    profile = ProfileReport(df, minimal=True)
    safe_filename = file.filename.replace(" ", "_").replace("/", "_")
    report_path = os.path.join(REPORTS_DIR, f"relatorio_{safe_filename}.html")
    profile.to_file(report_path)

    return {"mensagem": "Análise concluída", "relatorio": f"/baixar/{safe_filename}"}

@app.post("/analisar/dataframe/")
async def analisar_dataframe(data: dict[str, list]):
    """Recebe um JSON no formato de DataFrame e gera um relatório de análise de dados."""
    df = pd.DataFrame(data)
    timestamp = int(time.time())

    # Gerar relatório
    report_path = os.path.join(REPORTS_DIR, f"relatorio_{timestamp}.html")
    profile = ProfileReport(df, minimal=True)
    profile.to_file(report_path)

    return {"mensagem": "Análise concluída", "relatorio": f"/baixar/{timestamp}"}

@app.get("/baixar/{filename}")
async def baixar_relatorio(filename: str):
    """Faz o download de um relatório gerado."""
    file_path = os.path.join(REPORTS_DIR, f"relatorio_{filename}.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(file_path, filename=f"relatorio_{filename}.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8503)
