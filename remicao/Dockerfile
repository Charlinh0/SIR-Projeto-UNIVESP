# Imagem base: já vem com Python 3.12 instalado, sem você precisar instalar nada
FROM python:3.12-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia só o requirements primeiro (truque de performance: só reinstala libs se elas mudarem)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do código do projeto pra dentro do container
COPY . .

# Expõe a porta que a aplicação vai usar
EXPOSE 8000

# Comando que roda quando o container inicia
CMD ["gunicorn", "remicao.wsgi", "--bind", "0.0.0.0:8000"]