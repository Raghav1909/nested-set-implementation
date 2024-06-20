from pydantic import BaseModel
from typing import List

class NodeBase(BaseModel):
    name: str
    left: int
    right: int


class NodeCreate(BaseModel):
    parent_id: int
    name: str


class NodeOut(NodeBase):
    id: int


class NodeUpdate(BaseModel):
    id: int
    name: str


class TreeView(BaseModel):
    id: int
    name: str
    left: int
    right: int
    children: List['TreeView']