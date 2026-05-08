# KhomDev Web3 Whale Alert 🐳
![Whale Alert](screenshots/Screenshot%202026-04-20%20at%2015.49.06.png)

Real-time monitoring of high-value cryptocurrency transactions (Whales) across major blockchains. Built with Django and Web3.py.

## Features
- **Real-Time Monitoring**: Tracks large transfers of USDC, ETH, and other major tokens.
- **Smart Contract Integration**: Directly interacts with Ethereum/Polygon smart contracts.
- **Automated Alerts**: Persists significant transactions to a local dashboard.
- **WebSocket Streaming**: Real-time updates delivered via Django Channels.

## Tech Stack
- **Backend**: Python, Django
- **Blockchain**: Web3.py
- **Frontend**: Vanilla HTML/CSS (Glassmorphism)
- **Database**: SQLite (Local)

## Getting Started
1. `pip install -r requirements.txt`
2. Set up `GEMINI_API_KEY` in `.env`
3. `python manage.py migrate`
4. `python manage.py runserver`
