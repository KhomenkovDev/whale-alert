# KhomDev Web3 Whale Alert

Real-time monitoring of high-value cryptocurrency transactions (Whales) across Ethereum, BNB Chain, Polygon, and Avalanche. Built with Django, Web3.py, and Django Channels.

## Features

- **Multi-Chain Monitoring**: Scans 4 blockchains (ETH, BNB, POL, AVAX) for large stablecoin transfers (USDC, USDT, DAI, BUSD)
- **Real-Time WebSocket Feed**: Live updates pushed to the browser via Django Channels — no polling
- **AI-Powered Reports**: Each whale transaction analyzed by Claude AI for intent, market impact, risk level, and signals
- **Smart Scan Tracking**: Tracks the last scanned block per chain — no wasteful re-scans
- **Live Dashboard**: Glassmorphism UI with chain filtering, animated stats, theme toggle (dark/light), and toast notifications
- **Rate-Limited AI Endpoint**: Prevents API credit abuse with configurable rate limiting

## Architecture

```
Browser (ES6 modules)
    ↕ WebSocket + REST API
Django ASGI (daphne)
    ├── core app (models, views, consumers, WebSocket routing)
    └── monitor app (Celery tasks for blockchain scanning)
    ↕ Redis
Celery Worker + Celery Beat (every 15s)
    ↕ RPC
Ethereum / BNB Chain / Polygon / Avalanche
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Django 4.2.16 |
| ASGI | Daphne 4.1.2 |
| WebSocket | Django Channels 4.1 (Redis channel layer for production) |
| Task Queue | Celery 5.4 + Redis |
| Blockchain | Web3.py 6.20.1 |
| AI | Anthropic Claude API |
| Frontend | Vanilla JS (ES6 modules), CSS custom properties |
| Database | SQLite (dev), PostgreSQL-ready |
| Linting | ruff |
| Type Checking | mypy |
| Testing | pytest (30+ tests) |

## Quick Start

### Prerequisites

- Python 3.11+
- Redis (for Celery + Channels in production)
- UV (recommended) or pip

### Setup

```bash
# Clone and enter the project
git clone <repo> && cd whale-alert

# Create environment
uv venv && source .venv/bin/activate

# Install dependencies
uv sync

# Copy env config
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY, RPC endpoints, etc.

# Run migrations
python manage.py migrate

# Start the dev server
python manage.py runserver

# In another terminal, start Celery (for blockchain scanning):
celery -A whale_alert worker -l info
celery -A whale_alert beat -l info

# Seed demo transactions (optional):
python manage.py shell -c "from monitor.tasks import seed_demo_transactions; seed_demo_transactions()"
```

### Docker (Production)

```bash
docker compose up --build
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `True` | Django debug mode |
| `SECRET_KEY` | *(dev-only)* | Django secret key |
| `ALLOWED_HOSTS` | `*` | Allowed hosts |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | Database URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `CHANNEL_LAYER_TYPE` | `memory` | `memory` or `redis` |
| `ETHEREUM_RPC_URL` | — | Ethereum RPC endpoint |
| `BNB_RPC_URL` | — | BNB Chain RPC endpoint |
| `POLYGON_RPC_URL` | — | Polygon RPC endpoint |
| `AVALANCHE_RPC_URL` | — | Avalanche RPC endpoint |
| `WHALE_THRESHOLD_USD` | `1000000` | Minimum USD value for alert |
| `ANTHROPIC_API_KEY` | — | Claude API key for AI reports |
| `AI_REPORT_RATE_LIMIT` | `10/hour` | Rate limit for AI report endpoint |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/api/transactions/?chain=&limit=` | GET | Recent transactions (JSON) |
| `/api/stats/?chain=` | GET | Aggregate statistics |
| `/api/report/<id>/` | POST | Generate/cache AI report |
| `/health/` | GET | DB + Redis health check |
| `/ws/whales/` | WebSocket | Live whale alerts |

## Testing

```bash
uv run pytest
```

## License

MIT
