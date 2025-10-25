"""
SACI v3.0 - Backend Server
==========================

Este servidor FastAPI expõe a funcionalidade da SACI v2.1 
através de uma API REST para ser consumida pela UI.
"""

import os
import json
import glob
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from saci.saci_v2 import debate_saci_v2

# Carrega variáveis do arquivo .env para garantir que as chaves estejam disponíveis
load_dotenv()

app = FastAPI(
    title="SACI v3.0 API",
    description="API para gerenciar e executar debates SACI.",
    version="3.0.0"
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

def run_debate_background(problema: str, contexto: str, max_rodadas: int, debug_mode: bool):
    """Wrapper para rodar o debate em segundo plano."""
    print(f"Iniciando debate em background: {problema}")
    debate_saci_v2(
        problema=problema,
        contexto=contexto,
        max_rodadas=max_rodadas,
        verbose=True,
        debug_mode=debug_mode
    )
    print(f"Debate em background finalizado: {problema}")

@app.post("/debates", status_code=202)
async def create_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """
    Inicia um novo debate em segundo plano.
    """
    background_tasks.add_task(
        run_debate_background,
        request.problema,
        request.contexto,
        request.max_rodadas,
        request.debug_mode
    )
    return {"message": "Debate iniciado em segundo plano. Monitore o histórico para ver o resultado."}

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
                
                # Extrai o problema do prompt da primeira rodada
                problema_resumido = "Problema não encontrado"
                if data.get('rodadas'):
                    respostas = data['rodadas'][0].get('respostas', {})
                    # Acessa a primeira resposta que tiver sucesso
                    primeira_resposta_valida = next((r for r in respostas.values() if r.get('success')), None)
                    # Esta parte é complexa pois o prompt não é salvo diretamente.
                    # Por simplicidade, vamos usar o nome do arquivo por enquanto.
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
