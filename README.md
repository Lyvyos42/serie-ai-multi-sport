# AI Multi-Sport Prediction Bot ⚽🎾🏀

An AI-powered Telegram bot that providing predictions, match analysis, and live standings for Football, Tennis, and Basketball.

## 🚀 Features

- **Multi-Sport Support**: Football, Tennis, and Basketball.
- **AI Predictions**: Advanced analysis for match outcomes, spreads, and scores.
- **Live Data**: Today's matches and games fetched via API-SPORTS.
- **Standings & Rankings**: League standings for Football/Basketball and ATP/WTA rankings for Tennis.
- **Database Tracking**: All user predictions are saved to PostgreSQL with accuracy tracking.
- **Admin Panel**: Statistics and management tools for administrators.

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Framework**: `python-telegram-bot`
- **Database**: PostgreSQL (via SQLAlchemy)
- **Deployment**: Optimized for Railway
- **APIs**: API-SPORTS (Football, Tennis, Basketball)

## 📋 Prerequisites

- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- API-SPORTS Key (from [api-sports.io](https://api-sports.io/))
- PostgreSQL Database

## ⚙️ Environment Variables

Set the following environment variables in your deployment environment (e.g., Railway):

| Variable | Description |
| --- | --- |
| `BOT_TOKEN` | Your Telegram Bot API token |
| `SPORTS_API_KEY` | Your API-SPORTS key |
| `DATABASE_URL` | PostgreSQL connection string |
| `ADMIN_USER_ID` | Comma-separated Telegram IDs of admins |
| `INVITE_ONLY` | Set to `true` to restrict access |
| `FOOTBALL_DATA_API_KEY` | (Optional) Legacy football API key |

## 📦 Local Setup

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd <repo-name>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   python init_database.py
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

## 🚢 Deployment (Railway)

1. Connect your GitHub repository to [Railway](https://railway.app/).
2. Add a PostgreSQL database to your project.
3. Add the required Environment Variables.
4. The `Procfile` will automatically handle the startup command.

---

*Note: For the best experience, ensure your PostgreSQL URL starts with `postgresql://` (if using Railway's default `postgres://`, the code handles the conversion).*
