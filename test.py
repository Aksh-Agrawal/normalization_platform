import requests
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import math

# -------- Codeforces API Fetch --------
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

# -------- Classes --------
class Platform:
    def __init__(self, name, max_rating=5000):
        self.name = name
        self.max_rating = max_rating
        self.difficulty = None
        self.participation = None
        self.drift = None
        self.last_update = None
        self.user_ratings = defaultdict(dict)
        self.historical_stats = []

    def update_stats(self, difficulty, participation, current_ratings):
        self.historical_stats.append({
            'difficulty': difficulty,
            'participation': participation,
            'avg_rating': np.mean(list(current_ratings.values())) if current_ratings else 0,
            'timestamp': datetime.now()
        })

        self.difficulty = difficulty / self.max_rating
        self.participation = participation
        self.drift = self._calculate_drift(current_ratings)
        self.last_update = datetime.now()

        for user_id, rating in current_ratings.items():
            self.user_ratings[user_id][datetime.now()] = rating

    def _calculate_drift(self, current_ratings):
        if not self.historical_stats or not current_ratings:
            return 0.0
        hist_avg = np.mean([s['avg_rating'] for s in self.historical_stats[-5:]])
        current_avg = np.mean(list(current_ratings.values()))
        return abs(current_avg - hist_avg) / self.max_rating

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.platform_ratings = {}
        self.completed_courses = []
        self.unified_rating = 0.0
        self.course_bonus = 0.0
        self.total_rating = 0.0

class UnifiedRankingSystem:
    def __init__(self, alpha=0.5, beta=0.3, gamma=0.2, decay_lambda=0.01):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.decay_lambda = decay_lambda
        self.platforms = {}
        self.users = {}
        self.raw_weights = {}
        self.softmax_weights = {}
        self.final_weights = {}

    def add_platform(self, platform_name, max_rating=5000):
        self.platforms[platform_name] = Platform(platform_name, max_rating)

    def add_user(self, user_id):
        self.users[user_id] = User(user_id)

    def update_platform_stats(self, platform_name, difficulty, participation, current_ratings):
        if platform_name not in self.platforms:
            raise ValueError(f"Platform {platform_name} not found")
        platform = self.platforms[platform_name]
        platform.update_stats(difficulty, participation, current_ratings)

        for user_id, rating in current_ratings.items():
            if user_id not in self.users:
                self.add_user(user_id)
            self.users[user_id].platform_ratings[platform_name] = rating

        self._calculate_weights()
        self._update_all_ratings()

    def _calculate_weights(self):
        self.raw_weights = {}
        for platform_name, platform in self.platforms.items():
            if None in [platform.difficulty, platform.participation, platform.drift]:
                continue
            delta_t = (datetime.now() - platform.last_update).days if platform.last_update else 0
            raw_weight = (self.alpha * platform.difficulty +
                          self.beta * platform.participation +
                          self.gamma * platform.drift)
            self.raw_weights[platform_name] = raw_weight

        exp_weights = {p: math.exp(w) for p, w in self.raw_weights.items()}
        sum_exp = sum(exp_weights.values()) or 1e-8
        self.softmax_weights = {p: w / sum_exp for p, w in exp_weights.items()}

        self.final_weights = {}
        for platform_name, platform in self.platforms.items():
            if platform.last_update is None:
                continue
            delta_t = (datetime.now() - platform.last_update).days
            self.final_weights[platform_name] = (
                self.softmax_weights[platform_name] *
                math.exp(-self.decay_lambda * delta_t))

    def _impute_missing_rating(self, user, platform_name):
        valid_ratings = [r for p, r in user.platform_ratings.items() if p != platform_name]
        if valid_ratings:
            return np.mean(valid_ratings)
        platform = self.platforms[platform_name]
        if platform.historical_stats:
            return np.mean([s['avg_rating'] for s in platform.historical_stats[-3:]])
        return platform.max_rating * 0.5

    def _update_all_ratings(self):
        for user in self.users.values():
            unified_rating = 0.0
            total_weight = 0.0
            for platform_name, weight in self.final_weights.items():
                rating = user.platform_ratings.get(platform_name)
                if rating is None:
                    rating = self._impute_missing_rating(user, platform_name)
                unified_rating += weight * rating
                total_weight += weight
            user.unified_rating = unified_rating / total_weight if total_weight > 0 else 0
            user.total_rating = user.unified_rating

    def get_rankings(self, top_n=None):
        sorted_users = sorted(self.users.values(), key=lambda u: -u.total_rating)
        rankings = []
        for user in sorted_users:
            rankings.append((
                user.user_id,
                user.unified_rating,
                user.course_bonus,
                user.total_rating
            ))
        return rankings[:top_n] if top_n else rankings

# -------- Main Execution --------
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
