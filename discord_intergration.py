import discord
import json
from discord.ext import commands, tasks
import instagrapi
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword, ReloginAttemptExceeded, ChallengeRequired,
    SelectContactPointRecoveryForm, RecaptchaChallengeForm,
    FeedbackRequired, PleaseWaitFewMinutes, LoginRequired,RateLimitError
)   
import time
import os

# Instagram login credentials
USERNAME = ''
PASSWORD = ''
INSTAGRAM_THREAD_ID = 340282366841710301281157199448462624174
SESSION_FILE = 'session.json'
LAST_MESSAGE_FILE = 'last_message.json'

# Discord Bot setup
DISCORD_TOKEN = ''
DISCORD_CHANNEL_ID =   # Replace with your channel ID

# Login to Instagram with session cache
def login_with_session_cache(username, password, session_file):
    cl = Client()
    if os.path.exists(session_file):
        cl.load_settings(session_file)
    else:
        cl.login(username, password)
        cl.dump_settings(session_file)
    return cl

def handle_exception(client, e):
    if isinstance(e, BadPassword):
        client.logger.exception(e)
        client.set_proxy(client.next_proxy().href)
        if client.relogin_attempt > 0:
            client.freeze(str(e), days=7)
            raise ReloginAttemptExceeded(e)
        client.settings = client.rebuild_client_settings()
        return client.dump_settings(SESSION_FILE)
    elif isinstance(e, LoginRequired):
        client.logger.exception(e)
        login_with_session_cache(USERNAME,PASSWORD,SESSION_FILE)
        return client.dump_settings(SESSION_FILE)
    elif isinstance(e, ChallengeRequired):
        api_path = client.last_json.get("challenge", {}).get("api_path")
        if api_path == "/challenge/":
            client.set_proxy(client.next_proxy().href)
            client.dump_settings(SESSION_FILE)
        else:
            try:
                client.challenge_resolve(client.last_json)
            except ChallengeRequired as e:
                client.freeze("Manual Challenge Required", days=2)
                raise e
            except (
                ChallengeRequired,
                SelectContactPointRecoveryForm,
                RecaptchaChallengeForm,
            ) as e:
                client.freeze(str(e), days=4)
                raise e
            client.update_client_settings(client.get_settings())
        return True
    elif isinstance(e, FeedbackRequired):
        message = client.last_json["feedback_message"]
        if "This action was blocked. Please try again later" in message:
            client.freeze(message, hours=12)
            # client.settings = client.rebuild_client_settings()
            # return client.update_client_settings(client.get_settings())
        elif "We restrict certain activity to protect our community" in message:
            # 6 hours is not enough
            client.freeze(message, hours=12)
        elif "Your account has been temporarily blocked" in message:
            """
            Based on previous use of this feature, your account has been temporarily
            blocked from taking this action.
            This block will expire on 2020-03-27.
            """
            client.freeze(message)
    elif isinstance(e, PleaseWaitFewMinutes):
        client.freeze(str(e), hours=1)
    raise e

cl = login_with_session_cache(USERNAME,PASSWORD,SESSION_FILE)
cl.handle_exception = handle_exception # type: ignore
cl.delay_range = [1, 3]


# Fetch recent threads with detailed debug info
def fetch_recent_threads(cl,limit=20):
    if not cl:
        print("Client not logged in. Cannot fetch recent threads.")
        return []
    else:
        print("Fetching threads...")
        try:
            inbox = cl.direct_threads()
            print(f"Found {len(inbox)} threads.")
            messages = []
            
            print(f"Fetching messages from thread ID: {INSTAGRAM_THREAD_ID}")
            thread_messages = cl.direct_messages(INSTAGRAM_THREAD_ID,limit)
            print(f"Found {len(thread_messages)} messages in thread ID: {INSTAGRAM_THREAD_ID}")
            filtered_messages = [msg for msg in thread_messages if msg.user_id != '62196248090']
            messages.extend(filtered_messages)

            return messages
        except LoginRequired:
            print("Login required. Re-logging in...")
            cl.login(USERNAME, PASSWORD)
            return fetch_recent_threads(cl)
        except RateLimitError:
            print("Rate limit exceeded. Waiting for a while before retrying...")
            time.sleep(300)  # Wait for 5 minutes before retrying
            return fetch_recent_threads() # type: ignore
        except Exception as e:
            handled = handle_exception(cl, e)
            cl.dump_settings(SESSION_FILE)
        if not handled:
            # Handle the exception further or re-raise it
            raise

