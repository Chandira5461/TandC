import requests
import json
import datetime
import unittest
import os
import pprint

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
    
    def test_specific_company_games(self):
        """Test getting game data for specific company dates"""
        # Test Meta (2025-07-07)
        meta_date = "2025-07-07"
        response = requests.get(f"{API_URL}/game/{meta_date}")
        self.assertEqual(response.status_code, 200)
        meta_data = response.json()
        
        # Check Meta data
        self.assertEqual(meta_data["date"], meta_date)
        self.assertIn("Meta", meta_data["title"])
        self.assertTrue(len(meta_data["real_absurd_clauses"]) == 5, 
                       f"Expected 5 real clauses for Meta, got {len(meta_data['real_absurd_clauses'])}")
        self.assertTrue(len(meta_data["fake_absurd_clauses"]) == 5,
                       f"Expected 5 fake clauses for Meta, got {len(meta_data['fake_absurd_clauses'])}")
        
        print(f"✅ Meta game data for {meta_date} retrieved successfully")
        
        # Test TikTok (2025-07-08)
        tiktok_date = "2025-07-08"
        response = requests.get(f"{API_URL}/game/{tiktok_date}")
        self.assertEqual(response.status_code, 200)
        tiktok_data = response.json()
        
        # Check TikTok data
        self.assertEqual(tiktok_data["date"], tiktok_date)
        self.assertIn("TikTok", tiktok_data["title"])
        self.assertTrue(len(tiktok_data["real_absurd_clauses"]) == 5,
                       f"Expected 5 real clauses for TikTok, got {len(tiktok_data['real_absurd_clauses'])}")
        self.assertTrue(len(tiktok_data["fake_absurd_clauses"]) == 5,
                       f"Expected 5 fake clauses for TikTok, got {len(tiktok_data['fake_absurd_clauses'])}")
        
        print(f"✅ TikTok game data for {tiktok_date} retrieved successfully")
        
        # Test Slack (2025-08-02)
        slack_date = "2025-08-02"
        response = requests.get(f"{API_URL}/game/{slack_date}")
        self.assertEqual(response.status_code, 200)
        slack_data = response.json()
        
        # Check Slack data
        self.assertEqual(slack_data["date"], slack_date)
        self.assertIn("Slack", slack_data["title"])
        self.assertTrue(len(slack_data["real_absurd_clauses"]) == 5,
                       f"Expected 5 real clauses for Slack, got {len(slack_data['real_absurd_clauses'])}")
        self.assertTrue(len(slack_data["fake_absurd_clauses"]) == 5,
                       f"Expected 5 fake clauses for Slack, got {len(slack_data['fake_absurd_clauses'])}")
        
        print(f"✅ Slack game data for {slack_date} retrieved successfully")
        
        # Return all data for further testing
        return {
            "meta": meta_data,
            "tiktok": tiktok_data,
            "slack": slack_data
        }
    
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
    
    def test_game_result_submission_with_real_data(self):
        """Test submitting game results with real company data"""
        # Get company data
        company_data = self.test_specific_company_games()
        
        # Test submission for Meta
        meta_real_clause_ids = [clause["id"] for clause in company_data["meta"]["real_absurd_clauses"]]
        meta_selected_clauses = meta_real_clause_ids[:3]  # Select first 3 real clauses
        
        meta_submission_data = {
            "game_date": "2025-07-07",  # Meta date
            "session_id": "test_session_meta",
            "selected_clauses": meta_selected_clauses,
            "completion_time": 60
        }
        
        meta_response = requests.post(
            f"{API_URL}/game/submit", 
            json=meta_submission_data
        )
        
        self.assertEqual(meta_response.status_code, 200)
        meta_result = meta_response.json()
        
        # Check response structure
        self.assertIn("base_score", meta_result)
        self.assertIn("bonus_score", meta_result)
        self.assertIn("total_score", meta_result)
        self.assertIn("max_score", meta_result)
        self.assertIn("correct_answers", meta_result)
        self.assertIn("legal_detector_breakdown", meta_result)
        
        # Verify score calculation
        self.assertEqual(meta_result["base_score"], len(meta_selected_clauses))
        self.assertGreaterEqual(meta_result["total_score"], meta_result["base_score"])
        
        print("✅ Meta game result submission successful")
        
        # Test submission for TikTok
        tiktok_real_clause_ids = [clause["id"] for clause in company_data["tiktok"]["real_absurd_clauses"]]
        tiktok_selected_clauses = tiktok_real_clause_ids[:4]  # Select first 4 real clauses
        
        tiktok_submission_data = {
            "game_date": "2025-07-08",  # TikTok date
            "session_id": "test_session_tiktok",
            "selected_clauses": tiktok_selected_clauses,
            "completion_time": 45
        }
        
        tiktok_response = requests.post(
            f"{API_URL}/game/submit", 
            json=tiktok_submission_data
        )
        
        self.assertEqual(tiktok_response.status_code, 200)
        tiktok_result = tiktok_response.json()
        
        # Verify score calculation
        self.assertEqual(tiktok_result["base_score"], len(tiktok_selected_clauses))
        
        print("✅ TikTok game result submission successful")
        
        return {
            "meta_result": meta_result,
            "tiktok_result": tiktok_result
        }
    
    def test_game_stats(self):
        """Test getting game statistics"""
        # Submit results first to ensure we have stats
        submission_results = self.test_game_result_submission_with_real_data()
        
        # Get stats for Meta
        meta_date = "2025-07-07"
        meta_response = requests.get(f"{API_URL}/stats/{meta_date}")
        self.assertEqual(meta_response.status_code, 200)
        meta_stats = meta_response.json()
        
        # Check stats structure
        self.assertIn("date", meta_stats)
        self.assertIn("total_players", meta_stats)
        self.assertIn("clause_stats", meta_stats)
        
        # Verify data
        self.assertEqual(meta_stats["date"], meta_date)
        self.assertGreaterEqual(meta_stats["total_players"], 1)
        
        print(f"✅ Game statistics for Meta ({meta_date}) retrieved successfully")
        
        # Get stats for TikTok
        tiktok_date = "2025-07-08"
        tiktok_response = requests.get(f"{API_URL}/stats/{tiktok_date}")
        self.assertEqual(tiktok_response.status_code, 200)
        tiktok_stats = tiktok_response.json()
        
        # Verify data
        self.assertEqual(tiktok_stats["date"], tiktok_date)
        self.assertGreaterEqual(tiktok_stats["total_players"], 1)
        
        print(f"✅ Game statistics for TikTok ({tiktok_date}) retrieved successfully")
        
        return {
            "meta_stats": meta_stats,
            "tiktok_stats": tiktok_stats
        }
    
    def test_data_integrity(self):
        """Test data integrity of real business content"""
        # Get company data
        company_data = self.test_specific_company_games()
        
        # Check Meta data integrity
        meta_data = company_data["meta"]
        self.assertEqual(len(meta_data["real_absurd_clauses"]), 5)
        self.assertEqual(len(meta_data["fake_absurd_clauses"]), 5)
        self.assertEqual(len(meta_data["quiz_order"]), 10)
        
        # Verify all quiz_order items exist in clauses
        all_meta_clause_ids = [c["id"] for c in meta_data["real_absurd_clauses"] + meta_data["fake_absurd_clauses"]]
        for clause_id in meta_data["quiz_order"]:
            self.assertIn(clause_id, all_meta_clause_ids)
        
        # Check TikTok data integrity
        tiktok_data = company_data["tiktok"]
        self.assertEqual(len(tiktok_data["real_absurd_clauses"]), 5)
        self.assertEqual(len(tiktok_data["fake_absurd_clauses"]), 5)
        self.assertEqual(len(tiktok_data["quiz_order"]), 10)
        
        # Verify all quiz_order items exist in clauses
        all_tiktok_clause_ids = [c["id"] for c in tiktok_data["real_absurd_clauses"] + tiktok_data["fake_absurd_clauses"]]
        for clause_id in tiktok_data["quiz_order"]:
            self.assertIn(clause_id, all_tiktok_clause_ids)
        
        # Check Slack data integrity
        slack_data = company_data["slack"]
        self.assertEqual(len(slack_data["real_absurd_clauses"]), 5)
        self.assertEqual(len(slack_data["fake_absurd_clauses"]), 5)
        self.assertEqual(len(slack_data["quiz_order"]), 10)
        
        # Verify all quiz_order items exist in clauses
        all_slack_clause_ids = [c["id"] for c in slack_data["real_absurd_clauses"] + slack_data["fake_absurd_clauses"]]
        for clause_id in slack_data["quiz_order"]:
            self.assertIn(clause_id, all_slack_clause_ids)
        
        print("✅ Data integrity checks passed for all company data")
    
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
        
        # Check if the API properly handles this case
        if response.status_code == 200:
            print("✅ Submission for non-existent game handled correctly by creating fallback game")
        elif response.status_code == 404:
            print("✅ Submission for non-existent game correctly returns 404 Not Found")
        else:
            self.fail(f"Unexpected status code {response.status_code} for non-existent game submission")
    
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
    suite.addTest(TestTCBackendAPI('test_specific_company_games'))
    suite.addTest(TestTCBackendAPI('test_daily_game_valid_date'))
    suite.addTest(TestTCBackendAPI('test_daily_game_tomorrow'))
    suite.addTest(TestTCBackendAPI('test_daily_game_invalid_date'))
    suite.addTest(TestTCBackendAPI('test_game_result_submission_with_real_data'))
    suite.addTest(TestTCBackendAPI('test_data_integrity'))
    suite.addTest(TestTCBackendAPI('test_game_stats'))
    suite.addTest(TestTCBackendAPI('test_submit_nonexistent_game'))
    suite.addTest(TestTCBackendAPI('test_malformed_submission'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)