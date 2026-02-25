from datetime import datetime, timezone, timedelta
import zoneinfo
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_session_factory
from app.domains.task import models, schemas
from app.domains.auth.security import get_current_user
from app.domains.auth.models import User

router = APIRouter()

def get_db():
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()

def get_today_bounds():
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    return start_of_day, end_of_day

@router.get("", response_model=List[schemas.TaskResponse])
def list_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """자신의 활성 할 일 조회 (보관되지 않은 것)"""
    tasks = db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.is_archived == False
    ).order_by(models.Task.due_date.asc()).all()
    return tasks

@router.get("/archive", response_model=List[schemas.TaskResponse])
def list_archived_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """보관함 조회"""
    tasks = db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.is_archived == True
    ).order_by(models.Task.due_date.desc()).all()
    return tasks

@router.get("/past-incomplete", response_model=List[schemas.TaskResponse])
def list_past_incomplete_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """과거 미완료 할 일 조회"""
    start_of_day, _ = get_today_bounds()
    tasks = db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.is_archived == False,
        models.Task.due_date < start_of_day,
        models.Task.status != models.TaskStatus.COMPLETED
    ).order_by(models.Task.due_date.desc()).all()
    return tasks

@router.post("", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # [PRO-B-35] 미래 날짜 차단
    start_of_day, end_of_day = get_today_bounds()
    
    if task_data.due_date.tzinfo is not None:
        local_tz = zoneinfo.ZoneInfo("Asia/Seoul")
        due_date_naive = task_data.due_date.astimezone(local_tz).replace(tzinfo=None)
    else:
        due_date_naive = task_data.due_date
    
    if due_date_naive >= end_of_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a task for a future date."
        )

    # [PRO-B-34] 일일 5개 제한 차단
    c_tasks_today = db.query(func.count(models.Task.id)).filter(
        models.Task.user_id == current_user.id,
        models.Task.due_date >= start_of_day,
        models.Task.due_date < end_of_day
    ).scalar()
    
    if c_tasks_today >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 tasks allowed per day."
        )

    new_task = models.Task(
        title=task_data.title,
        description=task_data.description,
        due_date=due_date_naive,
        user_id=current_user.id,
        status=models.TaskStatus.PENDING
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.patch("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_data: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.is_archived is not None:
        task.is_archived = task_data.is_archived

    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    db.delete(task)
    db.commit()
    return {"message": "Task permanently deleted"}

@router.post("/batch-action")
def batch_action_past_tasks(
    action_data: schemas.TaskBatchAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if action_data.action not in ["archive", "delete"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    tasks = db.query(models.Task).filter(
        models.Task.id.in_(action_data.task_ids),
        models.Task.user_id == current_user.id
    ).all()

    if not tasks:
        return {"message": "No valid tasks found for the operation"}

    if action_data.action == "archive":
        for t in tasks:
            t.is_archived = True
            t.status = models.TaskStatus.PENDING # optional status reset if wanted
        db.commit()
        return {"message": f"Archived {len(tasks)} tasks."}
    else:
        for t in tasks:
            db.delete(t)
        db.commit()
        return {"message": f"Deleted {len(tasks)} tasks."}

@router.get("/stats/today")
def get_productivity_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """[PRO-B-40] 오늘 생산성 달성률 조회"""
    start_of_day, end_of_day = get_today_bounds()
    
    total_today = db.query(func.count(models.Task.id)).filter(
        models.Task.user_id == current_user.id,
        models.Task.due_date >= start_of_day,
        models.Task.due_date < end_of_day
    ).scalar()
    
    completed_today = db.query(func.count(models.Task.id)).filter(
        models.Task.user_id == current_user.id,
        models.Task.due_date >= start_of_day,
        models.Task.due_date < end_of_day,
        models.Task.status == models.TaskStatus.COMPLETED
    ).scalar()
    
    return {
        "total": total_today,
        "completed": completed_today,
        "rate": (completed_today / total_today * 100) if total_today > 0 else 0
    }
