import unicodedata
from django.core.files.storage import Storage
from django.conf import settings
from django.utils.text import get_valid_filename
from supabase import create_client


class SupabaseStorage(Storage):
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.bucket = settings.SUPABASE_BUCKET

    def _clean_name(self, name):
        # Remove acentos (Ã, Ç, á, ê, etc.)
        nfkd = unicodedata.normalize('NFKD', name)
        nome_sem_acento = nfkd.encode('ASCII', 'ignore').decode('ASCII')
        # Troca espaços e símbolos por "_", mantendo a extensão do arquivo
        return get_valid_filename(nome_sem_acento)

    def _save(self, name, content):
        name = self._clean_name(name)
        file_bytes = content.read()
        self.client.storage.from_(self.bucket).upload(
            path=name,
            file=file_bytes,
            file_options={"content-type": content.content_type or "application/octet-stream"}
        )
        return name

    def exists(self, name):
        return False

    def url(self, name):
        return self.client.storage.from_(self.bucket).get_public_url(name)

    def size(self, name):
        return 0