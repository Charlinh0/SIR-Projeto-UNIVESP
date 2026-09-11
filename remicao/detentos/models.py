

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
    TIPOS_CRIME = [
        ('COMUM', 'Crime Comum'),
        ('HEDIONDO_EQUIPARADO', 'Crime Hediondo ou Equiparado'),
    ]

    tipo_crime = models.CharField(
        max_length=25,
        choices=TIPOS_CRIME,
        default='COMUM',
        help_text="Classificação conforme a Lei nº 8.072/1990, para fins de "
                   "verificação de elegibilidade e frações de progressão de regime."
    )

    advogado = models.ForeignKey(
        'Advogado', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="detentos_vinculados"
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
        ('PENDENTE', 'Assinatura Pendente')
    ]

    detento = models.ForeignKey(Detento, on_delete=models.CASCADE, related_name="documentos")
    tipo_documento = models.CharField(max_length=25, choices=TIPOS_DOCUMENTO)
    arquivo = models.FileField(upload_to='')
    estado_assinatura = models.CharField(
        max_length=15,
        choices=ESTADOS_ASSINATURA,
        default='PENDENTE'
    )
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_documento} - {self.detento.nome}"

class Advogado(models.Model):
    nome = models.CharField(max_length=200)
    oab = models.CharField(max_length=20, unique=True, help_text="Número de registro na OAB (ex: 123456/SP)")
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.nome} (OAB {self.oab})"


class SolicitacaoRemicao(models.Model):
    STATUS = [
        ('PENDENTE', 'Pendente'),
        ('DEFERIDA', 'Deferida'),
        ('INDEFERIDA', 'Indeferida'),
    ]
    advogado = models.ForeignKey(Advogado, on_delete=models.CASCADE, related_name="solicitacoes")
    detento = models.ForeignKey(Detento, on_delete=models.CASCADE, related_name="solicitacoes")
    status = models.CharField(max_length=10, choices=STATUS, default='PENDENTE')
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Solicitação de {self.advogado.nome} — {self.detento.nome}"