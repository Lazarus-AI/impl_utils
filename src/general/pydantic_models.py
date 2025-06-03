from pydantic import BaseModel


class BoundingBox(BaseModel):
    """A Pydantic model representing a bounding box on a specific page."""

    page_number: int  # 1 Indexed
    box: dict
