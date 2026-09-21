import asyncio
import logging
import os
import time
from typing import List

from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    ChallengeRequired,
    FeedbackRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
    RecaptchaChallengeForm,
    ReloginAttemptExceeded,
    SelectContactPointRecoveryForm,
)
from instagrapi.types import DirectMessage

from discord_insta.config import config

logger = logging.getLogger(__name__)

class InstagramManager:
    def __init__(self):
        self.cl = Client()
        self.cl.delay_range = [1, 3]
        self._bot_user_id = None
        self._username_cache = {}

    def login(self):
        """Synchronously load session or login."""
        if os.path.exists(config.session_file):
            logger.info("Loading Instagram session from %s", config.session_file)
            self.cl.load_settings(config.session_file)
            try:
                # Optional: verify session is still valid
                self.cl.get_timeline_feed()
            except Exception as e:
                logger.warning("Session invalid, re-logging in. Error: %s", e)
                self.cl.login(config.ig_username, config.ig_password)
                self.cl.dump_settings(config.session_file)
        else:
            logger.info("Logging into Instagram with password...")
            self.cl.login(config.ig_username, config.ig_password)
            self.cl.dump_settings(config.session_file)
            
        self._bot_user_id = self.cl.user_id
        logger.info(f"Successfully logged in as {config.ig_username}")
        self.cl.handle_exception = self._handle_exception

    def _handle_exception(self, client, e):
        """Handle Instagram API exceptions."""
        if isinstance(e, BadPassword):
            client.logger.exception(e)
            if client.relogin_attempt > 0:
                client.freeze(str(e), days=7)
                raise ReloginAttemptExceeded(e)
            client.settings = client.rebuild_client_settings()
            return client.dump_settings(config.session_file)
        elif isinstance(e, LoginRequired):
            client.logger.exception(e)
            client.login(config.ig_username, config.ig_password)
            return client.dump_settings(config.session_file)
        elif isinstance(e, ChallengeRequired):
            api_path = client.last_json.get("challenge", {}).get("api_path")
            if api_path == "/challenge/":
                client.dump_settings(config.session_file)
            else:
                try:
                    client.challenge_resolve(client.last_json)
                except ChallengeRequired as e:
                    client.freeze("Manual Challenge Required", days=2)
                    raise e
                except (
                    ChallengeRequired,
                    SelectContactPointRecoveryForm,
                    RecaptchaChallengeForm
                ) as e:
                    client.freeze(str(e), days=4)
                    raise e
                client.update_client_settings(client.get_settings())
            return True
        elif isinstance(e, FeedbackRequired):
            message = client.last_json.get("feedback_message", "")
            if "This action was blocked" in message or "restrict certain activity" in message:
                client.freeze(message, hours=12)
            elif "temporarily blocked" in message:
                client.freeze(message)
        elif isinstance(e, PleaseWaitFewMinutes):
            client.freeze(str(e), hours=1)
        raise e

    def fetch_recent_messages(self, limit: int = 20) -> List[DirectMessage]:
        """Synchronously fetch recent messages from the configured thread."""
        try:
            thread_messages = self.cl.direct_messages(config.ig_thread_id, limit)
            # Filter out bot's own messages
            filtered = [
                msg for msg in thread_messages 
                if str(msg.user_id) != str(self._bot_user_id)
            ]
            return filtered
        except RateLimitError:
            logger.warning("Rate limit exceeded while fetching messages.")
            time.sleep(60) # Short block inside the thread pool is fine
            return []
        except Exception as e:
            handled = False
            try:
                handled = self._handle_exception(self.cl, e)
                self.cl.dump_settings(config.session_file)
            except Exception as handle_e:
                logger.error("Error while handling exception: %s", handle_e)
            if not handled:
                logger.error("Unhandled exception fetching messages: %s", e)
            return []

    def get_username(self, user_id: str) -> str:
        """Synchronously fetch a username from user ID, using a cache."""
        user_id_str = str(user_id)
        if user_id_str in self._username_cache:
            return self._username_cache[user_id_str]
        
        try:
            user_info = self.cl.user_info(user_id_str)
            self._username_cache[user_id_str] = user_info.username
            return user_info.username
        except RateLimitError:
            logger.warning("Rate limit fetching username.")
            return f"User_{user_id_str}"
        except Exception as e:
            logger.error("Error fetching username for %s: %s", user_id_str, e)
            return f"User_{user_id_str}"

    def send_message(self, text: str):
        """Synchronously send a message to the configured thread."""
        try:
            self.cl.direct_send(text=text, thread_ids=[int(config.ig_thread_id)])
            logger.info("Sent message to IG thread %s", config.ig_thread_id)
        except RateLimitError:
            logger.warning("Rate limit exceeded while sending message.")
        except Exception as e:
            logger.error("Failed to send message to Instagram: %s", e)
            try:
                self._handle_exception(self.cl, e)
            except Exception:
                pass

# Global instance
ig_manager = InstagramManager()

# Async wrappers
async def async_login():
    await asyncio.to_thread(ig_manager.login)

async def async_fetch_recent_messages(limit: int = 20) -> List[DirectMessage]:
    return await asyncio.to_thread(ig_manager.fetch_recent_messages, limit)

async def async_get_username(user_id: str) -> str:
    return await asyncio.to_thread(ig_manager.get_username, user_id)

async def async_send_message(text: str):
    await asyncio.to_thread(ig_manager.send_message, text)
