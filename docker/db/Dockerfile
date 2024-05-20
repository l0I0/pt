FROM postgres:15

COPY postgresql.conf.db /etc/postgresql/postgresql.conf
COPY pg_hba.conf.db /etc/postgresql/pg_hba.conf

COPY init.sql /docker-entrypoint-initdb.d/


ENV POSTGRES_USER=$DB_USER
ENV POSTGRES_PASSWORD=$DB_PASSWORD
ENV POSTGRES_DB=$DB_NAME