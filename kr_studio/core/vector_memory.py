"""VectorMemory reforzado con soporte multi-compartimentos.

Este módulo mantiene la compatibilidad con el API existente, pero añade la capacidad
de gestionar múltiples colecciones (compartimentos) y mantener aislamiento entre ellos.
"""

import chromadb
import logging
import json
import os
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
        auto_load: bool = True,
    ):
        """Inicializa la memoria vectorial con soporte multi-compartimentos.

        Args:
            db_path: Ruta local de Chromadb.
            compartments: Lista de nombres de compartimentos (colecciones).
            auto_load: Si True, carga automáticamente archivos .md de la carpeta knowledge.
        """
        self.compartment_names = compartments or self.DEFAULT_COMPARTMENTS
        self.collections = {}
        self.current_compartment: str = (
            self.compartment_names[0] if self.compartment_names else ""
        )
        self._force_reload = False

        # Añadir compartimentos adicionales para los documentos
        additional_compartments = ["conocimiento", "plantillas", "cursos", "series"]
        for comp in additional_compartments:
            if comp not in self.compartment_names:
                self.compartment_names.append(comp)

        try:
            # Cliente de Chromadb primero (sin modelo aún)
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

            # Carga automática de documentos .md (solo si hay datos en Chromadb o es primera vez)
            if auto_load:
                self.auto_load_knowledge()

        except Exception as e:
            # Fall back to in-memory fake Chromadb if real client cannot start
            logger.warning(
                f"No se pudo inicializar Chromadb real: {e}. Usando backend en memoria."
            )
            client = _FallbackChromadbClient(path=db_path)
            for name in self.compartment_names:
                col = client.get_or_create_collection(name=name)
                self.collections[name] = col

            # Intentar carga automática aunque sea con fallback
            if auto_load:
                try:
                    self.auto_load_knowledge()
                except Exception as load_err:
                    logger.warning(
                        f"No se pudo cargar conocimiento automáticamente: {load_err}"
                    )
                col = client.get_or_create_collection(name=name)
                self.collections[name] = col

            # Intentar carga automática aunque sea con fallback
            if auto_load:
                try:
                    self.auto_load_knowledge()
                except Exception as load_err:
                    logger.warning(
                        f"No se pudo cargar conocimiento automáticamente: {load_err}"
                    )

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

    def _ensure_model(self):
        """Carga el modelo de embeddings solo cuando se necesita (lazy loading)."""
        global embedding_model
        if embedding_model is None:
            logger.info("Cargando modelo de embeddings...")
            embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Modelo de embeddings cargado.")

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
            self._ensure_model()
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
            self._ensure_model()
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

    # ─────────────────────────────────────────────────────────────
    # CARGA AUTOMÁTICA INTELIGENTE DE DOCUMENTOS .md
    # Sistema de metadata para persistencia y carga eficiente
    # ─────────────────────────────────────────────────────────────

    COMPARTMENT_KEYWORDS = {
        "marketing": [
            "marketing",
            "viral",
            "promo",
            "venta",
            "hotmart",
            "udemy",
            "curso",
            "estrategia",
            "audiencia",
            "repurposing",
            "promocion",
            "funnel",
            "leads",
            "conversion",
        ],
        "conocimiento_general": [
            "shell",
            "linux",
            "nmap",
            "hack",
            "pentest",
            "security",
            "python",
            "script",
            "terminal",
            "comando",
            "bash",
            "kernel",
            "redes",
            "servidor",
            "docker",
            "kubernetes",
            "git",
            "code",
        ],
        "guion_director": [
            "guion",
            "script",
            "video",
            "narracion",
            "voiceover",
            "guionizacion",
        ],
        "plantillas": ["plantilla", "template", "formato", "estructura"],
        "opencode": ["opencode", "claude", "ai", "prompt", "agent", "llm", "modelo"],
    }

    _instance_metadata: Dict = {}

    def _get_metadata_path(self, knowledge_path: str) -> str:
        """Retorna la ruta del archivo de metadata."""
        return os.path.join(knowledge_path, ".knowledge_metadata.json")

    def _load_metadata(self, knowledge_path: str) -> Dict:
        """Carga el archivo de metadata (cache de archivos ya cargados)."""
        metadata_path = self._get_metadata_path(knowledge_path)

        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error leyendo metadata: {e}")

        return {}

    def _save_metadata(self, knowledge_path: str, metadata: Dict):
        """Guarda el archivo de metadata."""
        metadata_path = self._get_metadata_path(knowledge_path)
        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Error guardando metadata: {e}")

    def _detectar_compartimento(self, filename: str) -> str:
        """Detecta el compartimento basado en palabras clave del nombre del archivo."""
        filename_lower = filename.lower()

        for compartment, keywords in self.COMPARTMENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return compartment

        return "conocimiento_general"

    def _chunk_text(self, text: str, chunk_size: int = 1500) -> List[str]:
        """Divide texto grande en chunks más pequeños."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0

        for word in words:
            word_size = len(word) + 1
            if current_size + word_size > chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def cargar_documentos_desde_carpeta(
        self, folder_path: str = "knowledge", recargar: bool = False
    ) -> Dict:
        """
        Carga automáticamente todos los archivos .md de una carpeta.
        Sistema inteligente: solo carga archivos nuevos o modificados.

        Args:
            folder_path: Ruta de la carpeta con archivos .md
            recargar: Si True, fuerza recarga completa (borra cache)

        Returns:
            Dict con estadísticas de carga
        """
        import hashlib
        import time

        stats = {
            "cargados": 0,
            "errores": 0,
            "ya_cargados": 0,
            "modificados": 0,
            "compartimentos": {},
            "tiempo_total": 0,
        }

        if not os.path.exists(folder_path):
            logger.warning(f"La carpeta '{folder_path}' no existe.")
            return stats

        start_time = time.time()

        if recargar:
            logger.info("🗑 Recarga forzada: limpiando colecciones y cache...")
            self.clear_all()
            metadata = {}
        else:
            metadata = self._load_metadata(folder_path)

        archivos_en_disco = {}

        for filename in os.listdir(folder_path):
            if filename.startswith("."):
                continue
            if not filename.endswith((".md", ".txt")):
                continue

            filepath = os.path.join(folder_path, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                if not content.strip():
                    logger.warning(f"Archivo vacío: {filename}")
                    continue

                content_hash = hashlib.md5(content.encode()).hexdigest()
                archivos_en_disco[filename] = {
                    "hash": content_hash,
                    "size": len(content),
                    "path": filepath,
                }

                compartment = self._detectar_compartimento(filename)

                existing_metadata = metadata.get(filename)

                if existing_metadata and not recargar:
                    if existing_metadata.get("hash") == content_hash:
                        stats["ya_cargados"] += 1
                        logger.debug(f"✅ Ya cargado (sin cambios): {filename}")
                        continue
                    else:
                        logger.info(f"📝 Archivo modificado: {filename}")
                        stats["modificados"] += 1

                chunks = self._chunk_text(content)

                for i, chunk in enumerate(chunks):
                    chunk_id = f"{filename}_{content_hash[:8]}_chunk{i}"
                    self.add_document(chunk, chunk_id, compartment)

                metadata[filename] = {
                    "hash": content_hash,
                    "compartment": compartment,
                    "chunks": len(chunks),
                    "size": len(content),
                    "loaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }

                logger.info(f"📄 {filename} → {compartment} ({len(chunks)} chunks)")
                stats["cargados"] += 1
                stats["compartimentos"][compartment] = (
                    stats["compartimentos"].get(compartment, 0) + 1
                )

            except Exception as e:
                logger.error(f"Error cargando {filename}: {e}")
                stats["errores"] += 1

        self._save_metadata(folder_path, metadata)

        stats["tiempo_total"] = round(time.time() - start_time, 2)

        logger.info(
            f"✅ Carga completada en {stats['tiempo_total']}s: "
            f"{stats['cargados']} nuevos, {stats['ya_cargados']} sin cambios, "
            f"{stats['modificados']} modificados"
        )

        return stats

    def auto_load_knowledge(
        self, knowledge_path: str = "knowledge", force_load: bool = False
    ) -> Dict:
        """
        Carga automática de conocimiento al iniciar.

        Args:
            knowledge_path: Ruta de la carpeta de conocimiento
            force_load: Si True, fuerza recarga completa

        Returns:
            Dict con estadísticas de carga
        """
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_path, knowledge_path)

        if not os.path.exists(full_path):
            base_path = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            full_path = os.path.join(base_path, knowledge_path)

        if not os.path.exists(full_path):
            logger.warning(f"Carpeta de conocimiento no encontrada: {full_path}")
            return {"cargados": 0, "ya_cargados": 0, "error": "Carpeta no encontrada"}

        logger.info(f"🔄 Iniciando carga automática de conocimiento desde: {full_path}")

        recargar = force_load or self._force_reload
        self._force_reload = False

        return self.cargar_documentos_desde_carpeta(full_path, recargar=recargar)

    def reload_knowledge(self, knowledge_path: str = "knowledge") -> Dict:
        """
        Fuerza la recarga completa del conocimiento.
        Uso: Llamar desde UI cuando usuario quiere reindexar.
        """
        logger.info("🔄 Recarga manual de conocimiento iniciada...")
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_path, knowledge_path)

        if not os.path.exists(full_path):
            base_path = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            full_path = os.path.join(base_path, knowledge_path)

        return self.cargar_documentos_desde_carpeta(full_path, recargar=True)

    def get_knowledge_status(self, knowledge_path: str = "knowledge") -> Dict:
        """
        Retorna el estado actual del conocimiento cargado.
        """
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_path, knowledge_path)

        if not os.path.exists(full_path):
            full_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                ),
                knowledge_path,
            )

        metadata = self._load_metadata(full_path) if os.path.exists(full_path) else {}

        total_docs = sum(col.count() for col in self.collections.values())

        return {
            "total_documentos": total_docs,
            "archivos_cache": len(metadata),
            "metadata": metadata,
            "compartimentos": {k: v.count() for k, v in self.collections.items()},
        }


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
