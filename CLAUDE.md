# CLAUDE.md — SIR (Sistema Integrado de Remição)

Projeto Integrador II (PJI240) da UNIVESP, Grupo 12 (integrantes e polos no README). Orientadora: Profª Simone Santos. Responda em português.
Produção: https://sir-remicao.onrender.com · Repo: https://github.com/Charlinh0/SIR-Projeto-UNIVESP (branch padrão: `fase-2`; `main` guarda a Fase I aprovada, não mexer).

## O que o sistema faz
Calcula remição de pena (LEP, art. 126) e, na Fase II, tem 3 módulos:
1. **Validação documental**: upload de comprovantes (PDF/JPG/PNG, máx. 5 MB) com verificação de assinatura PAdES/ICP-Brasil (pyHanko). **A verificação é automática**: ao salvar o documento, a view faz `transaction.on_commit(lambda: iniciar_verificacao(documento.id))`, que roda `verificar_documento` numa thread (`services.py`). Há também o botão "Verificar agora" (view `reverificar_documento`, só POST) para documentos que ficarem PENDENTE, e o comando `verificar_documentos` como reprocessamento.
2. **Elegibilidade por tipo de crime**: alerta para hediondo/equiparado (Lei 8.072/90) + e-mail via API Resend. O sistema **alerta, não bloqueia**: a remição continua sendo calculada.
3. **Painel de advogados**: contagem de detentos e solicitações por advogado (`annotate`/`Count`).

Regras de cálculo (`detentos/views.py`, função `calcular_remicao`):
- Trabalho: `dias // 3` · Estudo: `horas // 12` · Leitura: `livros * 4`.
- `pena_restante = max(0, pena_total_dias - dias_cumpridos_informados - total_dias_remidos)`.
- `dias_cumpridos_informados` é digitado manualmente (vem da Vara de Execução). **Decisão de design**: o SIR não conta tempo de pena cumprida.
- **Não implementado (limitação conhecida)**: mínimo de 3 dias de frequência no estudo e teto anual de livros (CNJ 391/2021).

## Stack e estrutura
Django 4.2.11 · Python **3.12.10** (`.python-version` em `remicao/`; no Render o 3.14 quebrava o admin) · Bootstrap 5.3 tema escuro · JS puro · PostgreSQL (Supabase, Session Pooler porta 5432) · Supabase Storage (bucket público `documentos`) · Gunicorn + WhiteNoise.

```
remicao-de-pena/            # raiz git, venv em .venv
└── remicao/                # onde fica o manage.py (Root Directory no Render)
    ├── remicao/            # settings, urls, wsgi
    └── detentos/           # app principal
        ├── models.py       # Detento, Atividade, Documento, Advogado, SolicitacaoRemicao
        ├── views.py        # views + calcular_remicao
        ├── services.py     # verificação PAdES, elegibilidade, e-mail
        ├── storage_backends.py  # SupabaseStorage
        ├── certs/Cadeia_GovBr-der.p7b
        ├── management/commands/verificar_documentos.py
        ├── templates/detentos/
        ├── static/detentos/js/validacao_documento.js
        └── tests.py
```

