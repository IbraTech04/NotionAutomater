from datetime import datetime
from flask import Flask, request, jsonify
import dotenv

import threading
import time
import os

from NotionAPI import NotionMarketingAPI
from MarketingAPI import MarketingRequest

dotenv.load_dotenv("tokens.env")

app = Flask(__name__)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Global cache for Notion API data
notion_data = None

def fetch_notion_data():
    """Fetch marketing requests from Notion and update the global cache."""
    notion_api = NotionMarketingAPI(
        os.getenv("NOTION_API_KEY"), 
        os.getenv("COLLECTION_ID"), 
        os.getenv("SPACE_ID"), 
        os.getenv("COLLECTION_VIEW_ID"), 
        os.getenv("USER_ID")
    )
    global notion_data
    while True:
        try:
            notion_data = notion_api.query_marketing_requests()
            print("Updated Notion data: " + str(notion_data))
        except Exception as e:
            print("Error fetching Notion data:", e)
        
        time.sleep(60)  # Wait 60 seconds before updating again

# Start background thread
notion_thread = threading.Thread(target=fetch_notion_data, daemon=True)
notion_thread.start()

@app.route("/getbacklog", methods=["POST"])
def generate_weekly_backlog_graphics():

    # Use the cached Notion data

    filtered_data = notion_data.fetch_requests_by_status("Not Started")

    msg = "\n".join([request.to_markdown() for request in filtered_data])


    return jsonify({
        "response_type": "in_channel",
        "text": msg,
        "mkdwn": True
    })

@app.route("/getweeklyschedule", methods=["POST"])
def generate_weekly_posting_schedule():
    # filter data based on:
    # Requests that are CONFIRMED and WILL BE POSTED this week

    filtered_data = notion_data.filter_by_criterion(
        lambda req: req.status == "Confirmed",
        lambda req: req.is_this_week()
    )

    filtered_data.sort()

    msg = f"Posting Schedule for The Week of {datetime.now().strftime('%Y-%m-%d')}:\n"

    msg += "\n".join([request.to_markdown() for request in filtered_data])

    return jsonify({
        "response_type": "in_channel",
        "text": msg,
        "mkdwn": True
    })

if __name__ == "__main__":
    app.run(port=3000)
