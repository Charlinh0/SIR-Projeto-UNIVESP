import time
import unicodedata
from django.core.files.storage import Storage
from django.conf import settings
from django.utils.text import get_valid_filename
from supabase import create_client
from django.core.files.base import ContentFile


class SupabaseStorage(Storage):
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.bucket = settings.SUPABASE_BUCKET

    def _clean_segment(self, segment):
        nfkd = unicodedata.normalize('NFKD', segment)
        sem_acento = nfkd.encode('ASCII', 'ignore').decode('ASCII')
        return get_valid_filename(sem_acento)

    def _clean_name(self, name):
        # Limpa CADA pedaço do caminho separadamente, preservando as barras "/"
        partes = name.split('/')
        partes_limpas = [self._clean_segment(p) for p in partes if p]
        return '/'.join(partes_limpas)

    def _open(self, name, mode='rb'):
        conteudo = self.client.storage.from_(self.bucket).download(name)
        return ContentFile(conteudo)
  
    def _save(self, name, content):
        name = self._clean_name(name)

        # Garante nome único, mesmo que dois arquivos tenham o mesmo nome original
        timestamp = int(time.time())
        pasta, _, arquivo = name.rpartition('/')
        nome_unico = f"{timestamp}_{arquivo}"
        name = f"{pasta}/{nome_unico}" if pasta else nome_unico

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