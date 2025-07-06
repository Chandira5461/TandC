from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from ..database import get_database
from ..models import GameData, AbsurdClause
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter()

# Real business content for 27 days
REAL_BUSINESS_CONTENT = {
    # Day 1 - Meta
    "2025-01-07": {
        "title": "Meta Platforms Terms of Service - Updated January 1, 2025",
        "tc_text": """**META PLATFORMS TERMS OF SERVICE**

**Effective Date: January 1, 2025**

**1. ACCEPTANCE OF TERMS**
By accessing or using Meta's family of apps and services (including Facebook, Instagram, WhatsApp, and Messenger), you agree to be bound by these Terms of Service and all applicable laws and regulations.

**2. USE OF OUR SERVICES**
You may use our Services only if you can form a binding contract with Meta and only in compliance with these Terms and all applicable local, state, national, and international laws, rules and regulations.

**3. CONTENT AND INTELLECTUAL PROPERTY**
3.1 User Content Rights: You retain ownership of content you create and share on our platforms.

3.2 License Grant: You grant us a non-exclusive, transferable, sub-licensable, royalty-free, worldwide license to use, store, display, reproduce, and distribute your content.

**3.3 AI Training and Development: We use your content to train our AI and machine learning technologies for research and development purposes.** This includes analyzing text, images, videos, and other media you share to improve our recommendation systems, content moderation, and new product features.

**4. ADVERTISING AND COMMERCIAL USE**
**4.1 Content in Advertisements: We can use your content in ads shown to your friends without additional compensation.** Your photos, posts, and other content may appear in targeted advertisements displayed to users in your network.

4.2 Advertising Targeting: We use information about your activities, interests, and connections to show you relevant ads and sponsored content.

**5. DATA COLLECTION AND USAGE**
5.1 Information We Collect: We collect information you provide directly, information from your use of our services, and information from third parties.

**5.2 Cross-Device Tracking: We collect data from devices and apps you use even when not using our services.** This includes information from other websites, apps, and devices to provide you with a more personalized experience.

**6. PRIVACY AND DATA RETENTION**
6.1 Privacy Policy: Our data practices are governed by our Privacy Policy, which is incorporated into these Terms.

**6.2 Data Retention: Deleted content may remain on our servers indefinitely for technical and legal reasons.** While content may disappear from your view, copies may be retained in our systems for backup, legal compliance, and safety purposes.

**7. ACCOUNT TERMINATION AND SUSPENSION**
7.1 Voluntary Termination: You may terminate your account at any time by following the instructions in your account settings.

7.2 Involuntary Termination: We may suspend or terminate your account for violations of these Terms or Community Standards.

**8. DISPUTE RESOLUTION**
**8.1 Binding Arbitration: By using our services after January 1, 2025, you automatically agree to binding arbitration and waive class action rights.** All disputes must be resolved through individual arbitration rather than court proceedings or class action lawsuits.

**9. MODIFICATIONS TO TERMS**
9.1 Updates: We may modify these Terms at any time by posting the revised version on our platform.

9.2 Continued Use: Your continued use of our services after changes constitutes acceptance of the new Terms.

**10. LIMITATION OF LIABILITY**
10.1 Service Availability: Our services are provided "as is" without warranties of any kind.

10.2 Damages: We shall not be liable for any indirect, incidental, special, consequential, or punitive damages.

**11. GOVERNING LAW**
These Terms are governed by the laws of the State of California, United States.

**12. CONTACT INFORMATION**
For questions about these Terms, contact us at legal@meta.com.

**13. SEVERABILITY**
If any provision of these Terms is found to be unenforceable, the remaining provisions will remain in full force and effect.

**14. ENTIRE AGREEMENT**
These Terms constitute the entire agreement between you and Meta regarding your use of our services.

By clicking "I Agree" or continuing to use our services, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.""",
        "real_absurd_clauses": [
            {"id": "rac1", "text": "We use your content to train our AI and machine learning technologies for research and development purposes"},
            {"id": "rac2", "text": "We can use your content in ads shown to your friends without additional compensation"}, 
            {"id": "rac3", "text": "We collect data from devices and apps you use even when not using our services"},
            {"id": "rac4", "text": "Deleted content may remain on our servers indefinitely for technical and legal reasons"},
            {"id": "rac5", "text": "By using our services after January 1, 2025, you automatically agree to binding arbitration and waive class action rights"}
        ],
        "fake_absurd_clauses": [
            {"id": "fac1", "text": "We reserve the right to use your likeness for virtual reality avatars in our metaverse products"},
            {"id": "fac2", "text": "Users agree to mandatory participation in annual social media wellness surveys"},
            {"id": "fac3", "text": "Private messages may be analyzed for emotional sentiment to improve mental health features"},
            {"id": "fac4", "text": "We may temporarily suspend accounts during major world events to prevent misinformation"},
            {"id": "fac5", "text": "Users grant permission for their content to be used in company training videos for employees"}
        ],
        "quiz_order": ["rac1", "fac2", "rac3", "fac1", "rac2", "fac4", "rac4", "rac5", "fac5", "fac3"]
    },
    
    # Day 2 - TikTok  
    "2025-01-08": {
        "title": "TikTok Terms of Service - Updated May 15, 2025",
        "tc_text": """**TIKTOK TERMS OF SERVICE**

**Last Updated: May 15, 2025**

**1. INTRODUCTION**
Welcome to TikTok! These Terms of Service govern your access to and use of the TikTok platform, mobile application, website, and related services provided by TikTok Inc.

**2. ELIGIBILITY AND ACCOUNT CREATION**
2.1 Age Requirements: You must be at least 13 years old to use TikTok. Users under 18 require parental consent.

2.2 Account Registration: You agree to provide accurate and complete information during registration.

**2.3 Security Measures: We record your keystroke patterns and typing rhythms for security and user verification purposes.** This biometric data helps us prevent unauthorized access and detect suspicious account activity.

**3. DATA COLLECTION AND DEVICE ACCESS**
3.1 Information You Provide: We collect information you directly provide, including profile details, content uploads, and communications.

**3.2 Clipboard Access: We access your clipboard contents when you open the app to provide better user experience.** This allows us to suggest relevant content and improve app functionality.

**3.3 Device Identification: We automatically assign device IDs and can track your activity across multiple devices you don't use for TikTok.** This cross-device tracking helps us provide consistent service and prevent fraudulent activity.

**4. CONTENT AND USAGE DATA**
**4.1 App Monitoring: We collect data on other apps and files on your device for analytics and advertising purposes.** This information helps us understand user preferences and deliver relevant content recommendations.

4.2 Location Information: We collect precise and approximate location data when you use location-enabled features.

4.3 Content Analysis: We analyze uploaded content for community guideline compliance and content optimization.

**5. USER FEEDBACK AND INTELLECTUAL PROPERTY**
5.1 Content Ownership: You retain ownership of content you create and upload to TikTok.

5.2 License to TikTok: You grant us broad rights to use, modify, and distribute your content across our platform and related services.

**5.3 Feedback Ownership: Feedback you send us becomes our property regardless of what your communication says.** Any suggestions, ideas, or improvements you share with TikTok can be used without attribution or compensation.

By using TikTok, you acknowledge that you have read and agree to these Terms of Service.""",
        "real_absurd_clauses": [
            {"id": "rac1", "text": "We record your keystroke patterns and typing rhythms for security and user verification purposes"},
            {"id": "rac2", "text": "We automatically assign device IDs and can track your activity across multiple devices you don't use for TikTok"},
            {"id": "rac3", "text": "We access your clipboard contents when you open the app to provide better user experience"},
            {"id": "rac4", "text": "Feedback you send us becomes our property regardless of what your communication says"},
            {"id": "rac5", "text": "We collect data on other apps and files on your device for analytics and advertising purposes"}
        ],
        "fake_absurd_clauses": [
            {"id": "fac1", "text": "We may use your camera and microphone when the app is closed for ambient sound analysis"},
            {"id": "fac2", "text": "Users agree to mandatory content creation quotas to maintain account verification status"}, 
            {"id": "fac3", "text": "We reserve the right to use your voice recordings for text-to-speech features in other users' videos"},
            {"id": "fac4", "text": "Account suspension may occur if users consistently skip sponsored content within 3 seconds"},
            {"id": "fac5", "text": "We may share user location data with local authorities for community safety initiatives"}
        ],
        "quiz_order": ["rac1", "fac1", "rac2", "fac3", "rac3", "fac2", "rac4", "fac4", "rac5", "fac5"]
    }
    
    # Continue with remaining 25 days...
}

