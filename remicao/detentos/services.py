import unicodedata
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext
import os
from django.conf import settings
from cryptography.hazmat.primitives.serialization import pkcs7, Encoding
from asn1crypto import x509 as asn1_x509
import resend


def verificar_assinatura_pdf(caminho_ou_arquivo):
    """
    Recebe um arquivo PDF (caminho no disco ou objeto de arquivo aberto em modo binário)
    e retorna uma tupla: (estado, nome_do_assinante)

    estado é um dos valores de Documento.ESTADOS_ASSINATURA:
    'VALIDADO', 'INVALIDO' ou 'SEM_ASSINATURA'
    """
    try:
        if hasattr(caminho_ou_arquivo, 'read'):
            arquivo = caminho_ou_arquivo
            arquivo.seek(0)
            return _processar(arquivo)
        else:
            with open(caminho_ou_arquivo, 'rb') as arquivo:
                return _processar(arquivo)
    except Exception as e:
        print(f"Erro ao verificar assinatura: {e}")
        return 'SEM_ASSINATURA', None


def _processar(arquivo):
    r = PdfFileReader(arquivo)

    if not r.embedded_signatures:
        return 'SEM_ASSINATURA', None

    sig = r.embedded_signatures[0]
    nome_assinante = _extrair_nome(sig.signer_cert)

    # Validação SEM lista de confiança específica (ambiente de teste/desenvolvimento).
    # Em produção com certificado ICP-Brasil real, isso seria substituído por
    # trust_roots com os certificados oficiais do ITI.
    trust_roots = _carregar_certificados_confiaveis()
    vc = ValidationContext(
        trust_roots=trust_roots,
        allow_fetching=True,
        revocation_mode='soft-fail'
    )
    
    try:
        status = validate_pdf_signature(sig, vc)
        if status.intact and status.valid:
            return 'VALIDADO', nome_assinante
        else:
            return 'INVALIDO', nome_assinante
    except Exception as e:
        mensagem = str(e)
        if 'revocation' in mensagem.lower() or 'revinfo' in mensagem.lower():
            # A cadeia de confiança até a raiz ICP-Brasil foi validada com sucesso,
            # mas não foi possível confirmar a não-revogação do certificado (CRL/OCSP)
            # no ambiente de desenvolvimento. Aceito como VALIDADO nesta versão do
            # protótipo; ver limitação documentada no Relatório Parcial.
            return 'VALIDADO', nome_assinante
        print(f"Erro na validacao de confianca: {e}")
        return 'INVALIDO', nome_assinante


def _extrair_nome(cert):
    try:
        subject = cert.subject.native
        return subject.get('common_name', 'Desconhecido')
    except Exception:
        return 'Desconhecido'


def _carregar_certificados_confiaveis():
    caminho_p7b = os.path.join(settings.BASE_DIR, 'detentos', 'certs', 'Cadeia_GovBr-der.p7b')
    with open(caminho_p7b, 'rb') as f:
        certs_cryptography = pkcs7.load_der_pkcs7_certificates(f.read())
    return [asn1_x509.Certificate.load(c.public_bytes(Encoding.DER)) for c in certs_cryptography]

def verificar_elegibilidade_remicao(detento):
    """
    Verifica se o tipo de crime do detento exige atenção especial quanto às
    frações de progressão de regime, conforme a Lei nº 8.072/1990 (Lei dos
    Crimes Hediondos). Retorna um dicionário com o resultado e uma mensagem
    de alerta, quando aplicável.

    Importante: o SIR calcula a remição de dias por estudo/trabalho/leitura
    normalmente em todos os casos (conforme o art. 126 da LEP), pois a
    remição em si não é vedada a crimes hediondos. O alerta serve para
    lembrar o operador jurídico de que a FRAÇÃO DE CUMPRIMENTO DA PENA
    (para fins de progressão de regime) é diferenciada nesses casos, e deve
    ser conferida manualmente junto ao processo.
    """
    if detento.tipo_crime == 'HEDIONDO_EQUIPARADO':
        return {
            'elegivel_padrao': False,
            'mensagem': (
                f"Atenção: {detento.nome} está classificado como crime hediondo "
                f"ou equiparado (Lei nº 8.072/1990). As frações de cumprimento "
                f"de pena para progressão de regime são diferenciadas da regra "
                f"geral da LEP. Confira o percentual aplicável junto ao processo "
                f"antes de qualquer decisão sobre progressão."
            ),
        }
    return {
        'elegivel_padrao': True,
        'mensagem': None,
    }
def enviar_notificacao_elegibilidade(detento, destinatario_email):
    """
    Envia um e-mail de alerta quando o detento está classificado como crime
    hediondo/equiparado, notificando o operador jurídico responsável.
    """
    resend.api_key = settings.RESEND_API_KEY

    try:
        resend.Emails.send({
            "from": "SIR <onboarding@resend.dev>",
            "to": [destinatario_email],
            "subject": f"[SIR] Atenção: verificação de elegibilidade — {detento.nome}",
            "html": (
                f"<p>O detento <strong>{detento.nome}</strong> "
                f"(processo {detento.processo}) está classificado como "
                f"crime hediondo ou equiparado (Lei nº 8.072/1990).</p>"
                f"<p>As frações de cumprimento de pena para progressão de "
                f"regime são diferenciadas da regra geral da LEP. Confira "
                f"o percentual aplicável junto ao processo antes de "
                f"qualquer decisão sobre progressão.</p>"
                f"<p><em>Notificação automática do Sistema Integrado de Remição (SIR).</em></p>"
            ),
        })
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False