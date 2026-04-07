from urllib.parse import quote

from app.config import Settings
from app.services.runtime_store import RuntimeStore


class StorageService:
    def __init__(self, settings: Settings, store: RuntimeStore) -> None:
        self.settings = settings
        self.store = store

    async def upload_blob(self, user_id: str, document_id: str, filename: str, data: bytes) -> str:
        blob_path = f"{user_id}/{document_id}/{quote(filename)}"
        self.store.blobs[blob_path] = data
        return f"memory://{self.settings.blob_container}/{blob_path}"

    async def delete_blob(self, blob_url: str) -> None:
        blob_path = blob_url.split(f"{self.settings.blob_container}/", maxsplit=1)[-1]
        self.store.blobs.pop(blob_path, None)

    async def get_blob_bytes(self, blob_url: str) -> bytes | None:
        blob_path = blob_url.split(f"{self.settings.blob_container}/", maxsplit=1)[-1]
        return self.store.blobs.get(blob_path)

