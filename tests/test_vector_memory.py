import sys
import types
import os
import tempfile
import pytest


# --- Fake Chromadb backend for unit testing ---
class VecWrapper(list):
    def tolist(self):
        return list(self)


class FakeEmbeddingModel:
    def encode(self, text, convert_to_tensor=False):
        data = [ord(c) for c in text]
        data = (data[:8] + [0] * 8)[:8]
        return VecWrapper(data)


class FakeCollection:
    def __init__(self, name):
        self.name = name
        self.items = []  # each item: {id, embedding, document, metadata}

    def upsert(self, ids, embeddings, documents, metadatas):
        for i, doc in enumerate(documents):
            self.items.append(
                {
                    "id": ids[i],
                    "embedding": embeddings[i],
                    "document": doc,
                    "metadata": metadatas[i],
                }
            )

    def count(self):
        return len(self.items)

    def get(self, limit=None, include=None):
        lim = 0 if limit is None else int(limit)
        subset = self.items[-lim:] if lim > 0 else []
        ids = [it["id"] for it in subset]
        docs = [it["document"] for it in subset]
        return {
            "ids": ids,
            "documents": docs,
            "metadatas": [it["metadata"] for it in subset],
        }

    def delete(self, ids):
        self.items = [it for it in self.items if it["id"] not in set(ids)]


class FakePersistentClient:
    def __init__(self, path):
        self.path = path
        self.collections = {}

    def get_or_create_collection(self, name):
        if name not in self.collections:
            self.collections[name] = FakeCollection(name)
        return self.collections[name]

    def delete_collection(self, name):
        if name in self.collections:
            del self.collections[name]


# Wire up the fake chromadb module before importing vector_memory
import types as _types

fake_module = _types.ModuleType("chromadb")
setattr(fake_module, "PersistentClient", FakePersistentClient)
sys.modules["chromadb"] = fake_module

import kr_studio.core.vector_memory as vm


@pytest.fixture(autouse=True)
def patch_embedding_and_chromadb(monkeypatch):
    # Patch embedding model with a lightweight fake model
    monkeypatch.setattr(vm, "embedding_model", FakeEmbeddingModel(), raising=True)
    yield


def test_isolation_between_compartments(monkeypatch, tmp_path):
    mem = vm.VectorMemory(db_path=str(tmp_path / "mem"), compartments=["a", "b"])
    mem.add_document(text="Hello world", doc_id="d1", compartment="a")
    mem.add_document(text="Hola mundo", doc_id="d2", compartment="b")

    docs_a = mem.get_documents_for_compartment("a")
    docs_b = mem.get_documents_for_compartment("b")
    assert any(d["id"] == "d1" for d in docs_a)
    assert not any(d["id"] == "d1" for d in docs_b)
    assert any(d["id"] == "d2" for d in docs_b)


def test_search_returns_expected_doc_in_compartment(monkeypatch, tmp_path):
    mem = vm.VectorMemory(db_path=str(tmp_path / "mem2"), compartments=["a"])
    mem.add_document(text="Hello world", doc_id="d1", compartment="a")
    results = mem.search("Hello", n_results=2, compartment="a")
    assert isinstance(results, list)
    if results:
        assert any(r.get("id") == "d1" for r in results)


def test_get_and_clear_compartments_and_documents(monkeypatch, tmp_path):
    mem = vm.VectorMemory(db_path=str(tmp_path / "mem3"), compartments=["x", "y"])
    mem.add_document(text="Doc x1", doc_id="dx1", compartment="x")
    mem.add_document(text="Doc y1", doc_id="dy1", compartment="y")
    assert set(mem.get_compartments()) == {"x", "y"}
    mem.clear_compartment("x")
    docs_x = mem.get_documents_for_compartment("x")
    docs_y = mem.get_documents_for_compartment("y")
    assert len(docs_x) == 0
    assert len(docs_y) == 1
