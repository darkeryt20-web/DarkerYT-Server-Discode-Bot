#!/bin/bash

# CDTG extension එක background එකේ ක්‍රියාත්මක කරන්න
gunicorn -b 0.0.0.0:${PORT:-8000} CDTG:app &

# Verify.py bot එක ක්‍රියාත්මක කරන්න
python Verify.py

