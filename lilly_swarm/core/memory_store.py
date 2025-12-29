import os
import json
import time
from typing import List, Dict

DATA_DIR = "data/threads"
os.makedirs(DATA_DIR, exist_ok=True)

class MemoryStore:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.file_path = os.path.join(DATA_DIR, f"{session_id}.json")

    def load_history(self) -> List[Dict[str, str]]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("messages", [])
            except Exception:
                return []
        return []

    def save_message(self, role: str, content: str):
        history = self.load_history()
        history.append({"role": role, "content": content})
        
        # Política de rotación básica (configurable)
        if len(history) > 30: 
            history = history[-30:]

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": self.session_id,
                "last_updated": time.time(),
                "messages": history
            }, f, ensure_ascii=False, indent=2)
            
    def get_context_window(self, limit: int = 10) -> List[Dict[str, str]]:
        """Devuelve solo los últimos N mensajes para el prompt."""
        return self.load_history()[-limit:]