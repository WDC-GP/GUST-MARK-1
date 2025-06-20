#!/usr/bin/env python3
"""
Token Debug Script
==================
Use this to debug token validation issues
"""

import json
import os

def analyze_token_file():
    """Analyze the token file if it exists"""
    if not os.path.exists('gp-session.json'):
        print("❌ No token file found")
        return
    
    try:
        with open('gp-session.json', 'r') as f:
            data = json.load(f)
        
        print("✅ Token file loaded successfully")
        print(f"📊 File contains {len(data)} fields")
        
        # Check each token
        for token_type in ['access_token', 'refresh_token']:
            if token_type in data:
                token = data[token_type]
                print(f"\n🔍 {token_type.upper()}:")
                print(f"   Length: {len(token)}")
                print(f"   First 20 chars: {token[:20]}...")
                print(f"   Last 10 chars: ...{token[-10:]}")
                
                # Character analysis
                special_chars = set()
                for char in token:
                    if not char.isalnum():
                        special_chars.add(char)
                
                print(f"   Special characters found: {sorted(special_chars)}")
                
                # Test validation
                allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_+/=')
                invalid_chars = [c for c in token if c not in allowed_chars]
                
                if invalid_chars:
                    print(f"   ❌ Invalid characters: {invalid_chars}")
                else:
                    print(f"   ✅ All characters are valid")
            else:
                print(f"\n❌ {token_type} not found in file")
        
        # Check expiration times
        for exp_field in ['access_token_exp', 'refresh_token_exp']:
            if exp_field in data:
                exp_time = data[exp_field]
                print(f"\n⏰ {exp_field}: {exp_time}")
                try:
                    from datetime import datetime
                    exp_datetime = datetime.fromtimestamp(exp_time)
                    print(f"   Expires at: {exp_datetime}")
                    
                    import time
                    time_left = exp_time - time.time()
                    print(f"   Time left: {time_left:.0f} seconds")
                except:
                    print(f"   ❌ Invalid timestamp format")
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
    except Exception as e:
        print(f"❌ Error reading file: {e}")

def test_token_validation():
    """Test the token validation function"""
    print("\n🧪 TESTING TOKEN VALIDATION FUNCTION")
    
    def is_valid_token(token):
        if not token or len(token) < 10:
            return False
        # Allow alphanumeric plus common OAuth/JWT characters: . - _ + / =
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_+/=')
        return all(c in allowed_chars for c in token)
    
    # Test various token formats
    test_tokens = [
        "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9",  # JWT header
        "abc123-def456_ghi789",  # Simple with hyphens/underscores
        "token.with.dots",
        "token+with+plus",
        "token/with/slashes",
        "token=with=equals",
        "short",  # Too short
        "token with spaces",  # Invalid character
        "token@with#special!chars",  # Invalid characters
    ]
    
    for token in test_tokens:
        valid = is_valid_token(token)
        status = "✅" if valid else "❌"
        print(f"   {status} '{token}' - Valid: {valid}")

def create_sample_tokens():
    """Create sample tokens for testing"""
    print("\n🔧 CREATING SAMPLE TOKEN FILE FOR TESTING")
    
    import time
    from datetime import datetime
    
    current_time = time.time()
    
    sample_data = {
        'access_token': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.test_signature',
        'refresh_token': 'def50200-1234-5678-9abc-def012345678.refresh_token_part',
        'access_token_exp': int(current_time + 3600),  # 1 hour
        'refresh_token_exp': int(current_time + 86400),  # 24 hours
        'timestamp': datetime.now().isoformat(),
        'username': 'test_user',
        'token_version': '2.0'
    }
    
    with open('gp-session-test.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("✅ Created gp-session-test.json with sample tokens")
    print("   You can rename this to gp-session.json to test")

def main():
    print("🔍 GUST Bot Token Debug Tool")
    print("=" * 40)
    
    # Analyze existing token file
    analyze_token_file()
    
    # Test validation function
    test_token_validation()
    
    # Offer to create sample tokens
    print("\n" + "=" * 40)
    response = input("Create sample token file for testing? (y/n): ")
    if response.lower() == 'y':
        create_sample_tokens()
    
    print("\n🎯 DEBUGGING TIPS:")
    print("1. Check if token file exists and is valid JSON")
    print("2. Verify tokens don't contain invalid characters")
    print("3. Check token length (should be 10+ characters)")
    print("4. Valid characters: a-z, A-Z, 0-9, ., -, _, +, /, =")
    print("5. If login fails, check browser network tab for actual token format")

if __name__ == "__main__":
    main()
