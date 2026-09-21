import logging
import sys

from dotenv import load_dotenv


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    # Load environment variables from .env if present
    load_dotenv()
    
    # Setup basic logging
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Discord-Insta Bot...")
    
    from discord_insta.config import config
    from discord_insta.discord_bot import bot

    config.validate_required()

    try:
        bot.run(config.discord_token)
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
    except Exception as e:
        logger.error("Error running bot: %s", e)

if __name__ == "__main__":
    main()
