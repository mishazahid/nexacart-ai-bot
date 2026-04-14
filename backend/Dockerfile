FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/faiss_index data/logs
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
