from fastapi import APIRouter

router = APIRouter(tags=["Nodes"], prefix="/api")


@router.get("/")
def build_graph():
    return ""

@router.post("/add-node")
def add_node(name: str, left: int, right: int, tree_id: str):
    return ""