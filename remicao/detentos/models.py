

# Create your models here.
from django.db import models

class Detento(models.Model):
    REGIMES = [
        ('FECHADO', 'Fechado'),
        ('SEMIABERTO', 'Semiaberto'),
        ('ABERTO', 'Aberto'),
    ]
    nome = models.CharField(max_length=200)
    processo = models.CharField(max_length=50)
    pena_total_dias = models.IntegerField()
    dias_cumpridos_informados = models.IntegerField(
        default=0,
        help_text="Dias já descontados da pena por tempo de cumprimento, conforme "
                   "informado pela Vara de Execução Penal (fora do escopo de cálculo do SIR)."
    )
    data_inicio = models.DateField()
    regime = models.CharField(
        max_length=15,
        choices=REGIMES,
        error_messages={'blank': 'Atenção: Insira o regime do detento!',
                        'required': 'Atenção: Insira o regime do detento!'}
    )

    def __str__(self):
        return self.nome


class Atividade(models.Model):
    TIPOS = [
        ('TRABALHO', 'Trabalho'),
        ('ESTUDO', 'Estudo'),
        ('LEITURA', 'Leitura'),
    ]
    detento = models.ForeignKey(Detento, on_delete=models.CASCADE, related_name="atividades")
    tipo = models.CharField(max_length=10, choices=TIPOS)
    quantidade = models.IntegerField(help_text="Dias trabalhados, horas de estudo ou livros lidos")
    data_registro = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.detento.nome}"


class Documento(models.Model):
    TIPOS_DOCUMENTO = [
        ('ATESTADO_ESTUDO', 'Atestado de Estudo'),
        ('ATESTADO_TRABALHO', 'Atestado de Trabalho'),
        ('DOCUMENTO_PROCESSUAL', 'Documento Processual'),
    ]

    ESTADOS_ASSINATURA = [
        ('VALIDADO', 'Assinatura Válida (ICP-Brasil)'),
        ('INVALIDO', 'Assinatura Inválida'),
        ('SEM_ASSINATURA', 'Sem Assinatura Digital'),
    ]

    detento = models.ForeignKey(Detento, on_delete=models.CASCADE, related_name="documentos")
    tipo_documento = models.CharField(max_length=25, choices=TIPOS_DOCUMENTO)
    arquivo = models.FileField(upload_to='')
    estado_assinatura = models.CharField(
        max_length=15,
        choices=ESTADOS_ASSINATURA,
        default='SEM_ASSINATURA'
    )
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_documento} - {self.detento.nome}"