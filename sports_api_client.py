#!/usr/bin/env python3
"""
Sports API Client - Unified client for API-SPORTS
Handles Football, Tennis, and Basketball APIs
"""

import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class SportsAPIClient:
    """Unified API client for all sports from API-SPORTS"""
    
    def __init__(self):
        self.api_key = os.environ.get("SPORTS_API_KEY", "")
        
        # API endpoints
        self.football_url = "https://v3.football.api-sports.io"
        self.tennis_url = "https://v1.tennis.api-sports.io"
        self.basketball_url = "https://v1.basketball.api-sports.io"
        
        # Headers for all requests
        self.headers = {
            "x-rapidapi-host": "",
            "x-rapidapi-key": self.api_key
        }
        
        if not self.api_key:
            logger.warning("⚠️ SPORTS_API_KEY not set - APIs will use simulation mode")
    
    def _make_request(self, url, endpoint, params=None):
        """Make API request with error handling"""
        try:
            full_url = f"{url}/{endpoint}"
            response = requests.get(full_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('errors'):
                logger.error(f"API Error: {data['errors']}")
                return None
            
            return data.get('response', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            return None
    
    # ========== FOOTBALL API METHODS ==========
    
    def get_football_fixtures(self, date=None):
        """Get football fixtures for a date"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        return self._make_request(self.football_url, "fixtures", {"date": date})

    def get_football_standings(self, league_id, season=None):
        """Get football standings"""
        if not season:
            season = datetime.now().year
        return self._make_request(self.football_url, "standings", {
            "league": league_id,
            "season": season
        })

    def get_football_predictions(self, fixture_id):
        """Get predictions for a fixture"""
        return self._make_request(self.football_url, "predictions", {"fixture": fixture_id})

    # ========== TENNIS API METHODS ==========
    
    def get_tennis_matches_today(self):
        """Get today's tennis matches"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self._make_request(self.tennis_url, "games", {"date": today})
    
    def get_tennis_player_search(self, name):
        """Search for tennis player by name"""
        return self._make_request(self.tennis_url, "players", {"search": name})
    
    def get_tennis_h2h(self, player1_id, player2_id):
        """Get head-to-head stats between two players"""
        return self._make_request(self.tennis_url, "h2h", {
            "player1": player1_id,
            "player2": player2_id
        })
    
    def get_tennis_rankings(self, tour='atp'):
        """Get ATP or WTA rankings (tour: 'atp' or 'wta')"""
        return self._make_request(self.tennis_url, "rankings", {"tour": tour})
    
    def get_tennis_player_stats(self, player_id, season=None):
        """Get player statistics for a season"""
        params = {"player": player_id}
        if season:
            params["season"] = season
        return self._make_request(self.tennis_url, "statistics/players", params)
    
    # ========== BASKETBALL API METHODS (Future) ==========
    
    def get_basketball_games_today(self):
        """Get today's basketball games"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self._make_request(self.basketball_url, "games", {"date": today})
    
    def get_basketball_standings(self, league_id, season):
        """Get basketball standings"""
        return self._make_request(self.basketball_url, "standings", {
            "league": league_id,
            "season": season
        })
