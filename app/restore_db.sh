#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No file supplied"
    exit 1
fi

if [ -f "$1" ]; then
    echo "$1 exists."
else
    echo "$1 does not exist."
    exit 1
fi

if [[ ${ENVIRONMENT} == "production" ]]; then
    echo "The env '$env' does not allow restores."
    exit 1
fi


db_host="${DATABASE_HOST}"
db_name="${DATABASE_NAME}"
db_user="${DATABASE_USER}"

# drop all tables and recreate schema
PGPASSWORD="${DATABASE_PASSWORD}" psql -h $db_host -d $db_name -U $db_user -c "DROP SCHEMA public CASCADE"
PGPASSWORD="${DATABASE_PASSWORD}" psql -h $db_host -d $db_name -U $db_user -c "CREATE SCHEMA public"

# import dump
PGPASSWORD="${DATABASE_PASSWORD}" psql -h $db_host -d $db_name -U $db_user -f $1

echo "Udated"
