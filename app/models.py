from app.database import Base
from sqlalchemy import Column, Integer, String


class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    left = Column(Integer, nullable=False)
    right = Column(Integer, nullable=False)