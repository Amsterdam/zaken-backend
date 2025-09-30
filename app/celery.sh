#!/usr/bin/env bash
set -e

watchmedo auto-restart --directory=./ --pattern="*.py;*.bpmn" --recursive -- celery -A config worker -l info
