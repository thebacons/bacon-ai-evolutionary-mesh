import os
import logging
from typing import List, Dict, Any, Optional
from mem0 import MemoryClient

logger = logging.getLogger("bacon-memory-gateway")

class MemoryGateway:
    def __init__(self, user_id: str = "bacon-system"):
        # Initialize Mem0 in Cloud mode using the dedicated MemoryClient.
        # This bypasses local OpenAI and Vector DB checks.
        api_key = os.environ.get("MEM0_API_KEY")
        if api_key:
            self.client = MemoryClient(api_key=api_key)
        else:
            logger.error("MEM0_API_KEY not found. Cloud memory operations will fail.")
            self.client = None
        self.user_id = user_id

    def learn(self, text: str, agent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Record a memory for a specific agent or the system."""
        if not self.client:
            return None
        user_id = agent_id or self.user_id
        try:
            return self.client.add(text, user_id=user_id, metadata=metadata)
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return None

    def recall(self, query: str, agent_id: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for a query."""
        if not self.client:
            return []
        user_id = agent_id or self.user_id
        try:
            return self.client.search(query, user_id=user_id, limit=limit)
        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return []

    def get_all(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all memories for a specific agent. fallbacks to search if get_all is restricted."""
        if not self.client:
            return []
        user_id = agent_id or self.user_id
        try:
            # For Mem0 Cloud, search with empty query often works better if filters are required
            return self.client.get_all(user_id=user_id)
        except Exception as e:
            logger.warning(f"get_all failed, trying search fallback: {e}")
            try:
                return self.client.search("", user_id=user_id, limit=100)
            except Exception as e2:
                logger.error(f"Memory retrieval failed completely: {e2}")
                return []
