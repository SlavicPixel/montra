FROM apache/spark:3.5.1

USER root
RUN apt-get update && apt-get install -y curl python3-pip libpq-dev gcc \
 && rm -rf /var/lib/apt/lists/*

# JDBC driver
RUN curl -L -o /opt/spark/jars/postgresql.jar \
    https://jdbc.postgresql.org/download/postgresql-42.7.4.jar

# psycopg2 (binary je najlakši)
RUN pip3 install --no-cache-dir psycopg2-binary

WORKDIR /opt/app
COPY spark_jobs/ /opt/app/spark_jobs/

USER spark
