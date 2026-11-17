import chromadb
from typing import List, Dict, Any
from app.config import settings

class VectorService:
    def __init__(self):
        # Persistent storage ChromaDB
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(
            name="research_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def add_document_chunks(
        self,
        document_id: int,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ):
        """
        Menyimpan potongan teks (chunks), metadata (halaman, doc_id), dan embedding ke ChromaDB.
        """
        if not chunks:
            return

        ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunks))]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {
                "document_id": int(document_id),
                "page": int(c["page"]),
                "chunk_index": i
            }
            for i, c in enumerate(chunks)
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def search_chunks(
        self,
        document_id: int,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Melakukan cosine similarity search di ChromaDB berdasarkan dokumen tertentu.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"document_id": int(document_id)}
        )

        relevant_chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else []
            distances = results["distances"][0] if "distances" in results else []

            for i in range(len(docs)):
                page = metas[i].get("page", 1) if i < len(metas) else 1
                dist = distances[i] if i < len(distances) else 0.0
                relevant_chunks.append({
                    "text": docs[i],
                    "page": page,
                    "score": 1.0 - dist  # Cosine similarity estimate
                })

        return relevant_chunks

    def delete_document_chunks(self, document_id: int):
        """
        Menghapus seluruh vector chunks dokumen dari ChromaDB untuk menjaga konsistensi dengan MySQL.
        """
        try:
            self.collection.delete(where={"document_id": int(document_id)})
        except Exception:
            pass

vector_service = VectorService()