## Comandos (PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1      # na raiz remicao-de-pena
cd remicao
python -m pip install -r requirements.txt   # SEMPRE "python -m pip", nunca "pip" solto (há mais de um Python na máquina)
python manage.py runserver
python manage.py test             # 11 testes; usa SQLite + FileSystemStorage automaticamente (arquivos de teste vão para remicao/test_media/, que está no .gitignore)
python manage.py verificar_documentos   # reprocessa documentos PENDENTE (normalmente não é mais necessário: a verificação roda sozinha após o upload)
```
- Para atualizar dependências: `python -m pip freeze | Out-File -Encoding utf8 requirements.txt` (sem `-Encoding utf8` o arquivo vira UTF-16 e o deploy quebra).
- Rode `python manage.py test` antes de cada push.

## Deploy
Render faz deploy automático ao dar push na `fase-2`.
- Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start: `gunicorn remicao.wsgi`
- Variáveis de ambiente: `SECRET_KEY`, `DEBUG`, `DATABASE_URL` (senha URL-encoded), `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_BUCKET`, `RESEND_API_KEY`.
- **Nunca commitar `.env`** nem colar chaves/senhas em código, README ou neste arquivo. Credenciais de teste: pedir ao Carlos.
- O plano gratuito dorme: a 1ª requisição demora (tela de loading do Render).

## Decisões técnicas que NÃO devem ser "consertadas"
- **Verificação em thread, sem fila**: simples de propósito (sem Celery/Redis). `_executar_em_segundo_plano` fecha a conexão com `connection.close()` no `finally`; não chame `close_old_connections()` dentro de `verificar_documento`, pois quebra o `TestCase`. Se o Render reiniciar no meio, o documento fica PENDENTE e o botão/comando resolve.
- **Soft-fail de revogação (CRL/OCSP)**: se o pyHanko falhar só por falta de informação de revogação (exceção cujo texto contém "revocation"/"revinfo"), o documento é aceito como VALIDADO. Limitação documentada no relatório.
- **Classificar, não recusar**: PDF sem assinatura ou imagem não é rejeitado.
- **Destino do e-mail fixo** (`space.ace.guitar@gmail.com`) em `notificar_elegibilidade`: o remetente de teste `onboarding@resend.dev` só entrega para o e-mail da conta Resend. Só muda com domínio próprio verificado.
- **Nomes de arquivo no Storage**: `_clean_name` por segmento + timestamp (evita erro 409 de duplicado).
- Cadeia de confiança cobre só a AC do gov.br (ampliar para todas as ACs do ITI é trabalho futuro).

## Padrões de front-end (acessibilidade já auditada: Lighthouse 100 em Home, Ficha e Painel)
Mantenha, ao mexer em templates:
- `<main>` e `<nav aria-label>` em `base.html`; `<meta name="viewport">`.
- Hierarquia de títulos sem pular níveis: h1 → h2 → h3. Para tamanho menor use a classe (`<h3 class="h5">`), nunca troque a tag. Valores numéricos soltos são `<p class="h5">`, não título.
- Todo `input`/`select` com `<label for="{{ campo.id_for_label }}">`.
- Contraste: usar `text-*-emphasis` do Bootstrap no tema escuro; evitar `text-muted` em informação importante.
- Azul padrão: `#0d6efd`.
- **O auto-formatador do Antigravity quebra `{{ }}` longos em várias linhas e imprime o código cru na tela.** Uma variável por célula/linha curta. Se aparecer `{{ ... }}` na página, é isso.

## Armadilhas conhecidas
- **Pyrefly** (verificador do Antigravity) mostra erros falsos em imports relativos e `Model.objects`. Ignorar (config local em `pyrefly.toml`, que está no `.gitignore`). **Não instalar `django-stubs`** (polui o `requirements.txt` e o deploy).
- Push rejeitado: `git pull` primeiro; se abrir o Vim, `Esc` e `:wq`.
- Remote correto: `git remote set-url origin https://github.com/Charlinh0/SIR-Projeto-UNIVESP.git`.
- Pipe de PowerShell com acentos corrompe caminhos; prefira caminhos entre aspas.
- Docker/WSL2 (`Dockerfile`, `docker-compose.yml` em `remicao/`) é experimento pessoal, fora do escopo do PI.

## Commits
- Mensagens curtas, em português, no imperativo ("Corrige hierarquia de títulos no painel").
- Um assunto por commit. Não fazer `push --force`.

## Calendário do PI II (Fase II)
- Testes finais: 23–28/10 · Vídeo: 27/10–01/11 · Quinzena 6 até 01/11.
- **Live com a orientadora: 30/10 às 20h** (levar o relatório final, mesmo preliminar; panorama do que foi feito, resultados, testes, devolutivas e o que falta).
- **Entrega final: atividades abertas de 02/11 às 00h até 06/11 às 23:59** (carência até 15/11 23:59): Relatório Final + Avaliação Colaborativa + vídeo.
- Relatório Final, diferenças em relação ao parcial: link do vídeo na capa; nova seção 2.4 (Aplicação das disciplinas no PI); seção 3 vira "Resultados: solução final" (solução concluída, imagens, melhorias a partir de testes e devolutivas); nova seção 4 (Considerações finais: objetivos, resultados, contribuições, limitações, impacto na comunidade externa); revisar Resumo, Metodologia, Sumário/paginação, Referências e Apêndices; nada pode sugerir projeto "em andamento".

## Pendências
- Relatório Final: versão preliminar pronta (`Relatorio_Final_PI2_Grupo12.docx`); falta link do vídeo, disciplinas por integrante (seção 2.4), atualizar contagem do Forms e conferir o Apêndice A. Lighthouse já está 100/100/100.
- Roteiro e base para o vídeo; definir quem grava.
- Cobrar mais testadores no Google Forms.
- Opcional: selo "Hediondo" na lista (`<span class="badge bg-danger ms-2">Hediondo</span>` quando `item.detento.tipo_crime == 'HEDIONDO_EQUIPARADO'`).
- Futuro: fila de tarefas dedicada para a verificação de assinatura, mínimo de frequência/teto de livros (regulamentação do CNJ).
