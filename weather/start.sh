#!/bin/bash

if [ -z "${ENVIRONMENT}" ]
then
    ENVIRONMENT="dev"
fi


run_test() {
    py.test test.py
}

run_local() {
    python -u main.py
}

echo -ne "\n\n##\n##\tRUNNING WITH ENVIRONMENT=\"${ENVIRONMENT}\"\n##\n\n"
if [ "${ENVIRONMENT}" == "test" ]
then
    run_test
fi

if [ "${ENVIRONMENT}" == "dev" ]
then
    run_local
fi
