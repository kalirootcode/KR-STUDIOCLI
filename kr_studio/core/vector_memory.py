"""VectorMemory reforzado con soporte multi-compartimentos.

Este módulo mantiene la compatibilidad con el API existente, pero añade la capacidad
de gestionar múltiples colecciones (compartimentos) y mantener aislamiento entre ellos.
"""

import chromadb
import logging
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Varias implementaciones de almacenamiento pueden usarse: Chromadb real o un fallback en memoria.
_classiller = None
"""Fallback in-memory Chromadb-like backend (used when Chromadb HTTP-only client fails)."""


class _FallbackCollection:
    def __init__(self, name):
        self.name = name
        self.items = []  # each: dict with id, embedding, document, metadata

    def upsert(self, ids, embeddings, documents, metadatas):
        for i, _id in enumerate(ids):
            # if exists, update; else append
            found = next((it for it in self.items if it["id"] == _id), None)
            entry = {
                "id": _id,
                "embedding": embeddings[i],
                "document": documents[i],
                "metadata": metadatas[i],
            }
            if found:
                self.items[self.items.index(found)] = entry
            else:
                self.items.append(entry)

    def count(self):
        return len(self.items)

    def get(self, limit=None, include=None):
        lim = 0 if limit is None else int(limit)
        subset = self.items[-lim:] if lim > 0 else []
        ids = [it["id"] for it in subset]
        docs = [it["document"] for it in subset]
        res = {"ids": ids, "documents": docs}
        if include and "metadatas" in include:
            res["metadatas"] = [it["metadata"] for it in subset]
        return res

    def delete(self, ids):
        self.items = [it for it in self.items if it["id"] not in set(ids)]

    def query(self, query_embeddings, n_results, include=None):
        # Very simple cosine-like similarity using dot product on flat vectors
        q = query_embeddings[0]

        def score(it):
            e = it["embedding"]
            # Avoid division by zero; small heuristic
            dot = sum(x * y for x, y in zip(q, e))
            return dot

        sorted_items = sorted(self.items, key=score, reverse=True)
        top = sorted_items[: int(n_results)]
        return {
            "ids": [it["id"] for it in top],
            "documents": [it["document"] for it in top],
        }


class _FallbackChromadbClient:
    def __init__(self, path):
        self.path = path
        self.collections = {}

    def get_or_create_collection(self, name):
        if name not in self.collections:
            self.collections[name] = _FallbackCollection(name)
        return self.collections[name]

    def delete_collection(self, name):
        if name in self.collections:
            del self.collections[name]


embedding_model = None
client = None


