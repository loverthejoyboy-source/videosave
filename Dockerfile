FROM python:3.12-slim
RUN useradd -m -u 1000 user
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -U -r requirements.txt
COPY --chown=user . .
USER user
CMD ["sh","-c","gunicorn -b 0.0.0.0:${PORT:-10000} -w 1 --threads 8 --timeout 50 app:app"]
