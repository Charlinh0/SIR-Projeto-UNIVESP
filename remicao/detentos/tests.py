from datetime import date
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Count
from django.test import TestCase
from django.urls import reverse

from .models import Detento, Atividade, Documento, Advogado, SolicitacaoRemicao
from .services import verificar_elegibilidade_remicao, verificar_documento
from .views import calcular_remicao


class CalculoRemicaoTestCase(TestCase):
    def setUp(self):
        self.detento = Detento.objects.create(
            nome="Detento Teste", processo="000.000/2026", pena_total_dias=1000,
            data_inicio="2024-01-01", regime="FECHADO"
        )

    def test_remicao_trabalho(self):
        Atividade.objects.create(detento=self.detento, tipo="TRABALHO", quantidade=9)
        resultado = calcular_remicao(self.detento)
        self.assertEqual(resultado['dias_remidos_trabalho'], 3)

    def test_remicao_estudo(self):
        Atividade.objects.create(detento=self.detento, tipo="ESTUDO", quantidade=24)
        resultado = calcular_remicao(self.detento)
        self.assertEqual(resultado['dias_remidos_estudo'], 2)

    def test_remicao_leitura(self):
        Atividade.objects.create(detento=self.detento, tipo="LEITURA", quantidade=2)
        resultado = calcular_remicao(self.detento)
        self.assertEqual(resultado['dias_remidos_leitura'], 8)

    def test_pena_restante_nunca_negativa(self):
        self.detento.pena_total_dias = 5
        self.detento.save()
        Atividade.objects.create(detento=self.detento, tipo="TRABALHO", quantidade=999)
        resultado = calcular_remicao(self.detento)
        self.assertEqual(resultado['pena_restante'], 0)

    def test_dias_cumpridos_informados_e_descontado(self):
        self.detento.dias_cumpridos_informados = 300
        self.detento.save()
        resultado = calcular_remicao(self.detento)
        self.assertEqual(resultado['pena_restante'], 1000 - 300)


class ElegibilidadeTestCase(TestCase):
    def test_crime_comum_sem_alerta(self):
        detento = Detento.objects.create(
            nome="Comum", processo="1", pena_total_dias=100,
            data_inicio="2024-01-01", regime="FECHADO", tipo_crime="COMUM"
        )
        resultado = verificar_elegibilidade_remicao(detento)
        self.assertTrue(resultado['elegivel_padrao'])
        self.assertIsNone(resultado['mensagem'])

    def test_crime_hediondo_gera_alerta(self):
        detento = Detento.objects.create(
            nome="Hediondo", processo="2", pena_total_dias=100,
            data_inicio="2024-01-01", regime="FECHADO", tipo_crime="HEDIONDO_EQUIPARADO"
        )
        resultado = verificar_elegibilidade_remicao(detento)
        self.assertFalse(resultado['elegivel_padrao'])
        self.assertIsNotNone(resultado['mensagem'])
        self.assertIn("hediondo", resultado['mensagem'].lower())


class DocumentoTestCase(TestCase):
    def test_documento_criado_como_pendente(self):
        detento = Detento.objects.create(
            nome="Doc Teste", processo="3", pena_total_dias=100,
            data_inicio="2024-01-01", regime="FECHADO"
        )
        arquivo = SimpleUploadedFile("teste.pdf", b"conteudo fake", content_type="application/pdf")
        documento = Documento.objects.create(
            detento=detento, tipo_documento="ATESTADO_TRABALHO", arquivo=arquivo
        )
        self.assertEqual(documento.estado_assinatura, "PENDENTE")


class PainelAdvogadosTestCase(TestCase):
    def test_contagem_detentos_e_solicitacoes(self):
        advogado = Advogado.objects.create(nome="Dr. Teste", oab="123456/SP")
        d1 = Detento.objects.create(
            nome="D1", processo="1", pena_total_dias=100, data_inicio="2024-01-01",
            regime="FECHADO", advogado=advogado
        )
        Detento.objects.create(
            nome="D2", processo="2", pena_total_dias=100, data_inicio="2024-01-01",
            regime="FECHADO", advogado=advogado
        )
        SolicitacaoRemicao.objects.create(advogado=advogado, detento=d1, status="PENDENTE")

        resultado = Advogado.objects.annotate(
            total_detentos=Count('detentos_vinculados', distinct=True),
            total_solicitacoes=Count('solicitacoes', distinct=True),
        ).get(pk=advogado.pk)

        self.assertEqual(resultado.total_detentos, 2)
        self.assertEqual(resultado.total_solicitacoes, 1)


class VerificacaoAutomaticaTests(TestCase):
    def setUp(self):
        User.objects.create_user('tester', password='x')
        self.client.login(username='tester', password='x')
        self.detento = Detento.objects.create(
            nome='Fulano de Tal', processo='0001', pena_total_dias=1000,
            data_inicio=date(2024, 1, 1), regime='FECHADO',
        )

    def test_upload_dispara_verificacao_em_segundo_plano(self):
        arquivo = SimpleUploadedFile(
            'atestado.pdf', b'%PDF-1.4 conteudo', content_type='application/pdf'
        )
        with mock.patch('detentos.views.iniciar_verificacao') as disparo:
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(
                    reverse('detalhe_detento', args=[self.detento.id]),
                    {'tipo_documento': 'ATESTADO_ESTUDO', 'arquivo': arquivo},
                )
        documento = Documento.objects.get()
        disparo.assert_called_once_with(documento.id)

    def test_verificar_documento_atualiza_o_estado(self):
        documento = Documento.objects.create(
            detento=self.detento, tipo_documento='ATESTADO_ESTUDO',
            arquivo=SimpleUploadedFile('x.pdf', b'nao e um pdf'),
        )
        self.assertEqual(documento.estado_assinatura, 'PENDENTE')
        verificar_documento(documento)
        documento.refresh_from_db()
        self.assertEqual(documento.estado_assinatura, 'SEM_ASSINATURA')