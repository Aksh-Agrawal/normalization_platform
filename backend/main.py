# main.py

from platform import UnifiedRankingSystem
from api import fetch_codeforces_profile_api
from leetcode_api import fetch_leetcode_profile

def run():
    ranking_system = UnifiedRankingSystem()

    handle_CF = input("Enter Codeforces handle_CF: ")
    profile_data_CF = fetch_codeforces_profile_api(handle_CF)

    if not profile_data_CF or profile_data_CF["rating"] == 'N/A':
        print("Could not retrieve valid Codeforces rating. Exiting.")
        return

    cf_rating = int(profile_data_CF["rating"])
    print(f"Codeforces Rating: {cf_rating}")

    # Fetch Leetcode profile
    handle_LC = input("Enter Leetcode handle_LC: ")
    profile_data_LC = fetch_leetcode_profile(handle_LC)
    if not profile_data_LC or profile_data_LC["rating"] == 'N/A':
        print("Could not retrieve valid Leetcode rating. Exiting.")
        return
    lc_rating = int(profile_data_LC["rating"])
    print(f"Leetcode Rating: {lc_rating}")
    

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
            current_ratings={handle_CF: cf_rating}
        )
    ranking_system.update_platform_stats(
            "Leetcode",
        difficulty=2100,
        participation=0.8,
        current_ratings={handle_LC: lc_rating}
    )

    # Dummy ratings for other platforms
    dummy_ratings = {
        # "Leetcode": {handle_CF: 3200},
        "Atcoder": {handle_CF: 3300},
        "CodeChef": {handle_CF: 3700}
    }

    platform_difficulty_participation = {
       
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

    # user - orzdevinwang