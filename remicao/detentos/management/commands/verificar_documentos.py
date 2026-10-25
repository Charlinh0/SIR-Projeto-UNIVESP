from django.core.management.base import BaseCommand
from detentos.models import Documento
from detentos.services import verificar_documento


class Command(BaseCommand):
    help = 'Verifica a assinatura digital dos documentos pendentes'

    def handle(self, *args, **options):
        pendentes = Documento.objects.filter(estado_assinatura='PENDENTE')
        total = pendentes.count()

        self.stdout.write(f"Encontrados {total} documento(s) pendente(s).")

        for documento in pendentes:
            estado, nome_assinante = verificar_documento(documento)
            self.stdout.write(
                f"Documento #{documento.id} ({documento.tipo_documento}): "
                f"{estado} - Assinante: {nome_assinante or 'N/A'}"
            )

        self.stdout.write(self.style.SUCCESS('Verificação concluída.'))
        
