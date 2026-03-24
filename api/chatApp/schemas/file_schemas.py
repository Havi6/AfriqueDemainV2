from pydantic import BaseModel

# schemas

class ImageMeta(BaseModel):
    title: str
    description: str | None