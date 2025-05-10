import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import math
import sqlite3
import json
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ranking_system.log'
)
logger = logging.getLogger('ranking_system')

class Database:
    """Database manager for the ranking system."""
    
    def __init__(self, db_path="ranking_system.db"):
        self.db_path = db_path
        self._initialize_db()
        
    def _initialize_db(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS platforms (
                name TEXT PRIMARY KEY,
                max_rating REAL,
                difficulty REAL,
                participation REAL,
                drift REAL,
                last_update TEXT,
                historical_stats TEXT
            )
            ''')
            
            conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                platform_ratings TEXT,
                unified_rating REAL,
                course_bonus REAL,
                total_rating REAL
            )
            ''')
            
            conn.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT,
                user_id TEXT,
                name TEXT,
                source TEXT,
                topic TEXT,
                completion_date TEXT,
                verified INTEGER,
                verification_date TEXT,
                PRIMARY KEY (course_id, user_id)
            )
            ''')
            
            conn.execute('''
            CREATE TABLE IF NOT EXISTS user_platform_ratings (
                user_id TEXT,
                platform_name TEXT,
                rating REAL,
                timestamp TEXT,
                PRIMARY KEY (user_id, platform_name, timestamp)
            )
            ''')
            
            conn.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            ''')
            
    def save_platform(self, platform):
        """Save platform data to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    '''INSERT OR REPLACE INTO platforms 
                    (name, max_rating, difficulty, participation, drift, last_update, historical_stats) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        platform.name,
                        platform.max_rating,
                        platform.difficulty,
                        platform.participation,
                        platform.drift,
                        platform.last_update.isoformat() if platform.last_update else None,
                        json.dumps(platform.historical_stats)
                    )
                )
            logger.info(f"Saved platform: {platform.name}")
            return True
        except Exception as e:
            logger.error(f"Error saving platform {platform.name}: {e}")
            return False
    
    # Add similar methods for saving/loading users, courses, etc.

class UnifiedRankingSystem:
        def __init__(self, config_path=None, **kwargs):
            """Initialize the ranking system with configuration."""
            # Default configuration
            self.config = {
                'alpha': 0.5,
                'beta': 0.3,
                'gamma': 0.2,
                'decay_lambda': 0.01,
                'regression_coeffs': {'a': 0.8, 'b': 0.2, 'c': -200},
                'source_weights': {'IIT': 1.0, 'NPTEL': 0.9, 'Coursera': 0.7, 'Udemy': 0.5},
                'topic_weights': {'DSA': 1.0, 'AI': 0.9, 'Web Dev': 0.8},
                'base_course_bonus': 50,
                'max_course_bonus': 200,
                'course_decay_lambda': 0.01,
                'min_rating': 0,
                'default_platform_max_rating': 5000,
            }
            
            # Load configuration from file if provided
            if config_path and os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        file_config = json.load(f)
                        self.config.update(file_config)
                    logger.info(f"Loaded configuration from {config_path}")
                except Exception as e:
                    logger.error(f"Error loading configuration: {e}")
            
            # Override with any provided kwargs
            for key, value in kwargs.items():
                if key in self.config:
                    self.config[key] = value
            
            # Initialize database
            self.db = Database()
            
            # Initialize system properties from config
            self.alpha = self.config['alpha']
            self.beta = self.config['beta']
            self.gamma = self.config['gamma']
            self.decay_lambda = self.config['decay_lambda']
            self.regression_coeffs = self.config['regression_coeffs']
            self.SOURCE_WEIGHTS = self.config['source_weights']
            self.TOPIC_WEIGHTS = self.config['topic_weights']
            self.BASE_COURSE_BONUS = self.config['base_course_bonus']
            self.MAX_COURSE_BONUS = self.config['max_course_bonus']
            self.COURSE_DECAY_LAMBDA = self.config['course_decay_lambda']
            
            # Initialize data structures
            self.platforms = {}
            self.users = {}
            self.raw_weights = {}
            self.softmax_weights = {}
            self.final_weights = {}
            
            # Load existing data
            self._load_data()
            
        def _load_data(self):
            """Load existing data from database."""
            # Implementation to load platforms, users, etc.
            pass
    
        def _update_user_rating(self, user_id):
            """Update a single user's rating instead of all users."""
            if user_id not in self.users:
                logger.warning(f"Attempted to update non-existent user: {user_id}")
                return
                
            user = self.users[user_id]
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
            
            # Save updated user to database
            self.db.save_user(user)
            
        def update_platform_stats(self, platform_name, difficulty, participation, current_ratings):
            if platform_name not in self.platforms:
                raise ValueError(f"Platform {platform_name} not found")
                
            platform = self.platforms[platform_name]
            platform.update_stats(difficulty, participation, current_ratings)
            
            # Save platform to database
            self.db.save_platform(platform)
            
            affected_users = set()
            for user_id, rating in current_ratings.items():
                if user_id not in self.users:
                    self.add_user(user_id)
                self.users[user_id].platform_ratings[platform_name] = rating
                affected_users.add(user_id)
            
            self._calculate_weights()
            
            # Only update affected users instead of all users
            for user_id in affected_users:
                self._update_user_rating(user_id)

