# Discord-Insta

A modern, robust Python bot that seamlessly synchronizes messages between an Instagram Direct Message thread and a Discord channel.

## Important Disclaimer: Instagram ToS & Account Risk

> **⚠️ WARNING:** This bot uses `instagrapi`, an unofficial wrapper for the private Instagram API. Instagram aggressively combats unofficial automated access.
> **DO NOT USE YOUR PRIMARY PERSONAL INSTAGRAM ACCOUNT.** It has a high risk of being temporarily or permanently banned. Create and use a dedicated "burner" account for this bot and invite that account to the desired Instagram group chat.

## Features

- **Asynchronous Architecture:** Uses `discord.py` 2.x and thread pooling to ensure the Discord bot remains responsive while polling Instagram.
- **Rich Embeds:** Instagram messages, images, and videos are forwarded to Discord using stylized embeds.
- **Two-Way Sync:** Sends messages from the Discord channel back to the Instagram thread.
- **Persistent Sessions:** Reuses Instagram sessions to minimize login attempts and evade spam filters.
- **Resilient:** Built-in rate limit handling, caching, and exponential backoff.

## Prerequisites

- Python 3.12+
- A dedicated burner Instagram account.
- A Discord Bot Token with the **Message Content Intent** enabled (configurable in the Discord Developer Portal).

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MrHitMan1/discord-insta.git
   cd discord-insta
   ```

2. **Install dependencies:**
   ```bash
   pip install .
   ```
   *(For development, install with `pip install ".[dev]"`)*

3. **Configure the Environment:**
   Copy `.env.example` to `.env` and fill in the values:
   ```bash
   cp .env.example .env
   ```
   
   **Configuration Table:**
   
   | Variable | Description |
   |----------|-------------|
   | `IG_USERNAME` | Burner Instagram account username |
   | `IG_PASSWORD` | Burner Instagram account password |
   | `IG_THREAD_ID` | The numeric ID of the Instagram group chat |
   | `DISCORD_TOKEN` | Your Discord bot token |
   | `DISCORD_CHANNEL_ID` | The numeric ID of the Discord channel |

   *Note: To get the `IG_THREAD_ID`, open Instagram on the web, navigate to the chat, and copy the number at the end of the URL (e.g., `https://instagram.com/direct/t/123456789012345`).*

## Running the Bot

Run the bot directly using Python:
```bash
python -m discord_insta.main
```

Or using Docker:
```bash
docker build -t discord-insta .
docker run --env-file .env discord-insta
```

## Known Limitations
- The bot polls Instagram every 5 minutes (default) to avoid rate limits. It is not strictly real-time.
- Unofficial Instagram API challenges (like SMS verification) may require manual intervention. The bot attempts to save the session to `session.json` to avoid this when possible.
