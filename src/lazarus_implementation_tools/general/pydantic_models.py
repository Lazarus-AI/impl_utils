from typing import Any, Optional

from pydantic import BaseModel


class BoundingBox(BaseModel):
    """A Pydantic model representing a bounding box on a specific page."""

    page_number: int  # 1 Indexed
    unit: Optional[str]
    box: dict
    # Example:
    # box_dict = {
    #     "top_left_x": 10,
    #     "top_left_y": 10,
    #     "bottom_right_x": 110,
    #     "bottom_right_y": 110,
    # }


class Polygon(BaseModel):
    """A Pydantic model representing a polygon on a specific page."""

    page_number: int
    unit: Optional[str]
    vertices: list[tuple]


class TextBox(BaseModel):
    """A Pydantic model representing the placement of text."""

    page_number: int
    unit: Optional[str]
    coordinates: tuple[float, float]
    text: str
    font: Optional[Any]  # Optional[ImageFont]