class CourseVerifier:
    """Handles verification of course completions."""
    
    def __init__(self, db):
        self.db = db
        self.verification_methods = {
            'IIT': self._verify_iit,
            'NPTEL': self._verify_nptel,
            'Coursera': self._verify_coursera,
            'Udemy': self._verify_udemy,
            'DEFAULT': self._verify_default
        }
    
    def verify_course(self, course, certificate_data=None):
        """Verify course completion with the appropriate method based on source."""
        source = course.source
        verify_method = self.verification_methods.get(source, self.verification_methods['DEFAULT'])
        return verify_method(course, certificate_data)
    
    def _verify_iit(self, course, certificate_data):
        # Implement IIT-specific verification
        # For example, call an external API or validate a certificate number
        if not certificate_data or 'certificate_id' not in certificate_data:
            logger.warning(f"Missing certificate data for IIT course {course.course_id}")
            return False
            
        # Verification logic would go here
        return True
        
    def _verify_default(self, course, certificate_data):
        logger.info(f"Using default verification for {course.source} course")
        return bool(certificate_data)  # Basic check that some data was provided
    
class RankingSystemAPI:
    """API for integrating the ranking system with external services."""
    
    def __init__(self, ranking_system):
        self.system = ranking_system
        
    def add_platform_rating(self, user_id, platform, rating, timestamp=None):
        """Add a new rating for a user on a platform."""
        if timestamp is None:
            timestamp = datetime.now()
            
        try:
            if user_id not in self.system.users:
                self.system.add_user(user_id)
                
            if platform not in self.system.platforms:
                raise ValueError(f"Platform {platform} does not exist")
                
            # Save the rating
            user = self.system.users[user_id]
            user.platform_ratings[platform] = rating
            
            # Save historical data
            self.system.db.save_user_rating(user_id, platform, rating, timestamp)
            
            # Update user's unified rating
            self.system._update_user_rating(user_id)
            
            return {"success": True, "message": f"Added rating {rating} for {user_id} on {platform}"}
        except Exception as e:
            logger.error(f"Error adding platform rating: {e}")
            return {"success": False, "error": str(e)}
        
class RankingAnalytics:
    """Provides analytics capabilities for the ranking system."""
    
    def __init__(self, ranking_system):
        self.system = ranking_system
        
    def get_platform_statistics(self, platform_name):
        """Get statistical information about a platform."""
        if platform_name not in self.system.platforms:
            return {"error": f"Platform {platform_name} not found"}
            
        platform = self.system.platforms[platform_name]
        ratings = []
        
        for user in self.system.users.values():
            if platform_name in user.platform_ratings:
                ratings.append(user.platform_ratings[platform_name])
        
        if not ratings:
            return {
                "name": platform_name,
                "users": 0,
                "error": "No ratings available"
            }
            
        return {
            "name": platform_name,
            "users": len(ratings),
            "average": np.mean(ratings),
            "median": np.median(ratings),
            "std_dev": np.std(ratings),
            "min": min(ratings),
            "max": max(ratings),
            "quartiles": np.percentile(ratings, [25, 50, 75]).tolist(),
            "difficulty": platform.difficulty,
            "participation": platform.participation,
            "weight": self.system.final_weights.get(platform_name, 0)
        }