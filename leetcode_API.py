import requests
import json
import time

def fetch_leetcode_profile_api(username, max_retries=1, retry_delay=5):
    url = f"https://alfa-leetcode-api.onrender.com/users/{username}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
    }
    
    retries = 0
    while retries <= max_retries:
        try:
            print(f"Fetching data from: {url}")
            response = requests.get(url, headers=headers)
            
            # Handle rate limiting (429 Too Many Requests)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', retry_delay))
                print(f"Rate limited. API says: {response.text}")
                
                if retries < max_retries:
                    print(f"Waiting {retry_after} seconds before retrying... (Attempt {retries+1}/{max_retries})")
                    time.sleep(retry_after)
                    retries += 1
                    continue
                else:
                    print("Max retries reached. Please try again later.")
                    return None
            
            # For other non-200 responses
            if response.status_code != 200:
                print(f"API returned status code {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            
            # Debug the structure of the received data
            if isinstance(data, dict):
                print(f"Keys in response: {list(data.keys())}")
            
            # The API might return data directly without status indicators
            if not data:
                print("Received empty data")
                return None
                
            # Use user_slug as fallback for username if needed
            user_data = data  # The API seems to return user data directly
            
            profile_data = {
                'username': user_data.get('username', user_data.get('user_slug', username)),
                'name': user_data.get('full_name', user_data.get('name', 'N/A')),
                'ranking': str(user_data.get('profile_ranking', user_data.get('ranking', 'N/A'))),
                'solved_problems': str(user_data.get('solved_questions', user_data.get('totalSolved', user_data.get('total_problems_solved', 'N/A')))),
                'acceptance_rate': str(user_data.get('acceptance_rate', user_data.get('acceptanceRate', 'N/A'))),
                'easy_solved': str(user_data.get('easy_questions_solved', user_data.get('easySolved', 'N/A'))),
                'medium_solved': str(user_data.get('medium_questions_solved', user_data.get('mediumSolved', 'N/A'))),
                'hard_solved': str(user_data.get('hard_questions_solved', user_data.get('hardSolved', 'N/A'))),
                'contribution_points': str(user_data.get('contribution_points', user_data.get('contributionPoints', 'N/A'))),
                'reputation': str(user_data.get('reputation', 'N/A')),
                'streak': str(user_data.get('streak', 'N/A'))
            }
            
            # Clean up any None values
            for key in profile_data:
                if profile_data[key] is None:
                    profile_data[key] = 'N/A'
                    
            return profile_data
        except requests.RequestException as e:
            print(f"Error fetching profile via API: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {str(e)}")
            print(f"Response content: {response.text}")
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None

def print_profile_data(profile_data):
    if not profile_data:
        print("No profile data available.")
        return
    
    print("=" * 50)
    print("LeetCode Profile Information (via API)")
    print("=" * 50)
    print(f"Username: {profile_data['username']}")
    print(f"Name: {profile_data['name']}")
    print(f"Ranking: {profile_data['ranking']}")
    print(f"Total Solved Problems: {profile_data['solved_problems']}")
    print(f"Acceptance Rate: {profile_data['acceptance_rate']}")
    print(f"Easy Problems Solved: {profile_data['easy_solved']}")
    print(f"Medium Problems Solved: {profile_data['medium_solved']}")
    print(f"Hard Problems Solved: {profile_data['hard_solved']}")
    print(f"Contribution Points: {profile_data['contribution_points']}")
    print(f"Reputation: {profile_data['reputation']}")
    print(f"Streak: {profile_data['streak']}")
    print("=" * 50)

def main():
    username = input("Enter LeetCode username: ")
    print("\nAttempting to fetch LeetCode profile data...")
    print("Note: This API has rate limits. If you get a 'Too Many Requests' error,")
    print("you may need to wait up to an hour before trying again.\n")
    
    profile_data = fetch_leetcode_profile_api(username)
    print_profile_data(profile_data)
    
    if not profile_data:
        print("\nAlternative options:")
        print("1. Try again later when the rate limit resets")
        print("2. Use the official LeetCode GraphQL API")
        print("3. Try a different unofficial API or scraping approach")

if __name__ == "__main__":
    main()