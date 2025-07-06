from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, date
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from ..models import (
    GameData, GameDataCreate, GameResult, GameResultCreate, 
    GameStats, DailyGameResponse, ScoreResponse, UserAnswer
)
from ..database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_games_collection() -> AsyncIOMotorCollection:
    db = await get_database()
    return db.games

async def get_results_collection() -> AsyncIOMotorCollection:
    db = await get_database()
    return db.game_results

async def get_stats_collection() -> AsyncIOMotorCollection:
    db = await get_database()
    return db.game_stats

@router.get("/game/{game_date}", response_model=DailyGameResponse)
async def get_daily_game(
    game_date: str,
    games_collection: AsyncIOMotorCollection = Depends(get_games_collection)
):
    """Get daily game content for a specific date"""
    try:
        # Validate date format
        datetime.strptime(game_date, "%Y-%m-%d")
        
        game_data = await games_collection.find_one({"date": game_date})
        
        if not game_data:
            # If no game data exists for this date, create default/fallback game
            fallback_game = await create_fallback_game(game_date, games_collection)
            return DailyGameResponse(**fallback_game)
        
        return DailyGameResponse(**game_data)
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error fetching daily game: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch daily game")

@router.post("/game", response_model=GameData)
async def create_game(
    game_create: GameDataCreate,
    games_collection: AsyncIOMotorCollection = Depends(get_games_collection)
):
    """Create a new daily game (admin endpoint)"""
    try:
        # Check if game already exists for this date
        existing_game = await games_collection.find_one({"date": game_create.date})
        if existing_game:
            raise HTTPException(status_code=400, detail="Game already exists for this date")
        
        game_data = GameData(**game_create.dict())
        await games_collection.insert_one(game_data.dict())
        
        return game_data
    
    except Exception as e:
        logger.error(f"Error creating game: {e}")
        raise HTTPException(status_code=500, detail="Failed to create game")

@router.post("/game/submit", response_model=ScoreResponse)
async def submit_game_result(
    result_create: GameResultCreate,
    games_collection: AsyncIOMotorCollection = Depends(get_games_collection),
    results_collection: AsyncIOMotorCollection = Depends(get_results_collection),
    stats_collection: AsyncIOMotorCollection = Depends(get_stats_collection)
):
    """Submit game results and calculate score"""
    try:
        # Get the game data for scoring
        game_data = await games_collection.find_one({"date": result_create.game_date})
        if not game_data:
            raise HTTPException(status_code=404, detail="Game not found for this date")
        
        # Calculate score
        real_clause_ids = [clause["id"] for clause in game_data["real_absurd_clauses"]]
        selected_clauses = result_create.selected_clauses
        
        # Base score calculation
        correct_answers = [clause_id for clause_id in selected_clauses if clause_id in real_clause_ids]
        base_score = len(correct_answers)
        
        # Get current stats for Legal Detector bonus
        current_stats = await get_or_create_stats(result_create.game_date, stats_collection)
        
        # Calculate bonus score based on rarity
        bonus_score = 0.0
        legal_detector_breakdown = {}
        
        for clause_id in correct_answers:
            if clause_id in current_stats.get("clause_stats", {}):
                clause_stat = current_stats["clause_stats"][clause_id]
                percentage = clause_stat.get("percentage", 0)
                
                if percentage < 30:  # Rarely found
                    bonus = 0.5
                elif percentage < 70:  # Moderately found
                    bonus = 0.3
                else:  # Commonly found
                    bonus = 0.1
                
                bonus_score += bonus
                legal_detector_breakdown[clause_id] = {
                    "percentage": percentage,
                    "bonus": bonus,
                    "rarity": "rare" if percentage < 30 else "moderate" if percentage < 70 else "common"
                }
            else:
                # First time this clause is found
                bonus_score += 0.5
                legal_detector_breakdown[clause_id] = {
                    "percentage": 0,
                    "bonus": 0.5,
                    "rarity": "rare"
                }
        
        total_score = base_score + bonus_score
        
        # Create user answers for storage
        all_clauses = game_data["real_absurd_clauses"] + game_data["fake_absurd_clauses"]
        user_answers = []
        
        for clause_id in game_data["quiz_order"]:
            clause = next((c for c in all_clauses if c["id"] == clause_id), None)
            if clause:
                is_real = clause_id in real_clause_ids
                was_selected = clause_id in selected_clauses
                correct = (is_real and was_selected) or (not is_real and not was_selected)
                
                user_answers.append(UserAnswer(
                    clause_id=clause_id,
                    was_selected=was_selected,
                    is_real=is_real,
                    correct=correct
                ))
        
        # Create game result
        game_result = GameResult(
            game_date=result_create.game_date,
            session_id=result_create.session_id,
            selected_clauses=selected_clauses,
            score={"base": base_score, "bonus": bonus_score, "total": total_score},
            user_answers=user_answers,
            completion_time=result_create.completion_time
        )
        
        # Save result to database
        await results_collection.insert_one(game_result.dict())
        
        # Update statistics
        await update_game_stats(result_create.game_date, selected_clauses, real_clause_ids, stats_collection)
        
        return ScoreResponse(
            base_score=base_score,
            bonus_score=bonus_score,
            total_score=total_score,
            max_score=5,
            correct_answers=correct_answers,
            legal_detector_breakdown=legal_detector_breakdown
        )
    
    except Exception as e:
        logger.error(f"Error submitting game result: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit game result")

