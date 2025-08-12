#!/bin/bash

rm -rf ./output/newrelic/*

NEW_RELIC_ACCOUNT_ID=xxx NEW_RELIC_API_TOKEN=xxx python3 main.py --local