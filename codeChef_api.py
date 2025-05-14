import requests
import re

def fetch_codechef_profile(username):
    url = f"https://www.codechef.com/users/{username}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {'error': f"Failed to fetch profile. HTTP {response.status_code}"}

        html = response.text

        # Rating (e.g., <div class="rating-number">1797</div>)
        rating_match = re.search(r'<div class="rating-number">(\d+)</div>', html)
        rating = rating_match.group(1) if rating_match else 'N/A'

        # Stars (e.g., <span class="rating">★★★★</span>)
        # stars_match = re.search(r'<span class="rating">([^<]+)</span>', html)
        # stars = stars_match.group(1).strip() if stars_match else 'N/A'

        # Global Rank (e.g., <a href="/ratings/all">123</a>)
        # global_rank_match = re.search(r'<td>Global Rank</td>\s*<td>\s*<a [^>]+>([^<]+)</a>', html)
        # global_rank = global_rank_match.group(1).strip() if global_rank_match else 'N/A'

        # Fully Solved Problems (e.g., Fully Solved \(123\))
        # fully_solved_match = re.search(r'Fully Solved\s*\((\d+)\)', html)
        # fully_solved = fully_solved_match.group(1) if fully_solved_match else 'N/A'

        return {
            'username': username,
            'rating': rating
        }

    except requests.RequestException as e:
        return {'error': f"Connection error: {str(e)}"}
    except Exception as e:
        return {'error': f"Unexpected error: {str(e)}"}

def print_codechef_profile(profile):
    if 'error' in profile:
        print(f"Error: {profile['error']}")
        return

    print(f"\nCodeChef Profile: @{profile['username']}")
    print(f"Rating        : {profile['rating']}")
   

def main():
    username = input("Enter CodeChef username: ")
    profile = fetch_codechef_profile(username)
    print_codechef_profile(profile)

if __name__ == "__main__":
    main()