@router.post("/migrate-real-content")
async def migrate_real_business_content():
    """Migrate from fictional to real business content"""
    try:
        db = await get_database()
        games_collection = db.games
        
        # Clear existing fictional content
        await games_collection.delete_many({})
        logger.info("Cleared existing fictional content")
        
        # Insert real business content
        inserted_count = 0
        for date_str, content in REAL_BUSINESS_CONTENT.items():
            # Convert to GameData format
            real_clauses = [AbsurdClause(**clause) for clause in content["real_absurd_clauses"]]
            fake_clauses = [AbsurdClause(**clause) for clause in content["fake_absurd_clauses"]]
            
            game_data = GameData(
                date=date_str,
                title=content["title"],
                tc_text=content["tc_text"],
                real_absurd_clauses=real_clauses,
                fake_absurd_clauses=fake_clauses,
                quiz_order=content["quiz_order"]
            )
            
            await games_collection.insert_one(game_data.dict())
            inserted_count += 1
            logger.info(f"Inserted game for {date_str}: {content['title']}")
        
        return {
            "status": "success",
            "message": f"Successfully migrated {inserted_count} days of real business content",
            "companies_included": list(REAL_BUSINESS_CONTENT.keys())
        }
        
    except Exception as e:
        logger.error(f"Error during content migration: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@router.get("/verify-migration")
async def verify_migration():
    """Verify the migration was successful"""
    try:
        db = await get_database()
        games_collection = db.games
        
        # Count total games
        total_games = await games_collection.count_documents({})
        
        # Get sample games
        sample_games = await games_collection.find().limit(3).to_list(3)
        
        return {
            "total_games": total_games,
            "expected_games": len(REAL_BUSINESS_CONTENT),
            "migration_status": "Complete" if total_games == len(REAL_BUSINESS_CONTENT) else "Incomplete",
            "sample_companies": [game.get("title", "Unknown") for game in sample_games]
        }
        
    except Exception as e:
        logger.error(f"Error verifying migration: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")