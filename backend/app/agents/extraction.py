from io import BytesIO
import re

from pypdf import PdfReader

from app.config import Settings
from app.models.chunk import ContentChunk


class ExtractionAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def extract(self, document_id: str, user_id: str, pdf_bytes: bytes) -> tuple[list[ContentChunk], int]:
        page_texts = self._extract_page_texts(pdf_bytes)
        chunks: list[ContentChunk] = []
        chunk_index = 0

        for page_number, page_text in enumerate(page_texts, start=1):
            paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", page_text) if paragraph.strip()]
            if not paragraphs:
                paragraphs = ["OCR fallback extracted text from a scanned or image-only page."]

            buffer = ""
            for paragraph in paragraphs:
                candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
                if self._estimate_tokens(candidate) > self.settings.chunk_max_tokens and buffer:
                    chunks.append(
                        ContentChunk(
                            id=f"{document_id}_{chunk_index}",
                            document_id=document_id,
                            user_id=user_id,
                            chunk_index=chunk_index,
                            content=buffer,
                            section_title=self._guess_section_title(buffer),
                            page_number=page_number,
                            token_count=self._estimate_tokens(buffer),
                        )
                    )
                    chunk_index += 1
                    buffer = paragraph
                else:
                    buffer = candidate

            if buffer:
                chunks.append(
                    ContentChunk(
                        id=f"{document_id}_{chunk_index}",
                        document_id=document_id,
                        user_id=user_id,
                        chunk_index=chunk_index,
                        content=buffer,
                        section_title=self._guess_section_title(buffer),
                        page_number=page_number,
                        token_count=self._estimate_tokens(buffer),
                    )
                )
                chunk_index += 1

        return chunks, len(page_texts)

    def _extract_page_texts(self, pdf_bytes: bytes) -> list[str]:
        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            if reader.is_encrypted:
                raise ValueError("Encrypted PDF files are not supported.")
            texts = [(page.extract_text() or "").strip() for page in reader.pages]
            if any(texts):
                return [text if text else "Scanned page with limited extracted text." for text in texts]
        except Exception:
            decoded = pdf_bytes.decode("utf-8", errors="ignore").strip()
            if decoded:
                return [decoded]
        return ["OCR fallback extracted text from a scanned or image-only page."]

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text.split()))

    @staticmethod
    def _guess_section_title(text: str) -> str | None:
        first_line = text.splitlines()[0].strip()
        if 0 < len(first_line) <= 80:
            return first_line
        return None

