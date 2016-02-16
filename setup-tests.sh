#!/bin/bash
set -e -x

wait_for_line () {
    while read line
    do
        echo "$line" | grep -q "$1" && break
    done < "$2"
    # Read the fifo for ever otherwise process would block
    cat "$2" &
}

clean_exit () {
    local error_code="$?"
    kill $(jobs -p)
    rm -rf "$@"
    return $error_code
}

GNOCCHI_DATA=`mktemp -d /tmp/gnocchi-data-XXXXX`
trap "clean_exit \"$GNOCCHI_DATA\"" EXIT

source $(which overtest) mysql

mkfifo ${GNOCCHI_DATA}/out
cat > ${GNOCCHI_DATA}/gnocchi.conf <<EOF
[oslo_policy]
policy_file = ${VIRTUAL_ENV}/etc/gnocchi/policy.json
[api]
paste_config = ${VIRTUAL_ENV}/etc/gnocchi/api-paste.ini
[storage]
metric_processing_delay = 1
file_basepath = ${GNOCCHI_DATA}
driver = file
coordination_url = file://${GNOCCHI_DATA}
[indexer]
url = ${OVERTEST_URL/#mysql:/mysql+pymysql:}
EOF
gnocchi-upgrade --config-file ${GNOCCHI_DATA}/gnocchi.conf
gnocchi-metricd --config-file ${GNOCCHI_DATA}/gnocchi.conf &>/dev/null &
gnocchi-api --config-file ${GNOCCHI_DATA}/gnocchi.conf &> ${GNOCCHI_DATA}/out &
# Wait for Gnocchi to start
wait_for_line "Running on http://0.0.0.0:8041/" ${GNOCCHI_DATA}/out
export GNOCCHI_ENDPOINT=http://localhost:8041/

$*