@router.get("/stats/{game_date}")
async def get_game_stats(
    game_date: str,
    stats_collection: AsyncIOMotorCollection = Depends(get_stats_collection)
):
    """Get game statistics for a specific date"""
    try:
        stats = await stats_collection.find_one({"date": game_date})
        if not stats:
            return {"date": game_date, "total_players": 0, "clause_stats": {}, "average_score": 0.0}
        
        # Remove MongoDB ObjectId to avoid serialization issues
        if "_id" in stats:
            del stats["_id"]
        
        return stats
    
    except Exception as e:
        logger.error(f"Error fetching game stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch game stats")

async def create_fallback_game(game_date: str, games_collection: AsyncIOMotorCollection) -> dict:
    """Create a fallback game if no game exists for the date"""
    fallback_game_data = {
        "date": game_date,
        "title": "Terms of Service for Interdimensional Pet Adoption Co.",
        "tc_text": """TERMS OF SERVICE - INTERDIMENSIONAL PET ADOPTION CO.

1. ACCEPTANCE OF TERMS
By accessing or using the services provided by Interdimensional Pet Adoption Co. ("Company"), you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our services.

2. SERVICE DESCRIPTION
The Company provides pet adoption services across multiple dimensions and realities. We facilitate the matching of sentient beings with compatible animal companions from various planes of existence.

3. USER OBLIGATIONS
Users must provide accurate information about their dimensional coordinates and temporal stability ratings. By proceeding, user agrees to an annual mandatory glitter tax, payable in actual glitter, which will be collected by our interdimensional revenue agents during the third lunar eclipse of each fiscal year.

4. PAYMENT TERMS
All fees are due upon completion of adoption procedures. Payment may be made in standard currency, rare minerals, or emotional energy equivalents as determined by our quantum accounting department.

5. PRIVACY POLICY
We respect your privacy and will not share your personal information with third parties, except as required by interdimensional law. The company reserves the right to re-theme your emotional support animal as a corporate mascot without prior notice, including but not limited to costume changes, promotional appearances, and social media campaigns.

6. LIMITATION OF LIABILITY
The Company shall not be liable for any damages arising from temporal paradoxes, dimensional rifts, or reality dissolution caused by improper pet care across multiple timelines.

7. GOVERNING LAW
These terms are governed by the laws of the Primary Dimension and the Intergalactic Pet Welfare Code. Users consent to the jurisdiction of the Cosmic Court of Pet Affairs for any disputes arising from these terms.

8. MODIFICATIONS
The Company reserves the right to modify these terms at any time without notice. All pets adopted through our service are subject to our mandatory cuddle quotas as outlined in Schedule A, which requires a minimum of 47 hugs per day per pet, monitored by our emotion-sensing surveillance drones.

9. TERMINATION
Either party may terminate this agreement with 30 days notice, unless termination occurs during a mercury retrograde period, in which case 90 days notice is required.

10. ENTIRE AGREEMENT
This document constitutes the entire agreement between the parties and supersedes all prior negotiations, representations, or agreements relating to the subject matter herein.""",
        "real_absurd_clauses": [
            {"id": "rac1", "text": "By proceeding, user agrees to an annual mandatory glitter tax, payable in actual glitter, which will be collected by our interdimensional revenue agents during the third lunar eclipse of each fiscal year."},
            {"id": "rac2", "text": "The company reserves the right to re-theme your emotional support animal as a corporate mascot without prior notice, including but not limited to costume changes, promotional appearances, and social media campaigns."},
            {"id": "rac3", "text": "All pets adopted through our service are subject to our mandatory cuddle quotas as outlined in Schedule A, which requires a minimum of 47 hugs per day per pet, monitored by our emotion-sensing surveillance drones."},
            {"id": "rac4", "text": "Either party may terminate this agreement with 30 days notice, unless termination occurs during a mercury retrograde period, in which case 90 days notice is required."},
            {"id": "rac5", "text": "Users must provide accurate information about their dimensional coordinates and temporal stability ratings."}
        ],
        "fake_absurd_clauses": [
            {"id": "fac1", "text": "Participation in this service implies consent to occasional unsolicited serenades by our customer support team, performed in interpretive dance format during business hours."},
            {"id": "fac2", "text": "Users are prohibited from discussing the color purple on Tuesdays within a 50-mile radius of any Company facility, as this may disturb our psychic pets."},
            {"id": "fac3", "text": "All adopted pets must be taught to respond to their names backwards, and owners must address them only in whispers during the full moon."},
            {"id": "fac4", "text": "The Company reserves the right to replace any adopted pet with a holographic duplicate if the original pet achieves sentience beyond Level 7 consciousness."},
            {"id": "fac5", "text": "Users agree to submit monthly reports detailing their pet's dreams, transcribed in iambic pentameter and submitted via carrier pigeon only."}
        ],
        "quiz_order": ["rac1", "fac2", "rac3", "fac1", "rac2", "fac4", "rac4", "rac5", "fac5", "fac3"]
    }
    
    # Save fallback game to database
    game_data = GameData(**fallback_game_data)
    await games_collection.insert_one(game_data.dict())
    
    return fallback_game_data

