#!/bin/bash
set -e

until pg_isready -h db -p 5432; do
  echo "Waiting for Primary server to start..."
  sleep 2
done

pg_basebackup -h db -D /var/lib/postgresql/data -U repl_user -v -P --wal-method=stream

cat > /var/lib/postgresql/data/recovery.conf << EOF
standby_mode = 'on'
primary_conninfo = 'host=db port=5432 user=repl_user password=repl_password'
trigger_file = '/tmp/MasterNow'
EOF

chown postgres:postgres /var/lib/postgresql/data/recovery.conf

pg_ctlcluster 15 main restart
