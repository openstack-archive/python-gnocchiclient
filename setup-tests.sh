#!/bin/bash 
set -e -x

wait_for_line () {
    while read line
    do
        echo "$line" | grep -q "$1" && break
    done < "$2"
    # Read the fifo for ever otherwise process would block
    cat "$2" &
#    cat "$2" >/dev/null &
}

clean_exit (){
    local error_code="$?"
    kill $(jobs -p)
    rm -rf "$@"
    return $error_code
}

GNOCCHI_DATA=`mktemp -d /tmp/gnocchi-data-XXXXX`
MYSQL_DATA=`mktemp -d /tmp/gnocchi-mysql-XXXXX`
trap "clean_exit \"$GNOCCHI_DATA\" \"$MYSQL_DATA\"" EXIT

mkfifo ${MYSQL_DATA}/out
PATH=$PATH:/usr/libexec
mysqld --no-defaults --datadir=${MYSQL_DATA} --pid-file=${MYSQL_DATA}/mysql.pid --socket=${MYSQL_DATA}/mysql.socket --skip-networking --skip-grant-tables &> ${MYSQL_DATA}/out &
# Wait for MySQL to start listening to connections
wait_for_line "mysqld: ready for connections." ${MYSQL_DATA}/out
export GNOCCHI_TEST_INDEXER_URL="mysql+pymysql://root@localhost/test?unix_socket=${MYSQL_DATA}/mysql.socket&charset=utf8"
mysql --no-defaults -S ${MYSQL_DATA}/mysql.socket -e 'CREATE DATABASE test;'


mkfifo ${GNOCCHI_DATA}/out
echo '{"default": ""}' > ${GNOCCHI_DATA}/policy.json
cat > ${GNOCCHI_DATA}/gnocchi.conf <<EOF
[oslo_policy]
policy_file = ${GNOCCHI_DATA}/policy.json
[api]
middlewares = 
[storage]
metric_processing_delay = 1
file_basepath = ${GNOCCHI_DATA}
driver = file
coordination_url = file://${GNOCCHI_DATA}
[indexer]
url = mysql+pymysql://root@localhost/test?unix_socket=${MYSQL_DATA}/mysql.socket&charset=utf8
EOF
gnocchi-dbsync --config-file ${GNOCCHI_DATA}/gnocchi.conf 
gnocchi-metricd --config-file ${GNOCCHI_DATA}/gnocchi.conf &>/dev/null &
gnocchi-api --config-file ${GNOCCHI_DATA}/gnocchi.conf &> ${GNOCCHI_DATA}/out &
# Wait for Gnocchi to start
wait_for_line "Running on http://0.0.0.0:8041/" ${GNOCCHI_DATA}/out
export GNOCCHI_ENDPOINT=http://localhost:8041/

create_archive_policy() { curl -X POST -H "X-USER-ID: $(uuidgen)" -H "X-PROJECT-ID: $(uuidgen)" -H "Content-Type: application/json" -d "$1" ${GNOCCHI_ENDPOINT}v1/archive_policy ; }
create_archive_policy '{"name":"high","definition":[{"granularity": "1s","points": 86400},{"granularity": "1m","points": 43200},{"granularity": "1h","points": 8760}]}'

$*
