from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.lilly_agent import LillyAgent

app = FastAPI(title="Lilly Engine - Cognitive Layer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Modelo estricto de entrada
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"
    context: Optional[Dict[str, Any]] = None # El payload de Abu

@app.get("/")
def health_check():
    return {"status": "online", "service": "Lilly Swarm Cognitive Layer"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal de conversación.
    Recibe mensaje + contexto calculado (stateless request)
    Delega a LillyAgent (stateful logic)
    """
    try:
        # Instanciación efímera del agente (recupera estado de disco)
        agent = LillyAgent(session_id=request.session_id)
        
        response_text = agent.process_message(
            user_message=request.message,
            context=request.context
        )
        
        return {"response": response_text}
        
    except Exception as e:
        print(f"CRITICAL ERROR in /api/chat: {e}")
        raise HTTPException(status_code=500, detail="Internal Cognitive Error")