FROM python:3.8

WORKDIR /github.com/FilipAdrian/PAD
COPY ./PAD .

RUN pip install -r requirements.txt

#DB Config
#ENV DB_HOST=host.docker.internal
#ENV DB_PORT=5432
#ENV DB_USERNAME=postgres
#ENV DB_PASSWORD=postgres
#ENV DB_SCHEMA=postgres

#api properties
#ENV API_PORT=8081
#ENV API_HOST=0.0.0.0
#ENV API_BASE_PATH="/api/"
#ENV DEFAULT_RATE_LIMIT="5 per minute"
#ENV DEFAULT_CAPACITY=10
#ENV GATEWAY_URL="https://httpbin.org/post"

EXPOSE 8081
#EXPOSE 5432

CMD [ "python", "./main.py" ]