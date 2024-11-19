#!/bin/bash
# Starting the backend

cd /opt/CSULB_Calendar
source /opt/CSULB_Calendar/venv/bin/activate

uvicorn app.main:app --host 127.0.0.1 --port 8000
