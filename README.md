# Quote-a-Day Bot

![image](https://github.com/user-attachments/assets/f2b48dc0-4ec3-4ed7-9726-805381ea23dd)

<div align="center">
  <a href="https://shipwrecked.hackclub.com/?t=ghrm" target="_blank">
    <img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/739361f1d440b17fc9e2f74e49fc185d86cbec14_badge.png" 
         alt="This project is part of Shipwrecked, the world's first hackathon on an island!" 
         style="width: 35%;">
  </a>
</div>


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
