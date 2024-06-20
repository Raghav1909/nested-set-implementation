from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from . import models, schemas
from .database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["Nodes"], prefix="/api/nodes")

@router.get("/", response_model=schemas.TreeView)
def build_tree_view(db: Session = Depends(get_db)):
    root = db.query(models.Node).filter( models.Node.left == 1).first()
    
    if not root:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Root node not found")
    
    def build_tree(node: models.Node):
        children = db.query(models.Node).filter(
            models.Node.left > node.left,
            models.Node.right < node.right
        ).all()
        children_nodes = []
        i = node.left + 1
        while i < node.right:
            child = next((child for child in children if child.left == i), None)
            if child:
                children_nodes.append(build_tree(child))
                i = child.right + 1
            else:
                i += 1
        return {
            "id": node.id,
            "name": node.name,
            "left": node.left,
            "right": node.right,
            "children": children_nodes
        }
    
    tree = build_tree(root)
    
    return tree


@router.post("/")
def add_node(node: schemas.NodeCreate, db: Session = Depends(get_db)):
    if node.parent_id == 0:
        if db.query(models.Node).count() == 0:
            root = models.Node(   
                left=1,
                right=2,
                name=node.name,
            )
            db.add(root)
            db.commit()
            return JSONResponse(status_code=status.HTTP_201_CREATED, content={"id": root.id})
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Root node already exists")
    
    if node.parent_id not in [node.id  for node in db.query(models.Node).all()]:
        # Parent node does not exist, throw error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent node does not exist")
    
    parent_node = db.query(models.Node).filter(models.Node.id == node.parent_id).first()
    
    db.query(models.Node).filter(models.Node.right > parent_node.left).update({models.Node.right: models.Node.right + 2}, synchronize_session=False)
    
    db.query(models.Node).filter(models.Node.left > parent_node.left).update({models.Node.left: models.Node.left + 2}, synchronize_session=False)

    new_node = models.Node(
        name=node.name,
        left=parent_node.left + 1,
        right=parent_node.left + 2,
    )
    
    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"id": new_node.id})


@router.put("/{node_id}", status_code=status.HTTP_200_OK)
def update_node(node_id: int, node: schemas.NodeUpdate, db: Session = Depends(get_db)):
    node_to_update = db.query(models.Node).filter(models.Node.id == node_id).first()
    
    if not node_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    
    node_to_update.name = node.name
    db.commit()
    
    return JSONResponse(status_code=status.HTTP_200, content={"message": "Node updated successfully"})


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subtree(node_id: int, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    
    width = node.right - node.left + 1
    
    db.query(models.Node).filter(models.Node.left >= node.left, models.Node.right <= node.right).delete()
    db.commit()
    
    db.query(models.Node).filter(models.Node.right > node.right).update({models.Node.right: models.Node.right - width}, synchronize_session=False)
    db.query(models.Node).filter(models.Node.left > node.right).update({models.Node.left: models.Node.left - width}, synchronize_session=False)
    db.commit()


@router.delete("/{node_id}/delete-elevate", status_code=status.HTTP_204_NO_CONTENT)
def delete_node_and_elevate_decendants(node_id: int, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    
    db.query(models.Node).filter(models.Node.left == node.left).delete()
    db.commit()
    
    db.query(models.Node).filter(models.Node.left > node.left, models.Node.left < node.right).update({models.Node.left: models.Node.left - 1, models.Node.right: models.Node.right - 1}, synchronize_session=False)
    db.query(models.Node).filter(models.Node.right > node.right).update({models.Node.right: models.Node.right - 2}, synchronize_session=False)
    db.query(models.Node).filter(models.Node.left > node.right).update({models.Node.left: models.Node.left - 2}, synchronize_session=False)
    db.commit()


@router.put("/move/{node_id}", status_code=status.HTTP_200_OK)
def move_subtree(node_id: int, new_parent_id: int, db: Session = Depends(get_db)):
    # Fetch the origin node
    origin_node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not origin_node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    
    # Fetch the new parent node
    new_parent_node = db.query(models.Node).filter(models.Node.id == new_parent_id).first()
    if not new_parent_node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New parent node not found")
    
    # Check if we are trying to move the node under itself
    if new_parent_node.left >= origin_node.left and new_parent_node.right <= origin_node.right:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot move subtree under itself")
    
    origin_lft = origin_node.left
    origin_rgt = origin_node.right
    new_parent_rgt = new_parent_node.right
    subtree_width = origin_rgt - origin_lft + 1

    if new_parent_rgt < origin_lft:
        db.query(models.Node).filter(models.Node.left >= new_parent_rgt, models.Node.left < origin_lft).update({
            models.Node.left: models.Node.left + subtree_width
        }, synchronize_session=False)
        
        db.query(models.Node).filter(models.Node.right >= new_parent_rgt, models.Node.right < origin_lft).update({
            models.Node.right: models.Node.right + subtree_width
        }, synchronize_session=False)
        
        db.query(models.Node).filter(models.Node.left >= origin_lft, models.Node.left <= origin_rgt).update({
            models.Node.left: models.Node.left + (new_parent_rgt - origin_lft)
        }, synchronize_session=False)
        
        db.query(models.Node).filter(models.Node.right >= origin_lft, models.Node.right <= origin_rgt).update({
            models.Node.right: models.Node.right + (new_parent_rgt - origin_lft)
        }, synchronize_session=False)
        
    elif new_parent_rgt > origin_rgt:
        db.query(models.Node).filter(models.Node.left > origin_rgt, models.Node.left < new_parent_rgt).update({
            models.Node.left: models.Node.left - subtree_width
        }, synchronize_session=False)
        
        db.query(models.Node).filter(models.Node.right > origin_rgt, models.Node.right < new_parent_rgt).update({
            models.Node.right: models.Node.right - subtree_width
        }, synchronize_session=False)
        
        db.query(models.Node).filter(models.Node.left >= origin_lft, models.Node.left <= origin_rgt).update({
            models.Node.left: models.Node.left + (new_parent_rgt - origin_rgt - 1)
        }, synchronize_session=False)
        
        db.query(models.Node).filter(models.Node.right >= origin_lft, models.Node.right <= origin_rgt).update({
            models.Node.right: models.Node.right + (new_parent_rgt - origin_rgt - 1)
        }, synchronize_session=False)
    
    db.commit()

    return {"message": "Subtree moved successfully"}