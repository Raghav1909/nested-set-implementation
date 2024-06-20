from pydantic import BaseModel

class NodeBase(BaseModel):
    name: str
    left: int
    right: int


class NodeCreate(NodeBase):
    parent_id: int


class NodeOut(BaseModel):
    id: int
    name: str


class NodeUpdate(BaseModel):
    id: int
    name: str