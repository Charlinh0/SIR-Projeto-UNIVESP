# ⚖️ SIR — Sistema Integrado de Remição (Projeto UNIVESP)

Projeto Integrador em Computação (PJI110 → PJI240), Grupo 10 — UNIVESP.
Polos: Agudos, Bariri, Bocaína, Pederneiras, Bauru, Lins, Pirajuí, Iacanga, Dois Córregos.

O SIR automatiza o cálculo da remição de pena de detentos por estudo, trabalho e leitura, e evoluiu na Fase II para incluir validação documental com assinatura digital, verificação de elegibilidade por tipo de crime e um painel de gestão de advogados.

🔗 **Sistema em produção:** https://sir-remicao.onrender.com

---

## 📖 Contexto e Previsão Legal

O projeto baseia-se no **Artigo 126 da Lei de Execução Penal (Lei nº 7.210/1984)**, que estabelece que o condenado pode remir parte do tempo de execução da pena por meio de:

- **Trabalho:** 1 dia de pena a menos para cada 3 dias trabalhados.
- **Estudo:** 1 dia de pena a menos para cada 12 horas de frequência escolar.
- **Leitura:** remição por leitura de livros, conforme a Resolução CNJ nº 391/2021.

> "A cada três dias de trabalho ou doze horas de estudo permite-se a remissão de um dia de pena." — Art. 126, LEP.

Na Fase II, o sistema também passou a considerar a **Lei nº 8.072/1990 (Lei dos Crimes Hediondos)**, que estabelece frações de progressão de regime diferenciadas, e a **Medida Provisória nº 2.200-2/2001**, que rege a validade jurídica de assinaturas digitais no padrão ICP-Brasil.

---

## 🧩 Módulos do sistema

### Fase I
- Cadastro de detentos e atividades (trabalho, estudo, leitura)
- Cálculo automático de dias remidos e pena restante
- Consulta pública por nome
- Autenticação de usuários

### Fase II
1. **Validação Documental** — upload de comprovantes (PDF, JPG, PNG) vinculados ao detento, com verificação automática de assinatura digital no padrão **PAdES**, validada contra a cadeia oficial de certificados da **ICP-Brasil** (ITI).
2. **Elegibilidade por Tipo de Crime** — alerta automático (painel + notificação por e-mail) quando o detento está classificado como crime hediondo ou equiparado, sinalizando a necessidade de conferência das frações de progressão de regime.
3. **Painel de Gestão de Advogados** — contagem de detentos vinculados e histórico de solicitações de remição por profissional, com objetivo de auditoria e controle de uso do sistema.

---

## 🛠️ Tecnologias Utilizadas

**Backend**
- Python 3.12 + Django 4.2
- PostgreSQL (via [Supabase](https://supabase.com))
- [pyHanko](https://docs.pyhanko.eu/) — verificação de assinatura digital PAdES/ICP-Brasil
- [Resend](https://resend.com) — envio de notificações por e-mail via API

**Frontend**
- HTML5 + Bootstrap 5 (tema escuro)
- JavaScript (validação de upload no navegador)

**Infraestrutura**
- [Render](https://render.com) — hospedagem e deploy contínuo (via GitHub)
- [Supabase Storage](https://supabase.com/storage) — armazenamento de documentos enviados
- Gunicorn + WhiteNoise — servidor de produção e arquivos estáticos

**Controle de versão**
- Git/GitHub, com a branch `main` preservando a versão aprovada da Fase I e a branch `fase-2` concentrando o desenvolvimento atual

---

## 🚀 Como executar o projeto localmente

```bash
# 1. Clone o repositório (branch fase-2)
git clone -b fase-2 https://github.com/Charlinh0/remicao-de-pena-carlos.git
cd remicao-de-pena-carlos

# 2. Crie e ative um ambiente virtual
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# 3. Entre na pasta do projeto Django
cd remicao

# 4. Instale as dependências
python -m pip install -r requirements.txt

# 5. Configure as variáveis de ambiente
# Crie um arquivo .env na pasta "remicao" com:
#   SECRET_KEY=
#   DEBUG=True
#   DATABASE_URL=
#   SUPABASE_URL=
#   SUPABASE_KEY=
#   SUPABASE_BUCKET=
#   RESEND_API_KEY=

# 6. Aplique as migrations
python manage.py migrate

# 7. Crie um superusuário
python manage.py createsuperuser

# 8. Rode o servidor
python manage.py runserver
```

Acesse em `http://127.0.0.1:8000/`.

### Verificação de assinatura dos documentos

A verificação de assinatura digital é processada de forma assíncrona. Após o upload, um documento fica com status **Pendente** até a execução do comando:

```bash
python manage.py verificar_documentos
```

---

## 📁 Estrutura do projeto

```
remicao-de-pena-carlos/
├── remicao/                  # pasta raiz do projeto Django (manage.py)
│   ├── remicao/               # configurações (settings, urls, wsgi)
│   ├── detentos/               # app principal
│   │   ├── models.py            # Detento, Atividade, Documento, Advogado, SolicitacaoRemicao
│   │   ├── views.py
│   │   ├── services.py          # regras de negócio (cálculo, verificação PAdES, e-mail)
│   │   ├── storage_backends.py  # integração com Supabase Storage
│   │   ├── certs/                # certificados ICP-Brasil (cadeia gov.br)
│   │   └── management/commands/ # comando verificar_documentos
│   └── requirements.txt
└── README.md
```

---

## ⚠️ Limitações conhecidas (documentadas para fins acadêmicos)

- A verificação de revogação de certificado (CRL/OCSP) pode não ser confirmável em tempo real em ambiente de desenvolvimento; nesse caso, o sistema aceita a assinatura como válida (soft-fail), com a limitação registrada no Relatório Parcial.
- O envio de e-mail utiliza um remetente de teste da API Resend, que só entrega para o endereço cadastrado na conta até que um domínio próprio seja verificado.
- A validação de assinatura cobre a cadeia de certificados do gov.br; a cobertura completa de todas as Autoridades Certificadoras da ICP-Brasil é um trabalho futuro.

---

## 👥 Equipe — Grupo 10

Carlos Augusto Brosco Lopes · Marcel Melo · João Pedro Silvério Felipe · Matheus da Cruz Figueira · Gyordanna Mayara Gaspar da Costa Viana · Maycon Douglas Romano Viana · Guilherme Jardim Picoloto · Flavia Rejane Reimer

Orientação: Prof.ª Simone Santos (Fase II) · Prof. José Lima (Fase I)

---

## 📄 Licença

Projeto acadêmico desenvolvido para fins educacionais no âmbito do curso de Tecnologia da Informação — UNIVESP.
