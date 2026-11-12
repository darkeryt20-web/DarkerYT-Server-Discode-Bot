#!/bin/bash

# 1. CDTG extension එක background එකේ ක්‍රියාත්මක කරන්න
gunicorn -b 0.0.0.0:${PORT:-8000} python bot.py 


# 2. අනෙක් bots ටික background එකේ ක්‍රියාත්මක කරන්න (& ලකුණ සමඟ)

