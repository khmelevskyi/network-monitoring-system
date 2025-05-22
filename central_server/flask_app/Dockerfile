FROM python:3.10

WORKDIR /flask_app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./migrations/ ./migrations/
COPY ./run.py .
COPY ./src/ ./src/

CMD ["sh", "-c", "flask --app src.app:create_app db upgrade && python3 run.py"]
