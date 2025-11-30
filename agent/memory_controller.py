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

    def delete(self, query_or_id, user="default"):
        """Delete memory entries.

        Tries to interpret `query_or_id` as an exact memory id first; if not,
        runs a search and attempts to delete matching results. The exact
        deletion API depends on the MemoryClient implementation; this method
        tries a few common names (`delete`, `remove`, `delete_memory`). If
        those are not present, it raises NotImplementedError with guidance.
        """
        # If the client exposes a direct delete method, try it.
        for method_name in ("delete", "remove", "delete_memory", "delete_by_id"):
            method = getattr(self.client, method_name, None)
            if callable(method):
                try:
                    return method(query_or_id, user_id=user)
                except TypeError:
                    # Some implementations expect only an id or different kwargs
                    try:
                        return method(query_or_id)
                    except Exception:
                        pass

        # Otherwise, attempt to search for matching entries and delete them by id
        results = self.client.search(query=query_or_id, user_id=user)
        deleted = []
        for r in results:
            # Many mem clients return dicts with an 'id' or 'memory_id'
            mem_id = None
            if isinstance(r, dict):
                mem_id = r.get("id") or r.get("memory_id") or r.get("_id")
            # If we found an id and client has a deletion method, try to delete
            if mem_id is not None:
                for method_name in ("delete", "remove", "delete_memory", "delete_by_id"):
                    method = getattr(self.client, method_name, None)
                    if callable(method):
                        try:
                            method(mem_id, user_id=user)
                            deleted.append(mem_id)
                            break
                        except Exception:
                            continue

        if deleted:
            return deleted

        raise NotImplementedError(
            "MemoryClient does not expose a supported delete API.\n"
            "Implement `delete` on your MemoryClient or update this adapter to match your client's API."
        )
