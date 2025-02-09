from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from functools import total_ordering

# Dict used to rank the status of a marketing request. Aids with sorting.
STATUS_ORDER = {
    "Not Started": 0,
    "Need Visuals": 1,
    "Drafted": 2,
    "Confirmed": 3,
    "Posted": 4,
}

@dataclass
@total_ordering
class MarketingRequest:
    """
    POPO class to represent a marketing request.
    ==== Public Attributes ====
    id: str UUID of the marketing request.
    title: str User-facing title of the marketing request.
    event: Optional[str] Event associated with the marketing request.
    content_type: Optional[str] Type of content requested.
    status: Optional[str] Status of the marketing request.
    content_summary: Optional[str] Summary of the content requested.
    post_date: Optional[datetime] Date the content is scheduled to be posted.
    final_post: Optional[Any] File property of the final post.
    visuals: Optional[Any] File property of visuals.

    === Representation invariants ===
    - If post_date is not None, it is a datetime object.
    - If status is not None, it is a key in STATUS_ORDER.

    """
    id: str
    title: str
    event: Optional[str] = None
    content_type: Optional[str] = None
    status: Optional[str] = None
    content_summary: Optional[str] = None
    post_date: Optional[datetime] = None
    final_post: Optional[Any] = None
    visuals: Optional[Any] = None

    @classmethod
    def from_notion_page(cls, page: Dict[str, Any]) -> MarketingRequest:
        """
        Create a MarketingRequest from a Notion page dictionary.
        The Notion page's "properties" are mapped as follows:
          - "title":           → title
          - ">zXz":            → event (the related event)
          - "aJ@j":            → content_type
          - "nSLy":            → status
          - "[B|e":           → content_summary
          - "{Rrz":           → post_date (a date string, which we convert to a datetime object)
          - "LQ>I":           → final_post (a file property)
          - "q=zv":           → visuals (a file property)
        """
        properties = page.get("properties", {})

        def get_first(prop_key: str) -> Optional[str]:
            """
            Returns the first value of a property key, if it exists.
            """
            val = properties.get(prop_key)
            if val and isinstance(val, list) and len(val) > 0 and isinstance(val[0], list) and len(val[0]) > 0:
                return val[0][0]
            return None

        title = get_first("title") or ""
        event = get_first(">zXz")
        content_type = get_first("aJ@j")
        status = get_first("nSLy")
        content_summary = get_first("[B|e")

        # For the post date, the Notion property "{Rrz}" is a rollup with a date object.
        post_date = None
        if "{Rrz" in properties:
            try:
                # Example structure:
                # [[ "\u2023", [ ["d", {"type": "date", "start_date": "2025-02-03"}] ] ]]
                date_str = properties["{Rrz"][0][1][0][1].get("start_date")
                if date_str:
                    post_date = datetime.fromisoformat(date_str)
                else:
                    post_date = datetime(2024, 9, 1)
            except Exception as e:
                # In case of an unexpected structure or format, we leave post_date as None.
                # Set teh post date to september 1st 2024
                print(e)
                post_date = datetime(2024, 9, 1)
        else:
            post_date = datetime(2024, 9, 1)
                

        return cls(
            id=page.get("id"),
            title=title,
            event=event,
            content_type=content_type,
            status=status,
            content_summary=content_summary,
            post_date=post_date,
        )

    def __repr__(self):
        return f"<MarketingRequest id={self.id} title={self.title!r} content_type={self.content_type!r} status={self.status!r} post_date={self.post_date}>"

    def _sort_key(self):
        """
        Build the sort key as a tuple:
          1. The first element is the numeric rank for the status.
             If the status is not found in STATUS_ORDER, it defaults to infinity.
          2. The second element is based on the post_date.
             For descending order by date (i.e., newer dates first), we use the negative
             of the timestamp. If post_date is None, we use float('inf') so that it sorts last.
        """
        status_rank = STATUS_ORDER.get(self.status, float('inf'))
        date_key = self.post_date if self.post_date is not None else datetime(2024, 9, 1)

        return (status_rank, date_key)

    def __eq__(self, other):
        if not isinstance(other, MarketingRequest):
            return NotImplemented
        return self._sort_key() == other._sort_key()

    def __lt__(self, other):
        if not isinstance(other, MarketingRequest):
            return NotImplemented
        return self._sort_key() < other._sort_key()


class MarketingRequestCollection:
    """
    ADT to represent a collection of MarketingRequest objects. Allows for sorting and filtering by status and content type.
    """
    def __init__(self, requests: List[MarketingRequest]):
        self.requests = requests

    @classmethod
    def from_record_map(cls, record_map: Dict[str, Any]) -> MarketingRequestCollection:
        """
        Given the full Notion record map JSON (as a dict) and the marketing collection ID,
        filter out the page blocks whose parent_table is "collection" and whose parent_id
        matches the provided collection_id. Each such block is interpreted as a marketing request.
        """
        blocks = record_map.get("recordMap", {}).get("block", {})
        requests = []
        for block_data in blocks.values():
            value = block_data.get("value", {})
            req = MarketingRequest.from_notion_page(value)
            requests.append(req)
        requests.sort()
        return cls(requests)

    def _fetch(self, val: str, key: callable):
        """
        Method to be wrapped by fetch_requests_by_status and fetch_requests_by_type.
        """
        return [req for req in self.requests if key(req) == val]

    def fetch_requests_by_status(self, status: str) -> List[MarketingRequest]:
        """
        Return a list of MarketingRequest objects that match the given status.
        """
        return self._fetch(status, lambda req: req.status)
        

    def fetch_requests_by_type(self, content_type: str) -> List[MarketingRequest]:
        """
        Return a list of MarketingRequest objects that match the given content type.
        """
        return self._fetch(content_type, lambda req: req.content_type)

    def __iter__(self):
        return iter(self.requests)

    def __len__(self):
        return len(self.requests)

    def __getitem__(self, index):
        return self.requests[index]

    def __repr__(self):
        return f"<MarketingRequestCollection with {len(self.requests)} requests>"
    
    # define sort magic method



# Example usage:
if __name__ == "__main__":
    # Assume your exported Notion JSON is stored in 'marketing_requests.json'
    with open("response.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    marketing_requests = MarketingRequestCollection.from_record_map(data)

    marketing_requests.requests.sort()
    for req in marketing_requests:
        print(req)
