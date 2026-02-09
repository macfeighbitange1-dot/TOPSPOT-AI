import json
import os

def reset_system():
    data_file = "app_usage.json"
    default_data = {
        "trials": 0, 
        "is_pro": False, 
        "trans_id": None,
        "free_token_used": False
    }
    
    with open(data_file, "w") as f:
        json.dump(default_data, f, indent=4)
    
    # Also clear the last audit result to start fresh
    if os.path.exists("last_fix.json"):
        os.remove("last_fix.json")
        
    print("✅ System Reset: You are now a 'New User' with 1 Free Premium Token.")

if __name__ == "__main__":
    reset_system()