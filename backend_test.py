import requests
import json
import datetime
import unittest
import os

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

class TestTCBackendAPI(unittest.TestCase):
    
    def test_api_health(self):
        """Test the API health endpoint"""
        response = requests.get(f"{API_URL}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "T&C Auditor API is running")
        print("✅ API health check passed")
    
    def test_daily_game_valid_date(self):
        """Test getting game data for a valid date"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        response = requests.get(f"{API_URL}/game/{today}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn("date", data)
        self.assertIn("title", data)
        self.assertIn("tc_text", data)
        self.assertIn("real_absurd_clauses", data)
        self.assertIn("fake_absurd_clauses", data)
        self.assertIn("quiz_order", data)
        
        # Check data types
        self.assertIsInstance(data["real_absurd_clauses"], list)
        self.assertIsInstance(data["fake_absurd_clauses"], list)
        self.assertIsInstance(data["quiz_order"], list)
        
        # Check content
        self.assertTrue(len(data["real_absurd_clauses"]) > 0)
        self.assertTrue(len(data["fake_absurd_clauses"]) > 0)
        self.assertTrue(len(data["quiz_order"]) > 0)
        
        print(f"✅ Daily game data for {today} retrieved successfully")
        return data
    
    def test_daily_game_tomorrow(self):
        """Test getting game data for tomorrow (should create fallback)"""
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        response = requests.get(f"{API_URL}/game/{tomorrow}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn("date", data)
        self.assertIn("title", data)
        self.assertIn("tc_text", data)
        self.assertIn("real_absurd_clauses", data)
        self.assertIn("fake_absurd_clauses", data)
        self.assertIn("quiz_order", data)
        
        print(f"✅ Daily game data for {tomorrow} (fallback) retrieved successfully")
    
    def test_daily_game_invalid_date(self):
        """Test getting game data with invalid date format"""
        response = requests.get(f"{API_URL}/game/invalid-date")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        print("✅ Invalid date format handled correctly")
    
    def test_game_result_submission(self):
        """Test submitting game results"""
        # First get a valid game
        today = datetime.date.today().strftime("%Y-%m-%d")
        game_data = self.test_daily_game_valid_date()
        
        # Extract some real clause IDs for submission
        real_clause_ids = [clause["id"] for clause in game_data["real_absurd_clauses"]]
        selected_clauses = real_clause_ids[:3]  # Select first 3 real clauses
        
        # Create submission data
        submission_data = {
            "game_date": today,
            "session_id": "test_session_123",
            "selected_clauses": selected_clauses,
            "completion_time": 45
        }
        
        # Submit results
        response = requests.post(
            f"{API_URL}/game/submit", 
            json=submission_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn("base_score", data)
        self.assertIn("bonus_score", data)
        self.assertIn("total_score", data)
        self.assertIn("max_score", data)
        self.assertIn("correct_answers", data)
        self.assertIn("legal_detector_breakdown", data)
        
        # Verify score calculation
        self.assertEqual(data["base_score"], len(selected_clauses))
        self.assertGreaterEqual(data["total_score"], data["base_score"])
        
        print("✅ Game result submission successful")
        return data
    
    def test_game_stats(self):
        """Test getting game statistics"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        # Submit a result first to ensure we have stats
        self.test_game_result_submission()
        
        # Get stats
        response = requests.get(f"{API_URL}/stats/{today}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check stats structure
        self.assertIn("date", data)
        self.assertIn("total_players", data)
        self.assertIn("clause_stats", data)
        
        # Verify data
        self.assertEqual(data["date"], today)
        self.assertGreaterEqual(data["total_players"], 1)
        
        print(f"✅ Game statistics for {today} retrieved successfully")
    
    def test_submit_nonexistent_game(self):
        """Test submitting results for a non-existent game"""
        invalid_date = "2000-01-01"  # Assuming this game doesn't exist
        
        submission_data = {
            "game_date": invalid_date,
            "session_id": "test_session_456",
            "selected_clauses": ["test1", "test2"],
            "completion_time": 30
        }
        
        # This should create a fallback game and then accept the submission
        response = requests.post(
            f"{API_URL}/game/submit", 
            json=submission_data
        )
        
        # Should still work because the API creates a fallback game
        self.assertEqual(response.status_code, 200)
        print("✅ Submission for non-existent game handled correctly")
    
    def test_malformed_submission(self):
        """Test submitting malformed request body"""
        # Missing required fields
        submission_data = {
            "game_date": datetime.date.today().strftime("%Y-%m-%d"),
            # Missing session_id
            "selected_clauses": ["test1", "test2"],
            # Missing completion_time
        }
        
        response = requests.post(
            f"{API_URL}/game/submit", 
            json=submission_data
        )
        
        self.assertNotEqual(response.status_code, 200)
        print("✅ Malformed submission handled correctly")

if __name__ == "__main__":
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add tests in specific order
    suite.addTest(TestTCBackendAPI('test_api_health'))
    suite.addTest(TestTCBackendAPI('test_daily_game_valid_date'))
    suite.addTest(TestTCBackendAPI('test_daily_game_tomorrow'))
    suite.addTest(TestTCBackendAPI('test_daily_game_invalid_date'))
    suite.addTest(TestTCBackendAPI('test_game_result_submission'))
    suite.addTest(TestTCBackendAPI('test_game_stats'))
    suite.addTest(TestTCBackendAPI('test_submit_nonexistent_game'))
    suite.addTest(TestTCBackendAPI('test_malformed_submission'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)