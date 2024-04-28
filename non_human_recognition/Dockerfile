FROM python:3.10.14-alpine

EXPOSE 8050

COPY . /app

WORKDIR /app

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

ENTRYPOINT [ "gunicorn" ]
CMD ["-w 4", "-b :8050", "app:server"]