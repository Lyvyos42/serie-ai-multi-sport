#!/usr/bin/env python3
"""
Football Data Manager - Handles fetching football data from API-SPORTS
"""

import logging
import random
from datetime import datetime
from sports_api_client import SportsAPIClient

logger = logging.getLogger(__name__)

class FootballDataManager:
    """Manager for Football data using API-SPORTS"""
    
    def __init__(self):
        self.api_client = SportsAPIClient()
        self.leagues = {
            'SA': {'id': 135, 'name': '🇮🇹 Serie A'},
            'PL': {'id': 39, 'name': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League'}, 
            'PD': {'id': 140, 'name': '🇪🇸 La Liga'},
            'BL1': {'id': 78, 'name': '🇩🇪 Bundesliga'}
        }
    
    def get_todays_matches(self):
        """Get today's matches from API or simulation fallback"""
        if not self.api_client.api_key:
            return self._get_simulated_matches()
            
        try:
            fixtures = self.api_client.get_football_fixtures()
            if not fixtures:
                return self._get_simulated_matches()
            
            matches = []
            for fix in fixtures:
                league_id = fix.get('league', {}).get('id')
                # Filter for our supported leagues if we want, or just take all
                league_code = next((k for k, v in self.leagues.items() if v['id'] == league_id), None)
                if league_code:
                    matches.append({
                        'home': fix.get('teams', {}).get('home', {}).get('name'),
                        'away': fix.get('teams', {}).get('away', {}).get('name'),
                        'league': self.leagues[league_code]['name'],
                        'time': datetime.fromisoformat(fix.get('fixture', {}).get('date').replace('Z', '+00:00')).strftime("%H:%M")
                    })
            
            return matches if matches else self._get_simulated_matches()
        except Exception as e:
            logger.error(f"Error fetching football matches: {e}")
            return self._get_simulated_matches()

    def get_standings(self, league_code):
        """Get league standings from API or simulation fallback"""
        if league_code not in self.leagues or not self.api_client.api_key:
            return self._get_simulated_standings(league_code)
            
        try:
            league_id = self.leagues[league_code]['id']
            data = self.api_client.get_football_standings(league_id)
            
            if not data or not data[0].get('league', {}).get('standings'):
                return self._get_simulated_standings(league_code)
            
            api_standings = data[0]['league']['standings'][0]
            standings = []
            
            for rank in api_standings:
                standings.append({
                    'position': rank.get('rank'),
                    'team': rank.get('team', {}).get('name'),
                    'played': rank.get('all', {}).get('played'),
                    'won': rank.get('all', {}).get('win'),
                    'draw': rank.get('all', {}).get('draw'),
                    'lost': rank.get('all', {}).get('lose'),
                    'gf': rank.get('all', {}).get('goals', {}).get('for'),
                    'ga': rank.get('all', {}).get('goals', {}).get('against'),
                    'gd': rank.get('goalsDiff'),
                    'points': rank.get('points')
                })
            
            return {
                'league_name': self.leagues[league_code]['name'],
                'standings': standings
            }
        except Exception as e:
            logger.error(f"Error fetching football standings: {e}")
            return self._get_simulated_standings(league_code)

    def analyze_match(self, home, away):
        """Simulated analysis for now (could be enhanced with API predictions)"""
        # Mirroring the logic from DataManager in bot.py for consistency
        home_score = sum(ord(c) for c in home.lower()) % 100
        away_score = sum(ord(c) for c in away.lower()) % 100
        
        if home_score + away_score == 0:
            home_score, away_score = 50, 50
        
        home_prob = home_score / (home_score + away_score) * 100
        away_prob = away_score / (home_score + away_score) * 100
        draw_prob = max(20, 100 - home_prob - away_prob)
        
        home_prob -= draw_prob / 3
        away_prob -= draw_prob / 3
        
        prediction = "1" if home_prob > away_prob and home_prob > draw_prob else "X" if draw_prob > home_prob and draw_prob > away_prob else "2"
        confidence = max(home_prob, draw_prob, away_prob)
        
        return {
            'probabilities': {
                'home': round(home_prob, 1),
                'draw': round(draw_prob, 1),
                'away': round(away_prob, 1)
            },
            'prediction': prediction,
            'confidence': round(confidence, 1),
            'goals': {
                'home': max(0, round((home_score/100) * 3)),
                'away': max(0, round((away_score/100) * 2))
            },
            'value_bet': {
                'market': 'Match Result',
                'selection': prediction,
                'odds': round(1/({'1': home_prob, 'X': draw_prob, '2': away_prob}[prediction]/100), 2),
                'edge': round(random.uniform(3, 8), 1)
            }
        }

    def _get_simulated_matches(self):
        """Fallback simulation for matches"""
        return [
            {'league': '🇮🇹 Serie A', 'home': 'Inter', 'away': 'Milan', 'time': '20:45'},
            {'league': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League', 'home': 'Man City', 'away': 'Liverpool', 'time': '12:30'},
            {'league': '🇪🇸 La Liga', 'home': 'Barcelona', 'away': 'Real Madrid', 'time': '21:00'},
            {'league': '🇮🇹 Serie A', 'home': 'Juventus', 'away': 'Napoli', 'time': '18:00'},
            {'league': '🇩🇪 Bundesliga', 'home': 'Bayern', 'away': 'Dortmund', 'time': '17:30'}
        ]

    def _get_simulated_standings(self, league_code):
        """Fallback simulation for standings"""
        league_name = self.leagues.get(league_code, {}).get('name', 'Unknown League')
        teams = ['Team A', 'Team B', 'Team C', 'Team D', 'Team E']
        standings = []
        for i, team in enumerate(teams, 1):
            standings.append({
                'position': i, 'team': team, 'played': 20, 'won': 10, 'draw': 5, 'lost': 5,
                'gf': 30, 'ga': 20, 'gd': 10, 'points': 35
            })
        return {'league_name': league_name, 'standings': standings}
