from NotionAPI import NotionMarketingAPI
from MarketingAPI import MarketingRequestCollection, MarketingRequest
import os
import dotenv
dotenv.load_dotenv("tokens.env")

x = NotionMarketingAPI(os.getenv("NOTION_API_KEY"), os.getenv("COLLECTION_ID"), os.getenv("SPACE_ID"), os.getenv("COLLECTION_VIEW_ID"), os.getenv("USER_ID"))

y = x.query_marketing_requests()

for req in y.fetch_requests_by_status("Not Started"):
    print(req)