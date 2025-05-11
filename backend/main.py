# main.py

from platform import UnifiedRankingSystem
from api import fetch_codeforces_profile_api

def run():
    ranking_system = UnifiedRankingSystem()

    handle = input("Enter Codeforces handle: ")
    profile_data = fetch_codeforces_profile_api(handle)

    if not profile_data or profile_data["rating"] == 'N/A':
        print("Could not retrieve valid Codeforces rating. Exiting.")
        return

    cf_rating = int(profile_data["rating"])

    # Add all platforms
    ranking_system.add_platform("Codeforces", max_rating=3000)
    ranking_system.add_platform("Leetcode", max_rating=2500)
    ranking_system.add_platform("Atcoder", max_rating=2800)
    ranking_system.add_platform("CodeChef", max_rating=1800)

    # Update Codeforces with real rating
    ranking_system.update_platform_stats(
        "Codeforces",
        difficulty=2100,
        participation=0.8,
        current_ratings={handle: cf_rating}
    )

    # Dummy ratings for other platforms
    dummy_ratings = {
        "Leetcode": {handle: 3200},
        "Atcoder": {handle: 3300},
        "CodeChef": {handle: 3700}
    }

    platform_difficulty_participation = {
        "Leetcode": (3400, 0.7),
        "Atcoder": (3500, 0.6),
        "CodeChef": (3800, 0.5)
    }

    for platform, (difficulty, participation) in platform_difficulty_participation.items():
        ranking_system.update_platform_stats(
            platform,
            difficulty=difficulty,
            participation=participation,
            current_ratings=dummy_ratings.get(platform, {})
        )

    # Final Output
    print("\nFinal Rankings:")
    print(f"{'Rank':<5} {'User ID':<15} {'Platform Rating':<18} {'Course Bonus':<15} {'Total Rating':<15}")
    for i, (user_id, platform_rating, course_bonus, total) in enumerate(ranking_system.get_rankings(), 1):
        print(f"{i:<5} {user_id:<15} {platform_rating:<18.1f} {course_bonus:<15.1f} {total:<15.1f}")

if __name__ == "__main__":
    run()
