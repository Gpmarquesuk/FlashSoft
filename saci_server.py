"""
SACI v3.0 - Backend Server
==========================

Este servidor FastAPI expõe a funcionalidade da SACI v2.1 
através de uma API REST para ser consumida pela UI.
"""

import os
import json
import glob
import asyncio
from typing import List, Dict, Set
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from saci.saci_v2 import debate_saci_v2

# Carrega variáveis do arquivo .env para garantir que as chaves estejam disponíveis
load_dotenv()

# Sistema de gerenciamento de WebSockets
class ConnectionManager:
    """Gerencia conexões WebSocket para broadcasts de eventos de debates."""
    
    def __init__(self):
        # Dicionário de debate_id -> conjunto de WebSockets conectados
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, debate_id: str, websocket: WebSocket):
        """Registra nova conexão para um debate específico."""
        await websocket.accept()
        if debate_id not in self.active_connections:
            self.active_connections[debate_id] = set()
        self.active_connections[debate_id].add(websocket)
        print(f"[WS] Cliente conectado ao debate {debate_id}. Total: {len(self.active_connections[debate_id])}")
    
    def disconnect(self, debate_id: str, websocket: WebSocket):
        """Remove conexão de um debate."""
        if debate_id in self.active_connections:
            self.active_connections[debate_id].discard(websocket)
            print(f"[WS] Cliente desconectado do debate {debate_id}. Total: {len(self.active_connections[debate_id])}")
            
            # Remove o debate_id se não houver mais conexões
            if not self.active_connections[debate_id]:
                del self.active_connections[debate_id]
    
    async def broadcast(self, debate_id: str, message: dict):
        """Envia mensagem para todos os clientes conectados a um debate."""
        if debate_id not in self.active_connections:
            return
        
        # Lista de conexões mortas para remover
        dead_connections = []
        
        for websocket in self.active_connections[debate_id].copy():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"[WS] Erro ao enviar para cliente: {e}")
                dead_connections.append(websocket)
        
        # Remove conexões mortas
        for ws in dead_connections:
            self.disconnect(debate_id, ws)

manager = ConnectionManager()

app = FastAPI(
    title="SACI v3.1 API",
    description="API para gerenciar e executar debates SACI com atualizações em tempo real.",
    version="3.1.0"
)

# Configurar CORS para permitir requisições do Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens (para desenvolvimento)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP
    allow_headers=["*"],  # Permite todos os headers
)

class DebateRequest(BaseModel):
    problema: str
    contexto: str
    max_rodadas: int = 3
    debug_mode: bool = False

class DebateInfo(BaseModel):
    debate_id: str
    timestamp: float  # Alterado para float
    problema: str
    consenso: bool

class WebSocketEvent(BaseModel):
    """Modelo para eventos WebSocket."""
    event_type: str  # "debate.started", "round.start", "argument.new", "convergence.update", "debate.completed"
    debate_id: str
    data: dict

def run_debate_background(debate_id: str, problema: str, contexto: str, max_rodadas: int, debug_mode: bool, timestamp: datetime):
    """Executa o debate em background garantindo salvamento incremental."""
    print(f"[BACKEND] Iniciando debate: {problema[:50]}... (id={debate_id})")
    try:
        debate_saci_v2(
            debate_id=debate_id,  # agora sempre ID limpo (sem .json)
            problema=problema,
            contexto=contexto,
            max_rodadas=max_rodadas,
            verbose=True,
            debug_mode=debug_mode,
            timestamp=timestamp
        )
        print(f"[BACKEND] Debate finalizado com sucesso (id={debate_id})")
    except Exception as e:
        print(f"[BACKEND] ERRO no debate {debate_id}: {e}")
        import traceback
        traceback.print_exc()

