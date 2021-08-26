#!/bin/bash

dropdb zaken --force --if-exists
createdb zaken

# Create user with permissions
psql -d zaken -c "CREATE USER zaken WITH PASSWORD 'insecure' CREATEDB" >/dev/null 2>&1
psql -d zaken -c "CREATE EXTENSION pg_trgm" >/dev/null 2>&1
