from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class AbsurdClause(BaseModel):
    id: str
    text: str

class GameData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    title: str
    tc_text: str
    real_absurd_clauses: List[AbsurdClause]
    fake_absurd_clauses: List[AbsurdClause]
    quiz_order: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GameDataCreate(BaseModel):
    date: str
    title: str
    tc_text: str
    real_absurd_clauses: List[AbsurdClause]
    fake_absurd_clauses: List[AbsurdClause]
    quiz_order: List[str]

class UserAnswer(BaseModel):
    clause_id: str
    was_selected: bool
    is_real: bool
    correct: bool

class GameResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_date: str
    user_id: Optional[str] = None
    session_id: str
    selected_clauses: List[str]
    score: Dict[str, float]  # {"base": 3, "bonus": 0.6, "total": 3.6}
    user_answers: List[UserAnswer]
    completion_time: int  # seconds taken to complete quiz
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

class GameResultCreate(BaseModel):
    game_date: str
    session_id: str
    selected_clauses: List[str]
    completion_time: int

class GameStats(BaseModel):
    date: str
    total_players: int
    clause_stats: Dict[str, Dict[str, Any]]  # clause_id -> {found_count, total_players, percentage}
    average_score: float
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class DailyGameResponse(BaseModel):
    date: str
    title: str
    tc_text: str
    real_absurd_clauses: List[AbsurdClause]
    fake_absurd_clauses: List[AbsurdClause]
    quiz_order: List[str]

class ScoreResponse(BaseModel):
    base_score: int
    bonus_score: float
    total_score: float
    max_score: int
    correct_answers: List[str]
    legal_detector_breakdown: Dict[str, Any]