@app.post("/debates", status_code=202)
async def create_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """
    Inicia um novo debate em segundo plano.
    """
    print(f"[API] Recebida requisição de debate: {request.problema[:50]}...")
    
    # Inicia debate em background
    # Gera um ID de debate único baseado no tempo para fácil rastreamento
    timestamp = datetime.now()
    debate_id = f"debate_{int(timestamp.timestamp())}"  # ID limpo
    
    # Cria arquivo de log IMEDIATAMENTE com estado inicial
    # para que a UI possa começar a acompanhar de cara
    log_filename = os.path.join("logs", f"{debate_id}.json")
    os.makedirs("logs", exist_ok=True)
    initial_state = {
        'consenso': None,
        'solucao_final': None,
        'rodadas': [],
        'rodada_atual': 0,
        'max_rodadas': request.max_rodadas,
        'timestamp': timestamp.timestamp(),
        'versao': '2.1',
        'debug_mode': request.debug_mode,
        'problema': request.problema,
        'contexto': request.contexto
    }
    try:
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump(initial_state, f, ensure_ascii=False, indent=2)
        print(f"[API] Estado inicial salvo: {log_filename}")
    except Exception as e:
        print(f"[API] ERRO ao salvar estado inicial: {e}")

    background_tasks.add_task(
        run_debate_background,
        debate_id,  # passa o ID limpo para ser usado consistentemente
        request.problema,
        request.contexto,
        request.max_rodadas,
        request.debug_mode,
        timestamp
    )
    
    return {
        "message": "Debate iniciado em segundo plano. Acompanhe ao vivo.",
        "debate_id": debate_id, # Retorna o ID limpo
        "status": "accepted"
    }

@app.websocket("/ws/debates/{debate_id}")
async def websocket_endpoint(websocket: WebSocket, debate_id: str):
    """
    Endpoint WebSocket para receber atualizações em tempo real de um debate.
    
    Eventos enviados:
    - debate.started: Debate foi iniciado
    - round.start: Nova rodada começou
    - argument.new: Novo argumento de modelo recebido
    - convergence.update: Atualização na métrica de convergência
    - debate.completed: Debate foi finalizado
    """
    await manager.connect(debate_id, websocket)
    try:
        # Mantém a conexão aberta e aguarda mensagens do cliente (se houver)
        while True:
            # Aguarda qualquer mensagem do cliente (pode ser usado para ping/pong)
            data = await websocket.receive_text()
            # Por enquanto, apenas respondemos com pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(debate_id, websocket)
        print(f"[WS] Cliente desconectou do debate {debate_id}")

@app.get("/debates", response_model=List[DebateInfo])
async def get_debates_history():
    """
    Retorna o histórico de debates concluídos.
    """
    # Aceita tanto o novo padrão (debate_*.json) quanto o legado (saci_v2_debate_*.json)
    log_files = glob.glob("logs/debate_*.json") + glob.glob("logs/saci_v2_debate_*.json")
    debates = []
    # Ordenar por data de modificação para ter os mais recentes primeiro
    log_files.sort(key=os.path.getmtime, reverse=True)

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                debate_filename = os.path.basename(log_file)
                debate_id = os.path.splitext(debate_filename)[0]  # remove .json para interface
                
                # Extrai o problema diretamente do JSON (adicionado na v3.1)
                problema_completo = data.get('problema', '')
                if problema_completo:
                    # Trunca para 100 caracteres + reticências
                    problema_resumido = problema_completo[:100] + ('...' if len(problema_completo) > 100 else '')
                else:
                    # Fallback para debates antigos sem o campo 'problema'
                    problema_resumido = f"Debate {debate_id.split('_')[-1]}"

                # Tenta obter o timestamp numérico. Se falhar, usa o tempo de modificação do arquivo.
                timestamp_val = data.get('timestamp')
                if not isinstance(timestamp_val, (int, float)):
                    timestamp_val = os.path.getmtime(log_file)

                debates.append(DebateInfo(
                    debate_id=debate_id,  # sem .json
                    timestamp=timestamp_val,
                    problema=problema_resumido,
                    consenso=data.get('consenso', False)
                ))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Erro ao processar o arquivo de log {log_file}: {e}")
            continue
    return debates

@app.get("/debates/{debate_id}/status")
async def get_debate_status_endpoint(debate_id: str):
    """
    Retorna o status atual de um debate (usado para polling pela UI).
    Este é um alias para /debates/{debate_id} para compatibilidade.
    """
    return await get_debate_details(debate_id)

@app.get("/debates/{debate_id}")
async def get_debate_details(debate_id: str):
    """
    Retorna os detalhes completos de um debate específico.
    """
    # Sanitize input to prevent directory traversal
    if ".." in debate_id or "/" in debate_id or "\\" in debate_id:
        return {"error": "ID de debate inválido."}
        
    log_path = os.path.join("logs", f"{debate_id}.json") # Adiciona a extensão .json

    if not os.path.exists(log_path):
        # Se o arquivo não existe, pode ser que o debate esteja em andamento mas ainda não salvou o primeiro estado.
        # Retornamos um status "iniciado" para a UI não quebrar.
        return {"status": "iniciado", "rodada_atual": 0, "rodadas": []}

    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data
