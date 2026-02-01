
class EpisodicMemory:
    """Mock EpisodicMemory for now since it was referenced but not found."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memories = []

    def append(self, message: dict):
        self.memories.append(message)

    def retrieve(self, query: str, limit: int = 5):
        return self.memories[-limit:]
