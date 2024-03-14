# inspired by: https://github.com/hollaugo/chatgpt-slack-app/blob/main/app.py
import json
import os
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import re
import urllib.parse

load_dotenv()  # take environment variables from .env
# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def get_username_from_id(client, user_id):
    result = client.users_info(user=user_id)  # Call the Slack API
    username = result['user']['name']
    return username 

#Message handler for Slack
@app.action({
    "action_id": "thumbs_up"
})
def handleMessageFeedbackThumbsUp(ack, body, say, respond, client):
    ack()

    user_id = body['user']['id']
    username = get_username_from_id(client, user_id)
    channel_id = body['channel']['id']
    message_ts = body['message']['ts']

    # Add thumbs-up reaction
    client.reactions_add(
        name="thumbsup",
        channel=channel_id,
        timestamp=message_ts
    )

    # Post feedback in thread
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=message_ts,
        text=f"Thank you for your feedback, {username}! \n\nYou rated the below response (:+1:)" 
    )


@app.action({
    "action_id": "thumbs_down"
})
def handleMessageFeedbackThumbsDown(ack, client, body, say, respond):
    ack()
    user_id = body['user']['id']
    username = get_username_from_id(client, user_id)
    channel_id = body['channel']['id']
    message_ts = body['message']['ts']
    # Add thumbs-up reaction
    client.reactions_add(
        name="thumbsup",
        channel=channel_id,
        timestamp=message_ts
    )
    # Post feedback in thread
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=message_ts,
        text=f"Thank you for your feedback, {username}! \n\nYou rated the below response (:-1:)" 
    )



def ask_question(base_url, question):
    """
    Asks a question to the specified API endpoint.

    Args:
        base_url (str): The base URL of your Flask API.
        question (str): The question to ask.

    Returns:
        dict: The JSON response from the API, or None if the request failed.
    """

    response = requests.get(base_url, params={'question': question})

    if response.status_code == 200:
        return response.json()
    else:
        print("API request failed")
        return None
def ask_question_in_thread(base_url, question, history):
    """
    Asks a question to the specified API endpoint.

    Args:
        base_url (str): The base URL of your Flask API.
        question (str): The question to ask.

    Returns:
        dict: The JSON response from the API, or None if the request failed.
    """
    encodedq = urllib.parse.quote(question)

    response = requests.post(base_url+'?question='+encodedq, json={'history': history})

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print("API request failed")
        return None
    
def generate_blocks(QUESTION):
    base_url = 'http://127.0.0.1:5000/rag_service'
    question = QUESTION
    result = ask_question(base_url, question)
    blocks = result['response-blocks']
    blocks.extend(result['sources-blocks'])
    blocks.extend(result['action-blocks'])
    return blocks
def generate_thread_blocks(QUESTION, HISTORY):
    base_url = 'http://127.0.0.1:5000/thread_rag_service'
    question = QUESTION
    history = HISTORY
    result = ask_question_in_thread(base_url, question, history)
    blocks = result['response-blocks']
    blocks.extend(result['sources-blocks'])
    return blocks
def extract_clean_question(mention_text):
    """
    Extracts the clean question from a Slack mention string, handling edge cases, 
    multiple mentions, and potentially strange inputs.

    Args:
        mention_text (str): The raw mention text.

    Returns:
        str: The extracted question, if one is found and can be isolated.
        None: Otherwise.
    """

    # Regex to match a Slack mention (more flexible than basic string find)
    mention_pattern = r"<@U[A-Z0-9]+>"

    # Remove all mentions using the regex
    text_without_mentions = re.sub(mention_pattern, "", mention_text)

    # Clean up potential extra spaces
    clean_question = text_without_mentions.strip()

    # Decide how to handle empty or very short strings after mention removal
    if len(clean_question) > 3:  # Arbitrary threshold; adjust as needed
        return clean_question
    else:
        return None  
@app.event("app_mention")
def handleAppMentionEvent(body, say, logger, client):
    event = body["event"]
    thread_ts = event.get("thread_ts", None) or event["ts"]
    if thread_ts is not None:
        print("ignore app_mention in thread, threads are handled separately")
        return
    # Immediate response with loading GIF
    loading_blocks = say(blocks=[
        {
            "block_id": "loading-0",
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*I'm thinking... Hold on a sec!*"
            }
        },
        {
            "block_id": "loading-1",
            "type": "image",
            "title": {
                "type": "plain_text",
                "text": "Loading..."
            },
            "image_url": "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif", 
            "alt_text": "Loading animation"
        }
    ], thread_ts=thread_ts)

    
    QUESTION = extract_clean_question(body['event']['text']) #replace the mention of your specific BOT before sending to LLM
    QUESTION=str(QUESTION).strip()
    client.chat_update(channel=event['channel'], ts=loading_blocks['ts'], blocks = generate_blocks(QUESTION))

def print_thread_message(message):
    text = message.get('text', '')
    # Option 1: Plaintext
    print(f"[Thread Message] by {message['user']}: {text}") 
@app.event("message")
def handle_message_event(body, logger):
    event = body["event"]
    if event.get("thread_ts"):  # Check if message is within a thread
        # Retrieve thread messages (might need pagination)
        result = app.client.conversations_replies(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            channel=event["channel"],
            ts=event["thread_ts"]
        )

        # Iterate over messages in the thread
        for message in result['messages']:
            print_thread_message(message)
        
        # thread asking
        app.client.chat_postMessage(
            channel=event["channel"],
            thread_ts=event["thread_ts"],
            blocks = generate_thread_blocks(event["text"],result['messages'])
        )

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()