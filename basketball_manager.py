#!/usr/bin/env python3
"""
Basketball Data Manager - Handles basketball games, predictions, and standings
"""

import random
import logging
from datetime import datetime
from sports_api_client import SportsAPIClient

logger = logging.getLogger(__name__)

class BasketballDataManager:
    """Manages basketball data and predictions"""
    
    def __init__(self):
        self.api = SportsAPIClient()
        
        self.leagues = {
            '12': '🏀 NBA',
            '120': '🏀 Euroleague',
            '2': '🏀 Liga ACB',
            '13': '🏀 NCAA'
        }
    
    def get_todays_matches(self):
        """Get today's basketball matches"""
        # Try API first
        if self.api.api_key:
            games_data = self.api.get_basketball_games_today()
            if games_data:
                return self._format_api_games(games_data)
        
        # Fallback to simulation
        return self._get_simulated_games()
    
    def _format_api_games(self, api_data):
        """Format API data into standard game format"""
        games = []
        for game in api_data[:15]:
            try:
                games.append({
                    'home_team': game.get('teams', {}).get('home', {}).get('name', 'Home'),
                    'away_team': game.get('teams', {}).get('away', {}).get('name', 'Away'),
                    'league': game.get('league', {}).get('name', 'League'),
                    'time': game.get('time', 'TBD'),
                    'date': game.get('date', 'Today')
                })
            except Exception as e:
                logger.error(f"Error formatting basketball game: {e}")
                continue
        return games
    
    def _get_simulated_games(self):
        """Generate simulated basketball games"""
        nba_teams = [
            'LA Lakers', 'GS Warriors', 'Boston Celtics', 'Denver Nuggets',
            'Miami Heat', 'Milwaukee Bucks', 'Phoenix Suns', 'Dallas Mavericks',
            'NY Knicks', 'Philadelphia 76ers', 'LA Clippers', 'Chicago Bulls'
        ]
        
        games = []
        num_games = random.randint(5, 10)
        
        used_teams = set()
        for _ in range(num_games):
            available = [t for t in nba_teams if t not in used_teams]
            if len(available) < 2:
                used_teams.clear()
                available = nba_teams
            
            home, away = random.sample(available, 2)
            used_teams.add(home)
            used_teams.add(away)
            
            games.append({
                'home_team': home,
                'away_team': away,
                'league': 'NBA',
                'time': f"{random.randint(7, 10)}:30 PM",
                'date': 'Tonight'
            })
        
        return games
    
    def analyze_match(self, home_team, away_team):
        """Analyze a basketball match between two teams"""
        # Calculate probabilities based on team names (simulation)
        h_score = sum(ord(c) for c in home_team.lower()) % 100
        a_score = sum(ord(c) for c in away_team.lower()) % 100
        
        # Home court advantage
        h_score += 10
        
        total = h_score + a_score
        home_prob = (h_score / total) * 100
        away_prob = (a_score / total) * 100
        
        # Determination
        predicted_winner = home_team if home_prob > away_prob else away_team
        confidence = max(home_prob, away_prob)
        
        # Point spread simulation
        spread = random.randint(2, 12)
        total_points = random.randint(205, 235)
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'probabilities': {
                'home': round(home_prob, 1),
                'away': round(away_prob, 1)
            },
            'predicted_winner': predicted_winner,
            'confidence': round(confidence, 1),
            'spread': f"{'+' if predicted_winner == away_team else '-'}{spread}",
            'total_points': total_points,
            'keys': [
                "Rebound Control",
                "3-Point Percentage",
                "Turnover Margin"
            ]
        }
    
    def get_standings(self, league_id='12'):
        """Get basketball standings (default NBA: 12)"""
        # Simulation for now
        standings = []
        teams = [
            ('Boston Celtics', 45, 12), ('Milwaukee Bucks', 42, 15),
            ('NY Knicks', 38, 20), ('Cleveland Cavaliers', 37, 21),
            ('Philadelphia 76ers', 35, 23), ('Indiana Pacers', 34, 25),
            ('Miami Heat', 33, 26), ('Orlando Magic', 32, 27)
        ]
        
        for i, (name, w, l) in enumerate(teams):
            standings.append({
                'rank': i + 1,
                'team': name,
                'wins': w,
                'losses': l,
                'pct': round(w / (w+l), 3)
            })
            
        return standings
