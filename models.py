from database import Base
from sqlalchemy import Column, Integer, String


class Node(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    left = Column(Integer, nullable=False)
    right = Column(Integer, nullable=False)
    tree_id = Column(String, nullable=False)