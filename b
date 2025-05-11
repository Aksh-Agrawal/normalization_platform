import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import math

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

class Course:
    def __init__(self, course_id, name, source, topic, completion_date, verified=True):
        self.course_id = course_id
        self.name = name
        self.source = source
        self.topic = topic
        self.completion_date = completion_date
        self.verified = verified
        self.verification_date = datetime.now() if verified else None

    def days_since_completion(self):
        return (datetime.now() - self.completion_date).days

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
        self.regression_coeffs = {'a': 0.8, 'b': 0.2, 'c': -200}
        self.platforms = {}
        self.users = {}
        self.raw_weights = {}
        self.softmax_weights = {}
        self.final_weights = {}
        
        # Course parameters
        self.SOURCE_WEIGHTS = {'IIT': 1.0, 'NPTEL': 0.9, 'Coursera': 0.7, 'Udemy': 0.5}
        self.TOPIC_WEIGHTS = {'DSA': 1.0, 'AI': 0.9, 'Web Dev': 0.8}
        self.BASE_COURSE_BONUS = 50
        self.MAX_COURSE_BONUS = 200
        self.COURSE_DECAY_LAMBDA = 0.01

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
        self.softmax_weights = {p: w/sum_exp for p, w in exp_weights.items()}
        
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
            user.course_bonus = self._calculate_course_bonus(user)
            user.total_rating = user.unified_rating + user.course_bonus

    def _calculate_course_bonus(self, user: User) -> float:
        total_bonus = 0.0
        for course in user.completed_courses:
            if not course.verified:
                continue
            
            source_weight = self.SOURCE_WEIGHTS.get(course.source, 0.4)
            topic_weight = self.TOPIC_WEIGHTS.get(course.topic, 0.6)
            recency = math.exp(-self.COURSE_DECAY_LAMBDA * course.days_since_completion())
            
            course_contribution = self.BASE_COURSE_BONUS * source_weight * topic_weight * recency
            total_bonus += course_contribution
        
        return min(total_bonus, self.MAX_COURSE_BONUS)

    def update_course_completions(self, course_id: str, name: str, source: str, topic: str,
                                completion_date: datetime, user_ids: list, verified=True):
        for user_id in user_ids:
            if user_id not in self.users:
                self.add_user(user_id)
                
            course = Course(
                course_id=course_id,
                name=name,
                source=source,
                topic=topic,
                completion_date=completion_date,
                verified=verified
            )
            self.users[user_id].completed_courses.append(course)
        
        self._update_all_ratings()

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

if __name__ == "__main__":
    ranking_system = UnifiedRankingSystem()
    
    # Add platforms
    ranking_system.add_platform("Codeforces", max_rating=3000)
    ranking_system.add_platform("Leetcode", max_rating=2500)
    ranking_system.add_platform("Atcoder", max_rating=2800)
    ranking_system.add_platform("CodeChef", max_rating=1800)
    
    # Update platform statistics
    ranking_system.update_platform_stats(
        "Codeforces", 
        difficulty=2100, 
        participation=0.8, 
        current_ratings={
            "user1": 1900,
            "user2": 2100,
            "user3": 2400
        }
    )
    
    ranking_system.update_platform_stats(
        "Leetcode", 
        difficulty=1800, 
        participation=0.9, 
        current_ratings={
            "user1": 2000,
            "user2": 1900,
            "user4": 2200
        }
    )
    
    ranking_system.update_platform_stats(
        "Atcoder", 
        difficulty=2000, 
        participation=0.7, 
        current_ratings={
            "user1": 1800,
            "user3": 2000,
            "user5": 2300
        }
    )

    ranking_system.update_platform_stats(
        "CodeChef", 
        difficulty=1, 
        participation=0.2, 
        current_ratings={"user5": 1800}
    )
    
    # Add course completions
    ranking_system.update_course_completions(
        course_id="cs101",
        name="DSA Fundamentals",
        source="IIT",
        topic="DSA",
        completion_date=datetime.now() - timedelta(days=30),
        user_ids=["user1", "user2", "user3"]
    )
    
    ranking_system.update_course_completions(
        course_id="ai202",
        name="AI Bootcamp",
        source="Coursera",
        topic="AI",
        completion_date=datetime.now() - timedelta(days=180),
        user_ids=["user1", "user4"]
    )
    
    ranking_system.update_course_completions(
        course_id="web303",
        name="Web Development",
        source="Udemy",
        topic="Web Dev",
        completion_date=datetime.now() - timedelta(days=10),
        user_ids=["user5"]
    )
    
    # Display rankings
    print("Final Rankings:")
    print(f"{'Rank':<5} {'User ID':<10} {'Platform Rating':<15} {'Course Bonus':<15} {'Total Rating':<15}")
    for i, (user_id, platform, course, total) in enumerate(ranking_system.get_rankings(), 1):
        print(f"{i:<5} {user_id:<10} {platform:<15.1f} {course:<15.1f} {total:<15.1f}")



def main():
    handle = input("Enter Codeforces handle: ")
    profile_data = fetch_codeforces_profile_api(handle)
    
    if not profile_data or profile_data["rating"] == 'N/A':
        print("Could not retrieve valid rating. Exiting.")
        return

    cf_rating = int(profile_data["rating"])

    # Initialize system
    ranking_system = UnifiedRankingSystem()
    ranking_system.add_platform("Codeforces", max_rating=3000)
    ranking_system.add_platform("Leetcode", max_rating=2500)
    ranking_system.add_platform("Atcoder", max_rating=2800)
    ranking_system.add_platform("CodeChef", max_rating=1800)

    # Update only Codeforces with live data
    ranking_system.update_platform_stats(
        "Codeforces",
        difficulty=2100,
        participation=0.8,
        current_ratings={handle: cf_rating}
    )

    # Placeholder data for other platforms
    for p in ["Leetcode", "Atcoder", "CodeChef"]:
        ranking_system.update_platform_stats(
            p,
            difficulty=1,
            participation=0.1,
            current_ratings={}
        )

    # Display rankings
    print("Final Rankings:")
    print(f"{'Rank':<5} {'User ID':<10} {'Platform Rating':<15} {'Course Bonus':<15} {'Total Rating':<15}")
    for i, (user_id, platform, course, total) in enumerate(ranking_system.get_rankings(), 1):
        print(f"{i:<5} {user_id:<10} {platform:<15.1f} {course:<15.1f} {total:<15.1f}")
