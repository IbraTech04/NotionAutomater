import requests
from MarketingAPI import MarketingRequestCollection, MarketingRequest


class NotionMarketingAPI:
    """
    A simple wrapper for querying Notion collections (e.g., marketing requests)
    via Notion's private API.
    """
    
    BASE_URL = "https://www.notion.so/api/v3/"

    def __init__(self, notion_api_key, collection_id, space_id, collection_view_id, user_id, user_timezone="America/Toronto"):
        """
        Initialize the API wrapper.

        :param notion_api_key: Your Notion API key.
        :param collection_id: The ID of the Notion collection.
        :param space_id: The ID of the Notion workspace/space.
        :param collection_view_id: The ID of the collection view.
        :param user_id: Your user ID as required by the API.
        :param user_timezone: The user's time zone (default is "America/Toronto").
        """
        self.notion_api_key = notion_api_key
        self.collection_id = collection_id
        self.space_id = space_id
        self.collection_view_id = collection_view_id
        self.user_id = user_id
        self.user_timezone = user_timezone

        # Set up the default headers and query params.
        self.headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        self.params = {"src": "initial_load"}

    def query_marketing_requests(self, limit=50, sort_fields=None, search_query=""):
        """
        Query the Notion collection to retrieve marketing requests.

        :param limit: Maximum number of records to fetch.
        :param sort_fields: A list of dictionaries to define sort order.
                            Each dictionary should contain 'property' and 'direction' keys.
                            Defaults to sorting by 'nSLy' then '{Rrz', both ascending.
        :param search_query: A search string to filter records.
        :return: A sorted MarketingRequestCollection instance.
        :raises: requests.HTTPError if the API call fails.
        """
        # Default sort fields if none provided.
        if sort_fields is None:
            sort_fields = [
                {"property": "nSLy", "direction": "ascending"},
                {"property": "{Rrz", "direction": "ascending"},
            ]

        payload = {
            "source": {
                "type": "collection",
                "id": self.collection_id,
                "spaceId": self.space_id,
            },
            "collectionView": {
                "id": self.collection_view_id,
                "spaceId": self.space_id,
            },
            "loader": {
                "reducers": {
                    "collection_group_results": {
                        "type": "results",
                        "limit": limit,
                    },
                },
                "sort": sort_fields,
                "searchQuery": search_query,
                "userId": self.user_id,
                "userTimeZone": self.user_timezone,
            },
        }

        url = self.BASE_URL + "queryCollection"
        response = requests.post(url, headers=self.headers, params=self.params, json=payload)
        response.raise_for_status()  # Raises an exception for HTTP errors.
        data = response.json()

        # Convert the API response into a MarketingRequestCollection instance.
        marketing_requests = MarketingRequestCollection.from_record_map(data)
        marketing_requests.requests.sort()  # Assuming that MarketingRequest has __lt__ implemented.
        return marketing_requests