from pydantic import BaseModel


class BoundingBox(BaseModel):
    page_number: int  # 1 Indexed
    box: dict
