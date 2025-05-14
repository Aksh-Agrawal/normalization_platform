# api.py

import requests

def fetch_codeforces_profile_api(handle):
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] != 'OK':
            print(f"API error: {data.get('comment', 'Unknown error')}")
            return None
        
        user = data['result'][0]
        return {
            'rating': str(user.get('rating', 'N/A'))
        }
    except requests.RequestException as e:
        print(f"Error fetching profile via API: {e}")
        return None


def print_profile(profile):
    """Print the Codeforces rating"""
    if not profile:
        print("Unable to fetch Codeforces profile.")
    else:
        print(f"Codeforces Rating: {profile['rating']}")


if __name__ == "__main__":
    handle = input("Enter Codeforces handle: ")
    profile = fetch_codeforces_profile_api(handle)
    print_profile(profile)
