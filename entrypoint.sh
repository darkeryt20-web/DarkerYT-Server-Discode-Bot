#!/bin/bash

# 1. CDTG වෙබ් සර්වර් එක Background එකේ Run කිරීම (& ලකුණ අත්‍යවශ්‍යයි)
gunicorn -b 0.0.0.0:${PORT:-8000} CDTG:app &

# 2. ඊටපස්සේ Discord Bot එක Foreground එකේ Run කිරීම
python bot.py
