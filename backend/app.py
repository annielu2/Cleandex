import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import logging
import uvicorn
from enum import Enum

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Sentinel",
    description="Specialized API monitoring tool for public and private endpoints",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums para tipos de autenticação
class AuthType(str, Enum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"

# Modelos Pydantic
class AuthConfig(BaseModel):
    auth_type: AuthType = AuthType.NONE
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None  # Para OAuth2
    client_secret: Optional[str] = None  # Para OAuth2

class APIMonitorRequest(BaseModel):
    endpoints: List[str]
    expected_format: Optional[List[str]] = None
    timeout: Optional[int] = 10
    auth: Optional[AuthConfig] = None
    follow_redirects: Optional[bool] = True
    validate_ssl: Optional[bool] = True

class APIValidationResult(BaseModel):
    endpoint: str
    status: int
    response_time: float
    valid_format: bool
    headers: Dict[str, str]
    score: int
    error: Optional[str] = None
    warnings: List[str] = []

class MonitorResponse(BaseModel):
    success: bool
    results: Dict[str, Any]
    overall_score: float
    execution_time: float
    stats: Dict[str, float]

# Variáveis globais
START_TIME = time.time()

def calculate_api_score(status: int, response_time: float, valid_format: bool) -> int:
    """Calcula score de confiabilidade com pesos ajustados"""
    score = 0
    
    # Disponibilidade (50% do score)
    if status == 200:
        score += 50
    elif 200 <= status < 300:
        score += 40
    elif status == 401:
        score += 10  # Pelo menos a API respondeu
    
    # Performance (30% do score)
    if response_time < 0.5:
        score += 30
    elif response_time < 1:
        score += 20
    elif response_time < 2:
        score += 10
    
    # Consistência (20% do score)
    if valid_format:
        score += 20
    
    return min(100, score)  # Cap at 100

def prepare_headers(auth: Optional[AuthConfig]) -> Dict[str, str]:
    """Prepara headers de autenticação"""
    headers = {}
    if not auth:
        return headers
    
    if auth.auth_type == AuthType.API_KEY and auth.api_key:
        headers["X-API-KEY"] = auth.api_key
    elif auth.auth_type == AuthType.BEARER and auth.bearer_token:
        headers["Authorization"] = f"Bearer {auth.bearer_token}"
    elif auth.auth_type == AuthType.BASIC and auth.username and auth.password:
        import base64
        credentials = f"{auth.username}:{auth.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers["Authorization"] = f"Basic {encoded}"
    
    return headers

@app.get("/", include_in_schema=False)
async def health_check():
    """Endpoint básico de verificação de saúde"""
    return {
        "status": "operational",
        "version": app.version,
        "uptime": round(time.time() - START_TIME, 2),
        "services": ["API Monitoring"]
    }

@app.post("/monitor/api", response_model=MonitorResponse)
async def monitor_api(api_request: APIMonitorRequest):
    """
    Monitora e valida endpoints de API com métricas avançadas
    
    Parâmetros:
    - endpoints: Lista de URLs para monitorar
    - expected_format: Chaves esperadas no JSON de resposta
    - timeout: Tempo máximo de espera por resposta
    - auth: Configuração de autenticação
    - follow_redirects: Seguir redirecionamentos HTTP
    - validate_ssl: Validar certificados SSL
    
    Retorna:
    - Score individual por endpoint
    - Score geral
    - Métricas detalhadas
    - Estatísticas consolidadas
    """
    start_time = time.time()
    results = []
    total_score = 0
    stats = {
        'total_endpoints': len(api_request.endpoints),
        'successful': 0,
        'failed': 0,
        'avg_response_time': 0
    }

    for endpoint in api_request.endpoints:
        endpoint_start = time.time()
        warnings = []
        try:
            headers = prepare_headers(api_request.auth)
            
            response = requests.request(
                "GET",
                endpoint,
                headers=headers,
                timeout=api_request.timeout,
                allow_redirects=api_request.follow_redirects,
                verify=api_request.validate_ssl
            )
            
            response_time = time.time() - endpoint_start
            status = response.status_code
            valid_format = True

            # Validação de formato se especificado
            if api_request.expected_format:
                try:
                    json_data = response.json()
                    missing_keys = [
                        key for key in api_request.expected_format 
                        if key not in json_data
                    ]
                    if missing_keys:
                        valid_format = False
                        warnings.append(f"Missing keys: {', '.join(missing_keys)}")
                except ValueError:
                    valid_format = False
                    warnings.append("Invalid JSON response")

            # Verificação de headers importantes
            if 'X-RateLimit-Limit' in response.headers:
                warnings.append(
                    f"Rate limit: {response.headers['X-RateLimit-Remaining']}/{response.headers['X-RateLimit-Limit']}"
                )

            score = calculate_api_score(status, response_time, valid_format)
            total_score += score
            stats['successful'] += 1
            stats['avg_response_time'] += response_time

            results.append(APIValidationResult(
                endpoint=endpoint,
                status=status,
                response_time=round(response_time, 4),
                valid_format=valid_format,
                headers=dict(response.headers),
                score=score,
                warnings=warnings
            ))

        except requests.exceptions.SSLError as e:
            error_msg = "SSL Certificate verification failed"
            logger.warning(f"{error_msg} for {endpoint}: {str(e)}")
            results.append(APIValidationResult(
                endpoint=endpoint,
                status=0,
                response_time=0,
                valid_format=False,
                headers={},
                score=0,
                error=error_msg,
                warnings=["Try disabling SSL validation if testing internally"]
            ))
            stats['failed'] += 1
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API Monitoring failed for {endpoint}: {str(e)}")
            results.append(APIValidationResult(
                endpoint=endpoint,
                status=0,
                response_time=0,
                valid_format=False,
                headers={},
                score=0,
                error=str(e),
                warnings=[]
            ))
            stats['failed'] += 1

    # Calcula estatísticas finais
    if stats['successful'] > 0:
        stats['avg_response_time'] = round(stats['avg_response_time'] / stats['successful'], 4)
    else:
        stats['avg_response_time'] = 0
    
    avg_score = total_score / len(api_request.endpoints) if api_request.endpoints else 0

    return MonitorResponse(
        success=avg_score > 70,  # Threshold mais rigoroso
        results={"endpoints": results},
        overall_score=round(avg_score, 2),
        execution_time=round(time.time() - start_time, 4),
        stats=stats
    )

if __name__ == "__main__":
    uvicorn.run(
        "app:app", 
        host="0.0.0.0",
        port=8503,
        log_level="info",
        reload=True
    )