async def get_or_create_stats(game_date: str, stats_collection: AsyncIOMotorCollection) -> dict:
    """Get existing stats or create new stats entry for a date"""
    stats = await stats_collection.find_one({"date": game_date})
    if not stats:
        stats = {
            "date": game_date,
            "total_players": 0,
            "clause_stats": {},
            "average_score": 0.0
        }
    return stats

async def update_game_stats(game_date: str, selected_clauses: List[str], real_clause_ids: List[str], stats_collection: AsyncIOMotorCollection):
    """Update game statistics after a player submits results"""
    try:
        stats = await get_or_create_stats(game_date, stats_collection)
        
        # Increment total players
        stats["total_players"] += 1
        
        # Update clause statistics
        if "clause_stats" not in stats:
            stats["clause_stats"] = {}
        
        # Update stats for all real clauses
        for clause_id in real_clause_ids:
            if clause_id not in stats["clause_stats"]:
                stats["clause_stats"][clause_id] = {
                    "found_count": 0,
                    "total_players": 0,
                    "percentage": 0.0
                }
            
            stats["clause_stats"][clause_id]["total_players"] = stats["total_players"]
            
            if clause_id in selected_clauses:
                stats["clause_stats"][clause_id]["found_count"] += 1
            
            # Calculate percentage
            found_count = stats["clause_stats"][clause_id]["found_count"]
            total_players = stats["total_players"]
            stats["clause_stats"][clause_id]["percentage"] = (found_count / total_players) * 100 if total_players > 0 else 0
        
        # Update or insert stats
        await stats_collection.replace_one(
            {"date": game_date},
            stats,
            upsert=True
        )
        
    except Exception as e:
        logger.error(f"Error updating game stats: {e}")
        raise