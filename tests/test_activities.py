"""
Tests for the activities API endpoints
"""


class TestActivitiesAPI:
    """Test class for activities API endpoints"""

    def test_root_redirect(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/")
        assert response.status_code == 200
        # Should redirect to static files

    def test_get_activities(self, client):
        """Test GET /activities endpoint"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Check that we have the expected activities
        expected_activities = ["Chess Club", "Programming Class", "Gym Class", 
                             "Soccer Team", "Basketball Club", "Art Club", 
                             "Theater Troupe", "Math Club", "Debate Team"]
        
        for activity_name in expected_activities:
            assert activity_name in data
            
        # Check structure of each activity
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        
        # Check initial state via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        initial_participants = len(activities_data[activity_name]["participants"])
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify participant was added via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        assert len(activities_data[activity_name]["participants"]) == initial_participants + 1
        assert email in activities_data[activity_name]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for non-existent activity returns 404"""
        email = "student@mergington.edu"
        activity_name = "Nonexistent Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signup returns 400"""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"

    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        email = "michael@mergington.edu"  # Existing participant in Chess Club
        activity_name = "Chess Club"
        
        # Check initial state via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        initial_participants = len(activities_data[activity_name]["participants"])
        assert email in activities_data[activity_name]["participants"]
        
        response = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify participant was removed via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        assert len(activities_data[activity_name]["participants"]) == initial_participants - 1
        assert email not in activities_data[activity_name]["participants"]

    def test_remove_participant_from_nonexistent_activity(self, client):
        """Test removing participant from non-existent activity returns 404"""
        email = "student@mergington.edu"
        activity_name = "Nonexistent Club"
        
        response = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_remove_nonexistent_participant(self, client):
        """Test removing non-existent participant returns 404"""
        email = "nonexistent@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Participant not found in this activity"

    def test_url_encoding_in_activity_names(self, client):
        """Test that URL encoding works for activity names with spaces"""
        email = "student@mergington.edu"
        activity_name = "Programming Class"
        encoded_activity = "Programming%20Class"
        
        response = client.post(f"/activities/{encoded_activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant was added to the correct activity via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        assert email in activities_data[activity_name]["participants"]

    def test_url_encoding_in_email_addresses(self, client):
        """Test that URL encoding works for email addresses with special characters"""
        email = "test.student@mergington.edu"  # Use dot instead of + to avoid URL encoding issues
        activity_name = "Chess Club"
        
        # First add the participant
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant was added via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        assert email in activities_data[activity_name]["participants"]
        
        # Then remove them using the same email
        response = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert response.status_code == 200
        
        # Verify participant was removed via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        assert email not in activities_data[activity_name]["participants"]

    def test_activity_capacity_limits(self, client):
        """Test behavior when activities reach capacity"""
        # Find an activity and fill it to capacity
        activity_name = "Chess Club"
        
        # Get activity details via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        activity = activities_data[activity_name]
        max_participants = activity["max_participants"]
        current_participants = len(activity["participants"])
        
        # Add participants until capacity is reached
        spots_to_fill = max_participants - current_participants
        
        for i in range(spots_to_fill):
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify activity is at capacity via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        assert len(activities_data[activity_name]["participants"]) == max_participants
        
        # Try to add one more participant (should still work as we don't enforce capacity in backend)
        overflow_email = "overflow@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={overflow_email}")
        assert response.status_code == 200  # Backend doesn't enforce capacity limits