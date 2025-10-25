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

class DebateRequest(BaseModel):
    problema: str
    contexto: str
    max_rodadas: int = 3
    debug_mode: bool = False

class DebateInfo(BaseModel):
    debate_id: str
    timestamp: str
    problema: str
    consenso: bool

class WebSocketEvent(BaseModel):
    """Modelo para eventos WebSocket."""
    event_type: str  # "debate.started", "round.start", "argument.new", "convergence.update", "debate.completed"
    debate_id: str
    data: dict

async def run_debate_background_ws(debate_id: str, problema: str, contexto: str, max_rodadas: int, debug_mode: bool):
    """Wrapper assíncrono para rodar o debate em segundo plano com eventos WebSocket."""
    print(f"Iniciando debate em background: {problema}")
    
    # Notifica início do debate
    await manager.broadcast(debate_id, {
        "event_type": "debate.started",
        "debate_id": debate_id,
        "data": {
            "problema": problema,
            "timestamp": datetime.now().isoformat(),
            "max_rodadas": max_rodadas,
            "debug_mode": debug_mode
        }
    })
    
    # Executa o debate (síncrono)
    # Nota: debate_saci_v2 ainda é síncrono. Idealmente, deveria ser refatorado para assíncrono
    # Por enquanto, executamos em thread separada para não bloquear o event loop
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await asyncio.get_event_loop().run_in_executor(
            executor,
            debate_saci_v2,
            problema,
            contexto,
            max_rodadas,
            True,  # verbose
            debug_mode
        )
    
    # Notifica conclusão do debate
    await manager.broadcast(debate_id, {
        "event_type": "debate.completed",
        "debate_id": debate_id,
        "data": {
            "problema": problema,
            "consenso": result if isinstance(result, bool) else True,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    print(f"Debate em background finalizado: {problema}")

@app.post("/debates", status_code=202)
async def create_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """
    Inicia um novo debate em segundo plano com suporte a WebSocket.
    Retorna o debate_id para que o cliente possa se conectar ao WebSocket.
    """
    # Gera um debate_id único baseado em timestamp
    import time
    debate_id = f"debate_{int(time.time())}"
    
    # Inicia debate em background com suporte a WebSocket
    background_tasks.add_task(
        run_debate_background_ws,
        debate_id,
        request.problema,
        request.contexto,
        request.max_rodadas,
        request.debug_mode
    )
    return {
        "message": "Debate iniciado em segundo plano. Conecte-se ao WebSocket para atualizações em tempo real.",
        "debate_id": debate_id,
        "websocket_url": f"/ws/debates/{debate_id}"
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
    log_files = glob.glob("logs/saci_v2_debate_*.json")
    debates = []
    # Ordenar por data de modificação para ter os mais recentes primeiro
    log_files.sort(key=os.path.getmtime, reverse=True)

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                debate_id = os.path.basename(log_file)
                
                # Extrai o problema diretamente do JSON (adicionado na v3.1)
                problema_completo = data.get('problema', '')
                if problema_completo:
                    # Trunca para 100 caracteres + reticências
                    problema_resumido = problema_completo[:100] + ('...' if len(problema_completo) > 100 else '')
                else:
                    # Fallback para debates antigos sem o campo 'problema'
                    problema_resumido = f"Debate {debate_id.split('_')[-1].split('.')[0]}"

                debates.append(DebateInfo(
                    debate_id=debate_id,
                    timestamp=data.get('timestamp', 'N/A'),
                    problema=problema_resumido,
                    consenso=data.get('consenso', False)
                ))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Erro ao processar o arquivo de log {log_file}: {e}")
            continue
    return debates

@app.get("/debates/{debate_id}")
async def get_debate_details(debate_id: str):
    """
    Retorna os detalhes completos de um debate específico.
    """
    # Sanitize input to prevent directory traversal
    if ".." in debate_id or "/" in debate_id or "\\" in debate_id:
        return {"error": "ID de debate inválido."}
        
    log_path = os.path.join("logs", debate_id)

    if not os.path.exists(log_path):
        return {"error": "Debate não encontrado."}

    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data
