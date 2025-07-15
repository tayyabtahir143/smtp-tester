FROM python:3.11

WORKDIR /app

COPY smtp_tester_web.py .

RUN pip install flask

EXPOSE 8080

CMD ["python3", "smtp_tester_web.py"]

