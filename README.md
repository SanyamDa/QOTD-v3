# Quote-a-Day Bot

![image](https://github.com/user-attachments/assets/f2b48dc0-4ec3-4ed7-9726-805381ea23dd)


A simple Telegram bot that sends one finance/entrepreneurship quote every morning.

## Features

- Daily quotes at 07:00 Bangkok time (ICT).
- `/pause`: Stop receiving daily quotes.
- `/resume`: Resume receiving daily quotes.
- `/random`: Get a random quote on demand.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd quote-of-the-day-bot
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your Telegram bot token:
    ```
    BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
    ```

4.  **Run the bot:**
    ```bash
    python bot.py
    ```

## Deployment

The bot is designed to be deployed as a single Docker container on [Fly.io](https://fly.io/).

---

*This is a minimal side-project with a focus on delivering value with low maintenance.*
