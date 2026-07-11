#!/bin/bash

# අතිරේක extension/web service එක ක්‍රියාත්මක කරන්න (background එකේ)
gunicorn -b 0.0.0.0:${PORT:-8000} CDTG:app &

# Discord Bot එක ක්‍රියාත්මක කරන්න
python Verification.py
