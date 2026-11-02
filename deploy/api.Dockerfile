FROM python:3.12-slim
WORKDIR /srv
COPY backend/requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/main.py /srv/backend/main.py
COPY data/api /srv/data/api
RUN useradd --no-create-home rafah
USER rafah
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/v1/metadata')"
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
