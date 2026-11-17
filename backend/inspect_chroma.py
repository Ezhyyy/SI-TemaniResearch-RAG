import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chromadb
from app import create_app

def inspect_chroma():
    app = create_app()
    chroma_path = app.config.get("CHROMA_PATH", "./chroma_db")
    
    print("=" * 60)
    print(f"🔍 INSPEKSI DATABASE VEKTOR (ChromaDB)")
    print(f"📁 Lokasi Folder: {os.path.abspath(chroma_path)}")
    print("=" * 60)
    
    if not os.path.exists(chroma_path):
        print("❌ Folder ChromaDB belum ada (belum ada dokumen yang diunggah).")
        return

    client = chromadb.PersistentClient(path=chroma_path)
    collections = client.list_collections()
    
    if not collections:
        print("ℹ️ Belum ada collection yang dibuat di ChromaDB.")
        return

    for col in collections:
        count = col.count()
        print(f"\n📦 Collection: '{col.name}'")
        print(f"   Total Chunks Vektor : {count}")

        if count == 0:
            print("   (Collection masih kosong)")
            continue

        # Ambil sampel hingga 5 chunk data
        sample = col.peek(limit=5)
        ids = sample.get("ids", [])
        metadatas = sample.get("metadatas", [])
        documents = sample.get("documents", [])

        print(f"\n   --- Sampel Data ({len(ids)} dari {count} chunks) ---")
        for i, (cid, meta, doc) in enumerate(zip(ids, metadatas, documents), 1):
            doc_id = meta.get("document_id", "N/A")
            page = meta.get("page_number", meta.get("page", "N/A"))
            preview = (doc[:100] + "...") if len(doc) > 100 else doc
            print(f"   [{i}] ID Vector   : {cid}")
            print(f"       Document ID : {doc_id}")
            print(f"       Halaman PDF : {page}")
            print(f"       Teks Chunk  : {preview}")
            print()

    print("=" * 60)

if __name__ == "__main__":
    inspect_chroma()
