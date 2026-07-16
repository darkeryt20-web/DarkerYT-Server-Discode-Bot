#!/bin/bash

# 1. CDTG extension එක background එකේ ක්‍රියාත්මක කරන්න
gunicorn -b 0.0.0.0:${PORT:-8000} CDTG:app &

# 2. අනෙක් bots ටික background එකේ ක්‍රියාත්මක කරන්න (& ලකුණ සමඟ)
python Verify.py &
python Spam_Blocker.py &
python Status.py &

# 3. අවසාන bot එක foreground එකේ run කරන්න (එතකොට container එක දිගටම run වෙනවා)
python Support_Ticket.py
