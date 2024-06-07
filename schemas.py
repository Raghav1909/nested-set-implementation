from pydantic import BaseModel


class NodeBase(BaseModel):
    name: str
    left: int
    right: int
    tree_id: str