import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
from urllib.parse import urlparse
import re

# Configuração da página
st.set_page_config(
    page_title="cleandex API Monitor",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL do backend
BACKEND_URL = "http://backend:8503/"

# Função para validar URLs
def is_valid_url(url):
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        return re.match(r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', url)
    except:
        return False

# Função para monitorar APIs
def monitor_apis(endpoints, timeout, expected_keys, auth_type, auth_config):
    # Pré-validação das URLs
    urls = [e.strip() for e in endpoints.split('\n') if e.strip()]
    invalid_urls = [url for url in urls if not is_valid_url(url)]
    
    if invalid_urls:
        raise ValueError(f"URLs inválidas: {', '.join(invalid_urls)}")

    payload = {
        "endpoints": urls,
        "timeout": timeout,
        "expected_format": [k.strip() for k in expected_keys.split(',') if k.strip()],
        "follow_redirects": True,
        "validate_ssl": True
    }
    
    if auth_type != "none":
        auth_payload = {"auth_type": auth_type}
        if auth_type == "api_key":
            auth_payload.update({
                "api_key": auth_config["api_key"],
                "api_key_header": auth_config.get("api_key_header", "X-API-KEY")
            })
        elif auth_type == "bearer":
            auth_payload.update({"bearer_token": auth_config["bearer_token"]})
        elif auth_type == "basic":
            auth_payload.update({
                "username": auth_config["username"],
                "password": auth_config["password"]
            })
        payload["auth"] = auth_payload
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/monitor/api",
            json=payload,
            timeout=timeout+5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Erro ao conectar com o backend: {str(e)}")

# Inicialização do estado da sessão
if 'monitoring_results' not in st.session_state:
    st.session_state.monitoring_results = None
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Dashboard"

# Sidebar - Navegação
with st.sidebar:
    st.title("🌐 API Monitoring")
    st.markdown("---")
    
    # Botões de navegação que atualizam o estado
    if st.button("📊 Dashboard", 
                use_container_width=True,
                disabled=(st.session_state.current_tab == "Dashboard")):
        st.session_state.current_tab = "Dashboard"
        st.rerun()
    
    if st.button("🔍 New Monitoring", 
                 use_container_width=True,
                 disabled=(st.session_state.current_tab == "Monitor APIs")):
        st.session_state.current_tab = "Monitor APIs"
        st.rerun()
    
    if st.button("📅 History", 
                 use_container_width=True,
                 disabled=(st.session_state.current_tab == "History")):
        st.session_state.current_tab = "History"
        st.rerun()
    
    st.markdown("---")
    st.caption("v2.1 | Sentinel Monitor")

# Páginas
if st.session_state.current_tab == "Dashboard":
    st.title("📊 API Monitoring Dashboard")
    
    if not st.session_state.monitoring_results:
        st.warning("No monitoring data available. Run a test first.")
        if st.button("Go to Monitoring"):
            st.session_state.current_tab = "Monitor APIs"
            st.rerun()
        st.stop()
    
    data = st.session_state.monitoring_results
    
    # Métricas principais
    cols = st.columns(4)
    metrics = [
        ("Overall Score", f"{data['overall_score']}/100", "#28a745"),
        ("Total Endpoints", data['stats']['total_endpoints'], "#007bff"),
        ("Successful", data['stats']['successful'], "#28a745"),
        ("Failed", data['stats']['failed'], "#dc3545")
    ]
    
    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.markdown(
                f"<h3 style='color: {color};'>{value}</h3><p>{label}</p>",
                unsafe_allow_html=True
            )
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Status Distribution")
        status_data = pd.DataFrame(data['results']['endpoints'])
        fig = px.pie(
            status_data,
            names="status",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Response Times")
        fig = px.bar(
            status_data,
            x="endpoint",
            y="response_time",
            labels={"endpoint": "Endpoint", "response_time": "Time (s)"},
            color="status",
            color_continuous_scale="Bluered"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de resultados
    st.subheader("Endpoint Details")
    df = pd.DataFrame(data['results']['endpoints'])
    df['Endpoint'] = df['endpoint'].apply(lambda x: x.split('/')[-1] or x.split('/')[-2])
    
    st.dataframe(
        df[['Endpoint', 'status', 'response_time', 'score', 'valid_format']].rename(columns={
            'status': 'Status',
            'response_time': 'Response Time (s)',
            'score': 'Score',
            'valid_format': 'Valid Format'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Detalhes expandidos
    st.subheader("Detailed Results")
    for endpoint in data['results']['endpoints']:
        with st.expander(f"{endpoint['endpoint']} - Status: {endpoint['status']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Response Time", f"{endpoint['response_time']:.3f}s")
                st.metric("Score", f"{endpoint['score']}/100")
                st.write(f"Valid Format: {'✅' if endpoint['valid_format'] else '❌'}")
            
            with col2:
                if endpoint['error']:
                    st.error(f"**Error:** {endpoint['error']}")
                if endpoint['warnings']:
                    for warning in endpoint['warnings']:
                        st.warning(f"**Warning:** {warning}")

elif st.session_state.current_tab == "Monitor APIs":
    st.title("🔍 New API Monitoring")
    
    with st.form("monitor_form"):
        # Seção de configuração
        st.subheader("API Configuration")
        endpoints = st.text_area(
            "API Endpoints",
            value="https://api.chucknorris.io/jokes/random\nhttps://jsonplaceholder.typicode.com/todos/1",
            placeholder="Enter one endpoint per line",
            height=120,
            help="Add one API endpoint per line. Must include http:// or https://"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            expected_keys = st.text_input(
                "Expected Response Keys",
                value="value,id,userId",
                placeholder="Comma-separated keys",
                help="Keys you expect to find in the JSON response"
            )
        with col2:
            timeout = st.number_input(
                "Timeout (seconds)",
                min_value=1,
                max_value=60,
                value=10,
                help="Maximum time to wait for each API response"
            )
        
        # Seção de autenticação
        st.subheader("Authentication")
        auth_type = st.selectbox(
            "Type",
            ["none", "api_key", "bearer", "basic"],
            index=0
        )
        
        auth_config = {}
        if auth_type == "api_key":
            auth_config["api_key"] = st.text_input("API Key", type="password")
            auth_config["api_key_header"] = st.text_input(
                "Header Name",
                value="X-API-KEY"
            )
        elif auth_type == "bearer":
            auth_config["bearer_token"] = st.text_input(
                "Bearer Token",
                type="password"
            )
        elif auth_type == "basic":
            auth_config["username"] = st.text_input("Username")
            auth_config["password"] = st.text_input(
                "Password",
                type="password"
            )
        
        # Botão de envio
        submitted = st.form_submit_button(
            "🚀 Run Monitoring Test",
            use_container_width=True
        )
        
        if submitted:
            status_msg = st.empty()
            with st.spinner('Running API tests...'):
                try:
                    results = monitor_apis(
                        endpoints=endpoints,
                        timeout=timeout,
                        expected_keys=expected_keys,
                        auth_type=auth_type,
                        auth_config=auth_config
                    )
                    
                    if results and 'results' in results:
                        st.session_state.monitoring_results = results
                        status_msg.success("✅ Monitoring completed successfully!")
                        time.sleep(1)
                        st.session_state.current_tab = "Dashboard"
                        st.rerun()
                    else:
                        status_msg.error("Invalid response format from backend")
                        st.json(results)  # Para debug
                
                except ValueError as e:
                    status_msg.error(f"Validation error: {str(e)}")
                except ConnectionError as e:
                    status_msg.error(f"Connection error: {str(e)}")
                except Exception as e:
                    status_msg.error(f"Unexpected error: {str(e)}")
                    st.exception(e)

elif st.session_state.current_tab == "History":
    st.title("📅 Monitoring History")
    st.warning("This feature is under development")
    st.info("""
    Planned features:
    - Historical performance trends
    - API availability over time
    - Response time history
    """)
    if st.button("Back to Dashboard"):
        st.session_state.current_tab = "Dashboard"
        st.rerun()

# Estilos CSS adicionais
st.markdown("""
<style>
    /* Botões da sidebar */
    .stButton>button {
        transition: all 0.3s ease;
        text-align: left;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .stButton>button:disabled {
        background-color: #f0f2f6;
        color: #2c3e50;
        border-left: 4px solid #4e73df;
    }
    
    /* Títulos */
    h1 {
        color: #2c3e50;
        border-bottom: 2px solid #4e73df;
        padding-bottom: 0.3rem;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)