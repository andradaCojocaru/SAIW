from mem0 import MemoryClient

class StressMemory:
    """Memorie persistentă pentru jurnal emoțional"""

    def __init__(self):
        self.client = MemoryClient()

    def save(self, text, user="default"):
        """
        Salvează o intrare în memorie.
        `messages` trebuie să fie o listă de dict-uri conform mem0ai API.
        """
        # Convertim text simplu într-un message
        message = {"role": "user", "content": text}
        return self.client.add(messages=[message], user_id=user)

    def search(self, query, user="default"):
        """Caută intrări similare"""
        return self.client.search(
            query=query,
            user_id=user,
            filters={
                "AND": [
                    {"user_id": user}
                ]
            }
        )


    def all_memories(self, user="default"):
        """Returnează toate intrările din memorie"""
        return self.client.get_all(user_id=user)
