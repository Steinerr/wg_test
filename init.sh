#!/usr/bin/env bash

psql -U postgres -c "CREATE USER wg_stat WITH ENCRYPTED PASSWORD 'qwerty';CREATE DATABASE wg_stat;GRANT ALL ON DATABASE wg_stat TO wg_stat;"