def fetch_media_messages(threads):
    
    media_messages = []

    for thread in threads:
        for message in thread.messages:
            if message.item_type in ["media", "raven_media", "video_call_event", "reel_share", "clip"]:
                media_messages.append(message)

    return media_messages

async def send_media_to_discord(message):
    channel = bot.get_channel(DISCORD_CHANNEL_ID)

    if message.item_type in ["media", "raven_media"]:
        media_url = message.media_url
        await channel.send(f"Media from Instagram: {media_url}") # type: ignore
    elif message.item_type == "reel_share":
        reel_url = message.reel_share.link
        await channel.send(f"Reel from Instagram: {reel_url}") # type: ignore
    elif message.item_type == "clip":
        clip_url = message.clip.link
        await channel.send(f"Clip from Instagram: {clip_url}") # type: ignore

# Fetch username by user ID
def fetch_instagram_username(user_id):
    if user_id == 2147554699:
        return 'Midhun Antony'
    elif user_id == '51953998893':
        return "Amith"
    elif user_id == '62196248090':
        return "bot"
    elif user_id == '52238548444':
        return 'Sahl'
    else:   
        try:
            user_info = cl.user_info(user_id)
            return user_info.username
        except RateLimitError:
            print("Rate limit exceeded while fetching username. Waiting for a while before retrying...")
            time.sleep(300)  # Wait for 5 minutes before retrying
            return fetch_instagram_username(user_id)
        except Exception as e:
            print(f"Failed to fetch username for user ID {user_id}: {e}")
            handled = handle_exception(cl, e)
        if not handled:
            # Handle the exception further or re-raise it
            raise
        

# Function to send message to    Instagram group
def send_message_to_instagram_group(thread_id, message_text):
    try:
        cl.direct_send(text=message_text, thread_ids=[thread_id])
        print(f"Sent message to Instagram thread ID: {thread_id}")
    except RateLimitError:
        print("Rate limit exceeded while sending message. Waiting for a while before retrying...")
        time.sleep(300)  # Wait for 5 minutes before retrying
        send_message_to_instagram_group(thread_id, message_text)
    except Exception as e:
        print(f"Failed to send message to Instagram: {e}")
        handled = handle_exception(cl, e)
    

# Load the last message ID sent to Discord
def load_last_message_id():
    if os.path.exists(LAST_MESSAGE_FILE):
        with open(LAST_MESSAGE_FILE, 'r') as f:
            return json.load(f).get('last_message_id')
    return None

# Save the last message ID sent to Discord
def save_last_message_id(message_id):
    with open(LAST_MESSAGE_FILE, 'w') as f:
        json.dump({'last_message_id': message_id}, f)

# Discord Bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    fetch_and_send_messages.start(10)

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if the message is in the specific channel
    if message.channel.id == DISCORD_CHANNEL_ID:
        username = message.author.name
        content = message.content
        full_message = f"{username}: {content}"
        send_message_to_instagram_group(INSTAGRAM_THREAD_ID, full_message)

# Function to fetch recent messages from Instagram and send to Discord
@tasks.loop(minutes=5)

async def fetch_and_send_messages(message_limit):
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    await channel.send('Fetching new messages') # type: ignore
    messages = fetch_recent_threads(cl,message_limit)
    last_message_id = load_last_message_id()
    # Filter messages that were sent after the last sent message
    new_messages = [m for m in messages if m.id > last_message_id] if last_message_id else messages
    # Sort messages by timestamp to send them in ascending order
    sorted_messages = sorted(new_messages, key=lambda m: m.timestamp)
    for message in sorted_messages:
        username = fetch_instagram_username(message.user_id)
        await channel.send(f"{username}: {message.text}") # type: ignore
    # Update the last message ID sent to Discord
    if sorted_messages:
        save_last_message_id(sorted_messages[-1].id)


bot.run(DISCORD_TOKEN)


