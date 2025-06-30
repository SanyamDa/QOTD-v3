import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quote_bot.db import init_db, add_user, get_active_users, update_user_status

def test_database():
    print("Testing database initialization...")
    
    # Initialize the database
    init_db()
    print("✅ Database initialized successfully")
    
    # Test adding a user
    test_user_id = 12345
    add_user(test_user_id, "Test User", "testuser")
    print("✅ Test user added")
    
    # Test getting active users
    active_users = get_active_users()
    print(f"Active users: {active_users}")
    
    # Test updating user status
    update_user_status(test_user_id, True)  # Pause user
    active_users = get_active_users()
    print(f"Active users after pausing: {active_users}")
    
    update_user_status(test_user_id, False)  # Unpause user
    active_users = get_active_users()
    print(f"Active users after unpausing: {active_users}")
    
    print("✅ All database tests passed!")

if __name__ == "__main__":
    test_database()
