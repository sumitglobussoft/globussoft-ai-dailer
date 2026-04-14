#!/bin/bash
cd /home/callified-ftp/callified_ai
exec /home/callified-ftp/callified_ai/venv/bin/uvicorn main:app \
  --host 0.0.0.0 \
  --port 8001 \
  --loop uvloop \
  --log-level info
