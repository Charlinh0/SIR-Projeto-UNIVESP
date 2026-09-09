from django.shortcuts import render, get_object_or_404, redirect
from .models import Detento
from django.contrib.auth.decorators import login_required
from .forms import DocumentoForm
from .services import verificar_elegibilidade_remicao
from .services import enviar_notificacao_elegibilidade
from django.contrib import messages

# HOME (SEM login obrigatório)
def home(request):
    return render(request, 'detentos/home.html')


# detentos/views.py (cálculo de remição)
def calcular_remicao(detento):
    """
    Busca todas as atividades registradas para o detento e calcula os dias remidos:
    - Trabalho: 1 dia remido para cada 3 dias trabalhados (divisão inteira // 3)
    - Estudo: 1 dia remido para cada 12 horas de estudo (divisão inteira // 12)
    - Leitura: 4 dias remidos por livro lido
    """
    total_dias_trabalhados = 0
    total_horas_estudo = 0
    total_livros_lidos = 0

    # 1. Recupera todas as atividades do detento usando a relação ForeignKey (related_name="atividades")
    atividades = detento.atividades.all()

    # 2. Varre as atividades acumulando as quantidades de acordo com o tipo
    for atividade in atividades:
        if atividade.tipo == 'TRABALHO':
            total_dias_trabalhados += atividade.quantidade
        elif atividade.tipo == 'ESTUDO':
            total_horas_estudo += atividade.quantidade
        elif atividade.tipo == 'LEITURA':
            total_livros_lidos += atividade.quantidade

    # 3. Aplica a matemática da LEP
    dias_remidos_trabalho = total_dias_trabalhados // 3
    dias_remidos_estudo = total_horas_estudo // 12
    dias_remidos_leitura = total_livros_lidos * 4

    # 4. Soma tudo para obter o total de dias remidos
    total_dias_remidos = dias_remidos_trabalho + dias_remidos_estudo + dias_remidos_leitura

    # 5. Calcula a pena restante (garantindo que nunca seja menor do que zero)
    pena_restante = max(
        0,
        detento.pena_total_dias - detento.dias_cumpridos_informados - total_dias_remidos
    )

    # Retorna um dicionário estruturado para enviar ao template HTML
    return {
        'total_dias_trabalhados': total_dias_trabalhados,
        'total_horas_estudo': total_horas_estudo,
        'total_livros_lidos': total_livros_lidos,
        'dias_remidos_trabalho': dias_remidos_trabalho,
        'dias_remidos_estudo': dias_remidos_estudo,
        'dias_remidos_leitura': dias_remidos_leitura,
        'total_dias_remidos': total_dias_remidos,
        'dias_cumpridos_informados': detento.dias_cumpridos_informados,
        'pena_restante': pena_restante,
    }
    


# VIEW lista
@login_required
def lista_detentos(request):
    detentos = Detento.objects.all()
    dados = []

    for d in detentos:
        # Captura o dicionário retornado
        dados_remicao = calcular_remicao(d)

        # Extrai os valores específicos do dicionário
        dados.append({
            "detento": d,
            "dias_remidos": dados_remicao['total_dias_remidos'],
            "pena_restante": dados_remicao['pena_restante']
        })

    return render(request, "detentos/lista.html", {"dados": dados})


# VIEW detalhe
@login_required
def detalhe_detento(request, detento_id):
    detento = get_object_or_404(Detento, pk=detento_id)

    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.detento = detento
            documento.save()
            return redirect('detalhe_detento', detento_id=detento.id)
    else:
        form = DocumentoForm()

    dados_remicao = calcular_remicao(detento)
    documentos = detento.documentos.all().order_by('-data_envio')
    elegibilidade = verificar_elegibilidade_remicao(detento)

    return render(request, "detentos/detalhe.html", {
        "detento": detento,
        "dados_remicao": dados_remicao,
        "dias_remidos": dados_remicao['total_dias_remidos'],
        "pena_restante": dados_remicao['pena_restante'],
        "form": form,
        "documentos": documentos,
        "elegibilidade": elegibilidade,
    })


# VIEW consulta
@login_required
def consulta_detento(request):
    resultado = None

    if request.method == "POST":
        nome = request.POST.get("nome")
        try:
            detento = Detento.objects.get(nome__iexact=nome)

            # Captura o dicionário do cálculo
            dados_remicao = calcular_remicao(detento)

            resultado = {
                "detento": detento,
                "dias_remidos": dados_remicao['total_dias_remidos'],
                "pena_restante": dados_remicao['pena_restante']
            }
        except Detento.DoesNotExist:
            resultado = "Detento não encontrado."

    return render(request, "detentos/consulta.html", {"resultado": resultado})


@login_required
def notificar_elegibilidade(request, detento_id):
    detento = get_object_or_404(Detento, pk=detento_id)
    enviado = enviar_notificacao_elegibilidade(detento, 'space.ace.guitar@gmail.com')
    if enviado:
        messages.success(request, f"Notificação enviada com sucesso sobre {detento.nome}.")
    else:
        messages.error(request, "Falha ao enviar notificação. Tente novamente.")
    return redirect('detalhe_detento', detento_id=detento.id)
