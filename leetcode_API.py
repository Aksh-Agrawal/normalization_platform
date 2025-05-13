import requests
import json

def fetch_leetcode_profile(username):
    """
    Fetch LeetCode profile using official GraphQL API
    """
    api_url = 'https://leetcode.com/graphql/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Referer': f'https://leetcode.com/{username}/',
        'Origin': 'https://leetcode.com'
    }

    query = """
    query getUserProfile($username: String!) {
        userContestRanking(username: $username) {
            attendedContestsCount
            rating
            globalRanking
        }
        matchedUser(username: $username) {
            profile {
                realName
            }
            submitStats {
                acSubmissionNum {
                    difficulty
                    count
                }
            }
            tagProblemCounts {
                advanced {
                    tagName
                    problemsSolved
                }
                intermediate {
                    tagName
                    problemsSolved
                }
                fundamental {
                    tagName
                    problemsSolved
                }
            }
        }
    }
    """

    variables = {'username': username}

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json={'query': query, 'variables': variables},
            timeout=10
        )

        if response.status_code != 200:
            return {'error': f'API Error: HTTP {response.status_code}'}

        data = response.json()
        
        if 'errors' in data:
            return {'error': 'User not found'}

        profile = data['data']['matchedUser']
        contest = data['data']['userContestRanking'] or {}

        # Process solved problems
        solved = {s['difficulty']: s['count'] for s in profile['submitStats']['acSubmissionNum']}

        # Process tags (combine all categories)
        tags = []
        for category in ['fundamental', 'intermediate', 'advanced']:
            tags.extend(profile['tagProblemCounts'][category])

        return {
            'username': username,
            'name': profile['profile']['realName'],
            'ranking': contest.get('globalRanking', 'N/A'),
            'contests': contest.get('attendedContestsCount', 0),
            'rating': contest.get('rating', 'N/A'),
            'total_solved': solved.get('All', 0),
            'easy_solved': solved.get('Easy', 0),
            'medium_solved': solved.get('Medium', 0),
            'hard_solved': solved.get('Hard', 0),
            'top_tags': sorted(
                [{'tag': t['tagName'], 'solved': t['problemsSolved']} for t in tags],
                key=lambda x: x['solved'], 
                reverse=True
            )[:10]  # Top 10 tags
        }

    except requests.RequestException as e:
        return {'error': f'Connection error: {str(e)}'}
    except KeyError as e:
        return {'error': f'Unexpected API response format: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def print_profile(profile):
    """Print formatted profile information"""
    if 'error' in profile:
        print(f"Error: {profile['error']}")
        return

    #print(f"LeetCode Profile: {profile['username']}")
    #print("="*50)
    #print(f"Name: {profile['name']}")
    #print(f"Global Ranking: {profile['ranking']}")
    #print(f"Contests Participated: {profile['contests']}")
    print(f"Contest Rating: {profile['rating']:.2f}" if isinstance(profile['rating'], float) else f"Contest Rating: {profile['rating']}")
    # print("\nSolved Problems:")
    # print(f"Total: {profile['total_solved']}")
    # print(f"Easy: {profile['easy_solved']} | Medium: {profile['medium_solved']} | Hard: {profile['hard_solved']}")
    
    # if profile['top_tags']:
    #     print("\nTop Problem Tags:")
    #     for tag in profile['top_tags']:
    #         print(f"- {tag['tag']}: {tag['solved']} solved")

    # print("="*50 + "\n")

def main():
    username = input("Enter LeetCode username: ")
    data = fetch_leetcode_profile(username)
    print_profile(data)

if __name__ == "__main__":
    main()
    