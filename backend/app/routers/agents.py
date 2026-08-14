from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Agent, Category
from app.schemas import AgentResponse, CategoryResponse

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/agents", response_model=List[AgentResponse])
def list_agents(db: Session = Depends(get_db)):
    return db.query(Agent).order_by(Agent.name).all()


@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()
