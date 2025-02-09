import requests
from NotionAPI import NotionMarketingAPI
from MarketingAPI import MarketingRequestCollection, MarketingRequest
import os
import dotenv
dotenv.load_dotenv("tokens.env")

def send_slack_webhook_message(webhook_url, message, username="Notifier", icon_emoji=":robot_face:", markdown=True):
    """
    Sends a message to a Slack channel via an incoming webhook.

    :param webhook_url: The Slack webhook URL.
    :param message: The text message to send.
    :param username: The username to display as the sender (optional).
    :param icon_emoji: The emoji icon to use as the sender's avatar (optional).
    :raises Exception: If the request to Slack fails.
    """
    payload = {
        "text": message,
        "username": username,
        "icon_emoji": icon_emoji,
        "mrkdwn": markdown,
    }
    
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise Exception(
            f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}"
        )
    return response

def generate_weekly_backlog_graphics(webhook_url: str):
    x = NotionMarketingAPI(os.getenv("NOTION_API_KEY"), os.getenv("COLLECTION_ID"), os.getenv("SPACE_ID"), os.getenv("COLLECTION_VIEW_ID"), os.getenv("USER_ID"))

    y = x.query_marketing_requests()
    msg = ""
    for req in y.fetch_requests_by_status("Not Started"):
        msg += req.to_markdown() + "\n"
    
    send_slack_webhook_message(webhook_url, msg, username="Marketing Bot", icon_emoji=":chart_with_upwards_trend:", markdown=True)

def generate_posting_schedule(webhook_url: str):
    import datetime
    x = NotionMarketingAPI(os.getenv("NOTION_API_KEY"), os.getenv("COLLECTION_ID"), os.getenv("SPACE_ID"), os.getenv("COLLECTION_VIEW_ID"), os.getenv("USER_ID"))

    y = x.query_marketing_requests()

    filtered = y.filter_by_criterion(
        lambda req: req.status == "Confirmed",
        lambda req: req.is_this_week()
    )
    filtered.sort()
    msg = f"Posting Schedule for The Week of {datetime.datetime.now().strftime('%Y-%m-%d')}:\n"
    for req in filtered:
        msg += req.to_markdown() + "\n"
    
    send_slack_webhook_message(webhook_url, msg, username="Marketing Bot", icon_emoji=":chart_with_upwards_trend:", markdown=True)


# === Example Usage ===
if __name__ == "__main__":
    # Replace this URL with your actual Slack incoming webhook URL
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    try:
        generate_posting_schedule(webhook_url)
    except Exception as e:
        print(f"An error occurred: {e}")



