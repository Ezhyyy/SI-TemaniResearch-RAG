import fitz  # PyMuPDF
import re
from typing import List, Dict, Any

class PDFService:
    @staticmethod
    def extract_text_with_pages(pdf_path: str) -> List[Dict[str, Any]]:
        """
        Mengekstrak teks per halaman dari file PDF.
        Return: [{"page": 1, "text": "..."}, ...]
        """
        pages_content = []
        doc = fitz.open(pdf_path)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            text = page.get_text("text")
            # Normalisasi whitespace
            clean_text = re.sub(r'\s+', ' ', text).strip()
            if clean_text:
                pages_content.append({
                    "page": page_idx + 1,
                    "text": clean_text
                })
        doc.close()
        return pages_content

    @staticmethod
    def chunk_pages(pages_content: List[Dict[str, Any]], chunk_size: int = 400, overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Membagi teks halaman menjadi potongan-potongan (chunks) dengan mempertahankan nomor halaman sumber.
        chunk_size: jumlah kata perkiraan per chunk
        overlap: jumlah kata tumpang tindih
        """
        chunks = []
        for page_data in pages_content:
            page_num = page_data["page"]
            words = page_data["text"].split()
            
            if not words:
                continue

            # Jika halaman pendek, simpan sebagai 1 chunk langsung
            if len(words) <= chunk_size:
                chunks.append({
                    "page": page_num,
                    "text": " ".join(words)
                })
                continue

            start = 0
            while start < len(words):
                end = min(start + chunk_size, len(words))
                chunk_words = words[start:end]
                chunks.append({
                    "page": page_num,
                    "text": " ".join(chunk_words)
                })
                if end == len(words):
                    break
                start += (chunk_size - overlap)

        return chunks
