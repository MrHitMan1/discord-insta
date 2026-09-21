import json
import logging
import os

import discord
from discord.ext import commands, tasks

from discord_insta.config import config
from discord_insta.instagram_client import (
    async_fetch_recent_messages,
    async_get_username,
    async_login,
    async_send_message,
)

logger = logging.getLogger(__name__)

class DiscordInstaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.last_message_id = self._load_last_message_id()

    def _load_last_message_id(self) -> str | None:
        if os.path.exists(config.last_message_file):
            with open(config.last_message_file, "r") as f:
                data = json.load(f)
                return data.get("last_message_id")
        return None

    def _save_last_message_id(self, message_id: str):
        with open(config.last_message_file, "w") as f:
            json.dump({"last_message_id": message_id}, f)
        self.last_message_id = message_id

    async def setup_hook(self):
        logger.info("Initializing Instagram client...")
        try:
            await async_login()
            logger.info("Instagram client initialized.")
        except Exception as e:
            logger.error("Failed to initialize Instagram client: %s", e)
            
        self.poll_instagram.start()

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if message.channel.id == config.discord_channel_id:
            # Forward Discord message to Instagram
            username = message.author.name
            content = message.content
            
            # Append attachment URLs if any
            if message.attachments:
                attachments = " ".join([att.url for att in message.attachments])
                content = f"{content}\n{attachments}".strip()
                
            full_message = f"{username}: {content}"
            logger.info("Forwarding message from Discord to Instagram: %s", full_message)
            await async_send_message(full_message)

        await self.process_commands(message)

    @tasks.loop(seconds=config.poll_interval_seconds)
    async def poll_instagram(self):
        channel = self.get_channel(config.discord_channel_id)
        if not channel:
            logger.warning("Discord channel %s not found. Waiting...", config.discord_channel_id)
            return

        logger.debug("Polling Instagram for new messages...")
        messages = await async_fetch_recent_messages(limit=20)
        
        if not messages:
            return

        # Filter messages newer than the last sent message
        # Instagram message IDs are strings of integers, can be sorted directly or cast to int
        new_messages = []
        if self.last_message_id:
            for m in messages:
                try:
                    if int(m.id) > int(self.last_message_id):
                        new_messages.append(m)
                except ValueError:
                    # Fallback if id isn't strictly numeric
                    if m.id != self.last_message_id:
                        new_messages.append(m)
        else:
            new_messages = messages

        if not new_messages:
            return

        # Sort messages by timestamp ascending
        sorted_messages = sorted(new_messages, key=lambda m: m.timestamp)

        for msg in sorted_messages:
            username = await async_get_username(msg.user_id)
            text = msg.text or ""
            
            embed = discord.Embed(
                description=text,
                color=discord.Color.purple(),
                timestamp=msg.timestamp
            )
            embed.set_author(name=username, icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Instagram_logo_2016.svg/2048px-Instagram_logo_2016.svg.png")

            # Handle media types
            if msg.item_type in ["media", "raven_media"]:
                if hasattr(msg, "media_url") and msg.media_url:
                    embed.set_image(url=str(msg.media_url))
                embed.add_field(name="Attachment", value="Media from Instagram", inline=False)
            elif msg.item_type == "reel_share":
                link = (msg.reel_share.link if hasattr(msg, "reel_share") 
                        and msg.reel_share else "Unknown link")
                embed.add_field(name="Reel Share", value=str(link), inline=False)
            elif msg.item_type == "clip":
                link = msg.clip.link if hasattr(msg, "clip") and msg.clip else "Unknown link"
                embed.add_field(name="Clip", value=str(link), inline=False)
            elif msg.item_type == "video_call_event":
                embed.add_field(name="Call Event", value="Video Call", inline=False)

            try:
                await channel.send(embed=embed)
            except discord.DiscordException as e:
                logger.error("Failed to send message to Discord: %s", e)

        # Update last message ID
        if sorted_messages:
            self._save_last_message_id(sorted_messages[-1].id)

    @poll_instagram.before_loop
    async def before_poll_instagram(self):
        await self.wait_until_ready()

bot = DiscordInstaBot()