class VectorMemory:
    """Gestiona la memoria a largo plazo usando Chromadb en colecciones separadas."""

    DEFAULT_COMPARTMENTS = [
        "guion_director",
        "marketing",
        "opencode",
        "conocimiento_general",
    ]

    def __init__(
        self,
        db_path: str = "kr_studio_memory",
        compartments: Optional[List[str]] = None,
    ):
        """Inicializa la memoria vectorial con soporte multi-compartimentos.

        Args:
            db_path: Ruta local de Chromadb.
            compartments: Lista de nombres de compartimentos (colecciones).
        """
        self.compartment_names = compartments or self.DEFAULT_COMPARTMENTS
        self.collections = {}
        self.current_compartment: str = (
            self.compartment_names[0] if self.compartment_names else ""
        )
        try:
            # Cargar modelo de embeddings de forma singleton
            global embedding_model
            if embedding_model is None:
                embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

            # Cliente de Chromadb
            global client
            if client is None:
                client = chromadb.PersistentClient(path=db_path)
            # Crear o cargar colecciones para cada compartimento
            for name in self.compartment_names:
                col = client.get_or_create_collection(name=name)
                self.collections[name] = col
            logger.info(
                f"Memoria Vectorial lista con compartimentos: {self.compartment_names}"
            )
        except Exception as e:
            # Fall back to in-memory fake Chromadb if real client cannot start
            logger.warning(
                f"No se pudo inicializar Chromadb real: {e}. Usando backend en memoria."
            )
            client = _FallbackChromadbClient(path=db_path)
            for name in self.compartment_names:
                col = client.get_or_create_collection(name=name)
                self.collections[name] = col

    # Utilidad: obtener colección para un compartimento
    def _get_collection(self, compartment: Optional[str]):
        if compartment is None:
            compartment = self.current_compartment
        if compartment not in self.collections:
            # Crear dinámicamente si falta
            self.collections[compartment] = client.get_or_create_collection(
                name=compartment
            )
        return self.collections[compartment]

    def set_current_compartment(self, compartment: str):
        """Establece el compartimento actual para operaciones por defecto."""
        if compartment not in self.collections:
            self.collections[compartment] = client.get_or_create_collection(
                name=compartment
            )
        self.current_compartment = compartment

    def add_document(self, text: str, doc_id: str, compartment: Optional[str] = None):
        """Convierte un texto en vector y lo añade a la colección del compartimento actual."""
        if not text or not doc_id:
            logger.warning("Intento de añadir un documento vacío o sin ID.")
            return
        comp = compartment or self.current_compartment
        if comp is None:
            logger.error(
                "No se ha establecido un compartimento objetivo para add_document."
            )
            return
        try:
            collection = self._get_collection(comp)
            embedding = embedding_model.encode(text, convert_to_tensor=False).tolist()
            collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{"compartment": comp}],
            )
            logger.info(
                f"Documento '{doc_id}' añadido/actualizado en la memoria '{comp}'."
            )
        except Exception as e:
            logger.error(f"Error al añadir documento '{doc_id}': {e}")

    def get_all_documents(self) -> List[Dict]:
        """Devuelve todos los documentos de todos los compartimentos."""
        all_docs: List[Dict] = []
        try:
            for comp, collection in self.collections.items():
                count = collection.count()
                if count == 0:
                    continue
                results = collection.get(limit=count)
                texts = results.get("documents", [])
                ids = results.get("ids", [])
                for _id, doc in zip(ids, texts):
                    all_docs.append({"id": _id, "content": doc, "compartment": comp})
        except Exception as e:
            logger.error(f"Error al obtener documentos: {e}")
        return all_docs

    def clear_all(self):
        """Elimina TODOS los documentos de todas las colecciones."""
        try:
            global client
            for comp in list(self.collections.keys()):
                client.delete_collection(name=comp)
                self.collections[comp] = client.get_or_create_collection(name=comp)
            logger.info("Todas las colecciones han sido limpiadas.")
        except Exception as e:
            logger.error(f"Error al limpiar las colecciones: {e}")

    def search(
        self, query_text: str, n_results: int = 3, compartment: Optional[str] = None
    ) -> List[Dict]:
        """Busca documentos relevantes para la consulta dada.

        Si se especifica un compartimento, busca solo allí; si no, busca en todos.
        Devuelve una lista de documentos con id, content y compartment.
        """
        if not query_text:
            return []
        results_all: List[Dict] = []
        try:
            query_embedding = embedding_model.encode(
                query_text, convert_to_tensor=False
            ).tolist()
            target_comps = (
                [compartment] if compartment else list(self.collections.keys())
            )
            for comp in target_comps:
                collection = self._get_collection(comp)
                res = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    include=["documents", "distances"],
                )
                docs = res.get("documents", [[]])[0] or []
                ids = res.get("ids", [[]])[0] or []
                for _id, doc in zip(ids, docs):
                    results_all.append({"id": _id, "content": doc, "compartment": comp})
        except Exception as e:
            logger.error(f"Error durante la búsqueda en memoria: {e}")
        return results_all

    def delete_document(self, doc_id: str, compartment: Optional[str] = None):
        """Elimina un documento por ID en el compartimento especificado."""
        comp = compartment or self.current_compartment
        if comp is None:
            logger.error(
                "No se ha establecido un compartimento objetivo para delete_document."
            )
            return
        try:
            collection = self._get_collection(comp)
            collection.delete(ids=[doc_id])
            logger.info(f"Documento '{doc_id}' eliminado de la colección '{comp}'.")
        except Exception as e:
            logger.error(f"Error al eliminar documento '{doc_id}': {e}")

    def get_compartments(self) -> List[str]:
        """Devuelve la lista de compartimentos disponibles."""
        return list(self.collections.keys())

    def clear_compartment(self, compartment: str):
        """Limpia una colección/panel específica (compartimento)."""
        if compartment not in self.collections:
            self.collections[compartment] = client.get_or_create_collection(
                name=compartment
            )
        try:
            client.delete_collection(name=compartment)
        except Exception:
            # Si no existe, ignore
            pass
        # Recreate collection empty
        self.collections[compartment] = client.get_or_create_collection(
            name=compartment
        )
        logger.info(f"Colección '{compartment}' limpiada.")

    def get_documents_for_compartment(
        self, compartment: Optional[str] = None
    ) -> List[Dict]:
        """Devuelve documentos de un compartimento específico (o actual si None)."""
        comp = compartment or self.current_compartment
        if comp is None:
            return []
        collection = self._get_collection(comp)
        try:
            count = collection.count()
            if count == 0:
                return []
            results = collection.get(limit=count)
            docs = results.get("documents", [])
            ids = results.get("ids", [])
            return [
                {"id": _id, "content": doc, "compartment": comp}
                for _id, doc in zip(ids, docs)
            ]
        except Exception as e:
            logger.error(f"Error al obtener documentos del compartimento '{comp}': {e}")
            return []


if __name__ == "__main__":
    print("Ejecutando VectorMemory de prueba...")
    memory = VectorMemory(db_path="test_memory_db")
    memory.add_document(
        text="Ejemplo de guion sobre Nmap y técnicas de escaneo.",
        doc_id="guion_nmap_1",
        compartment="guion_director",
    )
    memory.set_current_compartment("marketing")
    memory.add_document(
        text="Plan de marketing para un curso de seguridad ofensiva.",
        doc_id="marketing_01",
        compartment=None,
    )
    print(memory.get_all_documents())
    print("Búsqueda de ejemplo:")
    print(memory.search("nmap guiones", n_results=2))
