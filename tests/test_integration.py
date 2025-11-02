"""
Integration tests for the complete workflow
"""


class TestIntegration:
    """Integration tests for complete user workflows"""

    def test_complete_student_signup_workflow(self, client):
        """Test complete workflow: view activities, signup, verify, then remove"""
        student_email = "integration.test@mergington.edu"
        activity_name = "Art Club"
        
        # Step 1: Get all activities
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        assert activity_name in activities_data
        
        initial_participants = len(activities_data[activity_name]["participants"])
        
        # Step 2: Sign up for an activity
        response = client.post(f"/activities/{activity_name}/signup?email={student_email}")
        assert response.status_code == 200
        
        # Step 3: Verify signup by getting activities again
        response = client.get("/activities")
        assert response.status_code == 200
        updated_activities = response.json()
        
        assert len(updated_activities[activity_name]["participants"]) == initial_participants + 1
        assert student_email in updated_activities[activity_name]["participants"]
        
        # Step 4: Remove the student
        response = client.delete(f"/activities/{activity_name}/participants/{student_email}")
        assert response.status_code == 200
        
        # Step 5: Verify removal
        response = client.get("/activities")
        assert response.status_code == 200
        final_activities = response.json()
        
        assert len(final_activities[activity_name]["participants"]) == initial_participants
        assert student_email not in final_activities[activity_name]["participants"]

    def test_multiple_students_same_activity_workflow(self, client):
        """Test multiple students signing up for the same activity"""
        activity_name = "Theater Troupe"
        students = [
            "actor1@mergington.edu",
            "actor2@mergington.edu", 
            "actor3@mergington.edu"
        ]
        
        # Get initial participant count via API
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        initial_count = len(activities_data[activity_name]["participants"])
        
        # Multiple students sign up
        for student in students:
            response = client.post(f"/activities/{activity_name}/signup?email={student}")
            assert response.status_code == 200
        
        # Verify all are registered
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        
        current_participants = activities_data[activity_name]["participants"]
        assert len(current_participants) == initial_count + len(students)
        
        for student in students:
            assert student in current_participants
        
        # Remove students one by one
        for student in students:
            response = client.delete(f"/activities/{activity_name}/participants/{student}")
            assert response.status_code == 200
        
        # Verify all are removed
        response = client.get("/activities")
        assert response.status_code == 200
        final_activities = response.json()
        
        final_participants = final_activities[activity_name]["participants"]
        assert len(final_participants) == initial_count
        
        for student in students:
            assert student not in final_participants

    def test_student_multiple_activities_workflow(self, client):
        """Test one student signing up for multiple activities"""
        student_email = "busy.student@mergington.edu"
        target_activities = ["Math Club", "Debate Team", "Programming Class"]
        
        # Sign up for multiple activities
        for activity_name in target_activities:
            response = client.post(f"/activities/{activity_name}/signup?email={student_email}")
            assert response.status_code == 200
        
        # Verify student is in all activities
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        
        for activity_name in target_activities:
            assert student_email in activities_data[activity_name]["participants"]
        
        # Remove from one activity
        response = client.delete(f"/activities/{target_activities[0]}/participants/{student_email}")
        assert response.status_code == 200
        
        # Verify partial removal
        response = client.get("/activities")
        assert response.status_code == 200
        updated_activities = response.json()
        
        assert student_email not in updated_activities[target_activities[0]]["participants"]
        assert student_email in updated_activities[target_activities[1]]["participants"]
        assert student_email in updated_activities[target_activities[2]]["participants"]

    def test_activity_state_consistency(self, client):
        """Test that activity state remains consistent across operations"""
        activity_name = "Basketball Club"
        test_email = "consistency.test@mergington.edu"
        
        # Get initial state
        response = client.get("/activities")
        initial_state = response.json()[activity_name]
        initial_participants = initial_state["participants"].copy()
        
        # Perform various operations
        operations = [
            ("POST", f"/activities/{activity_name}/signup?email={test_email}"),
            ("GET", "/activities"),
            ("DELETE", f"/activities/{activity_name}/participants/{test_email}"),
            ("GET", "/activities"),
        ]
        
        for method, url in operations:
            if method == "POST":
                response = client.post(url)
            elif method == "DELETE":
                response = client.delete(url)
            else:  # GET
                response = client.get(url)
            
            assert response.status_code == 200
        
        # Verify final state matches initial state
        response = client.get("/activities")
        final_state = response.json()[activity_name]
        
        assert final_state["description"] == initial_state["description"]
        assert final_state["schedule"] == initial_state["schedule"]
        assert final_state["max_participants"] == initial_state["max_participants"]
        assert final_state["participants"] == initial_participants

    def test_error_recovery_workflow(self, client):
        """Test system behavior after error conditions"""
        student_email = "error.test@mergington.edu"
        
        # Attempt invalid operations
        invalid_operations = [
            ("POST", "/activities/NonExistent/signup", {"email": student_email}),
            ("DELETE", "/activities/NonExistent/participants/anyone", {}),
            ("DELETE", "/activities/Chess Club/participants/nonexistent@email.com", {}),
        ]
        
        for method, url, params in invalid_operations:
            if method == "POST":
                if params:
                    response = client.post(f"{url}?email={params['email']}")
                else:
                    response = client.post(url)
            else:  # DELETE
                response = client.delete(url)
            
            assert response.status_code in [404, 422]  # Expected error codes
        
        # Verify system still works after errors
        response = client.get("/activities")
        assert response.status_code == 200
        
        # Verify normal operations still work
        response = client.post(f"/activities/Chess Club/signup?email={student_email}")
        assert response.status_code == 200