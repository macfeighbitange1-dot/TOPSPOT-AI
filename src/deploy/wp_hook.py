import requests
import base64
import json

class WordPressHook:
    def __init__(self, site_url, username, app_password):
        self.base_url = f"{site_url.rstrip('/')}/wp-json/wp/v2"
        auth_string = f"{username}:{app_password}"
        self.token = base64.b64encode(auth_string.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {self.token}',
            'Content-Type': 'application/json'
        }

    def push_schema(self, post_id: int, schema_data: dict):
        """
        Updates the post meta to include the new AEO-optimized Schema.
        """
        # We wrap the schema in a script tag for the content or a custom field
        schema_script = f"\n<script type='application/ld+json'>\n{json.dumps(schema_data, indent=2)}\n</script>"
        
        # Option: Append to the end of the post content
        # For a cleaner approach, you'd use a custom field like 'aeo_schema'
        try:
            get_post = requests.get(f"{self.base_url}/posts/{post_id}", headers=self.headers)
            current_content = get_post.json().get('content', {}).get('raw', '')
            
            payload = {
                'content': current_content + schema_script
            }
            
            response = requests.post(f"{self.base_url}/posts/{post_id}", headers=self.headers, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"[!] Deployment Error: {e}")
            return False