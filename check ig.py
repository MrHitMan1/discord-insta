from instagrapi import Client

# Instagram login credentials
USERNAME = ''
PASSWORD = ''



# Login to Instagram
cl = Client()
login_status = cl.login(USERNAME, PASSWORD)
print(f"Login status: {login_status}")

def fetch_recent_messages():
    print("Fetching threads...")
    try:
        inbox = cl.direct_threads()
        print(f"Found {len(inbox)} threads.")
        messages = []
        for thread in inbox:
            print(f"Fetching messages from thread ID: {thread.id}")
            thread_messages = cl.direct_thread(thread.id,40)
            filtered= [msg for msg in thread_messages]
            filtered2= [reels for reels in thread_messages]
            print(filtered)
            print(f"Found  messages in thread ID: {thread.id}")
            messages.extend(thread_messages)
        return messages
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Fetch and print messages
messages = fetch_recent_messages()
print(f"Total messages fetched: {len(messages)}")
for message in messages:
    print(f"From: {message.user_id}, Message: {message.text}")