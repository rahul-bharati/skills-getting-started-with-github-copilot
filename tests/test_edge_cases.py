"""
Tests for data validation and edge cases
"""


class TestValidationAndEdgeCases:
    """Test class for validation and edge cases"""

    def test_empty_email_parameter(self, client):
        """Test signup with empty email parameter"""
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email=")
        # FastAPI should handle this - might still work with empty string
        # The validation depends on how strict we want to be
        assert response.status_code in [200, 400, 422]

    def test_missing_email_parameter(self, client):
        """Test signup without email parameter"""
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup")
        assert response.status_code == 422  # Unprocessable Entity due to missing required parameter

    def test_invalid_email_format(self, client):
        """Test signup with invalid email format"""
        activity_name = "Chess Club"
        invalid_emails = [
            "not-an-email",
            "@mergington.edu",
            "student@",
            "student.mergington.edu",
            "student@mergington",
        ]
        
        for email in invalid_emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            # The backend doesn't validate email format, so these will succeed
            # In a real app, you might want email validation
            assert response.status_code == 200

    def test_very_long_email(self, client):
        """Test signup with very long email"""
        activity_name = "Chess Club"
        long_email = "a" * 100 + "@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={long_email}")
        assert response.status_code == 200

    def test_special_characters_in_activity_name(self, client):
        """Test with special characters in activity name"""
        email = "student@mergington.edu"
        # Test with non-existent activity that has special characters
        special_activity = "Test & Fun Club!"
        
        response = client.post(f"/activities/{special_activity}/signup?email={email}")
        assert response.status_code == 404

    def test_case_sensitivity_activity_names(self, client):
        """Test case sensitivity in activity names"""
        email = "student@mergington.edu"
        
        # Test with different case
        response = client.post("/activities/chess%20club/signup", params={"email": email})
        assert response.status_code == 404  # Should be case sensitive
        
        response = client.post("/activities/CHESS%20CLUB/signup", params={"email": email})
        assert response.status_code == 404  # Should be case sensitive

    def test_unicode_characters(self, client):
        """Test with unicode characters in email"""
        activity_name = "Chess Club"
        unicode_email = "tëst@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={unicode_email}")
        assert response.status_code == 200

    def test_sql_injection_attempt(self, client):
        """Test potential SQL injection in parameters"""
        activity_name = "Chess Club"
        malicious_email = "'; DROP TABLE activities; --"
        
        # Should be safe since we're not using SQL database
        response = client.post(f"/activities/{activity_name}/signup?email={malicious_email}")
        assert response.status_code == 200

    def test_multiple_signups_same_email_different_activities(self, client):
        """Test that same email can sign up for multiple activities"""
        email = "versatile@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Art Club"]
        
        for activity_name in activities_to_join:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
            
            # Use the API to verify the participant was added
            activities_response = client.get("/activities")
            assert activities_response.status_code == 200
            activities_data = activities_response.json()
            assert email in activities_data[activity_name]["participants"]

    def test_remove_participant_multiple_times(self, client):
        """Test removing the same participant multiple times"""
        email = "test@mergington.edu"
        activity_name = "Chess Club"
        
        # First add the participant
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        # Remove participant first time
        response = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert response.status_code == 200
        
        # Try to remove again - should fail
        response = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert response.status_code == 404

    def test_concurrent_signups_same_activity(self, client):
        """Test multiple signups for same activity (simulating concurrent requests)"""
        activity_name = "Programming Class"
        emails = [f"concurrent{i}@mergington.edu" for i in range(5)]
        
        # Get initial participant count via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        initial_count = len(activities_data[activity_name]["participants"])
        
        # Simulate concurrent signups
        for email in emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all were added via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        final_count = len(activities_data[activity_name]["participants"])
        assert final_count == initial_count + len(emails)
        
        for email in emails:
            assert email in activities_data[activity_name]["participants"]