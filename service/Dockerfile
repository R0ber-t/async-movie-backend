FROM python:3.11-slim


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY api.py .
COPY user.py .
COPY database.py .
COPY models.py .

