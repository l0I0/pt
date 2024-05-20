FROM postgres:15

COPY postgresql.conf.rep /etc/postgresql/postgresql.conf
COPY pg_hba.conf.rep /etc/postgresql/pg_hba.conf

COPY init-replica.sh /docker-entrypoint-initdb.d/init-replica.sh

ENV POSTGRES_USER=$DB_USER
ENV POSTGRES_PASSWORD=$DB_PASSWORD
ENV POSTGRES_DB=$DB_NAME

RUN chmod +x /docker-entrypoint-initdb.d/init-replica.sh
