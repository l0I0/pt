DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT
      FROM   pg_catalog.pg_database
      WHERE  datname = 'tg_bot') THEN
      PERFORM dblink_exec('dbname=postgres', 'CREATE DATABASE tg_bot');
   END IF;
END
$do$;

\connect tg_bot;

CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS phone_numbers (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE
);

INSERT INTO emails (email) VALUES ('test1@gmail.com') ON CONFLICT DO NOTHING;
INSERT INTO emails (email) VALUES ('test2@gmail.com') ON CONFLICT DO NOTHING;

INSERT INTO phone_numbers (phone_number) VALUES ('+71234567890') ON CONFLICT DO NOTHING;
INSERT INTO phone_numbers (phone_number) VALUES ('81234567890') ON CONFLICT DO NOTHING;

CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'repl_password';