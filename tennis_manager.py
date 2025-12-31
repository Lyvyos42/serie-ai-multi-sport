#!/usr/bin/env python3
"""
Tennis Data Manager - Handles tennis matches, predictions, and statistics
"""

import random
import logging
from datetime import datetime
from sports_api_client import SportsAPIClient

logger = logging.getLogger(__name__)

class TennisDataManager:
    """Manages tennis data and predictions"""
    
    def __init__(self):
        self.api = SportsAPIClient()
        
        # Sample tennis tournaments
        self.tournaments = {
            'GS': '🏆 Grand Slam',
            'ATP1000': '🎾 ATP Masters 1000',
            'ATP500': '🎾 ATP 500',
            'ATP250': '🎾 ATP 250',
            'WTA1000': '🎾 WTA 1000',
            'WTA500': '🎾 WTA 500',
            'WTA250': '🎾 WTA 250'
        }
        
        # Surface types
        self.surfaces = ['Hard', 'Clay', 'Grass', 'Carpet']
    
    def get_todays_matches(self):
        """Get today's tennis matches"""
        # Try API first
        if self.api.api_key:
            matches_data = self.api.get_tennis_matches_today()
            if matches_data:
                return self._format_api_matches(matches_data)
        
        # Fallback to simulation
        return self._get_simulated_matches()
    
    def _format_api_matches(self, api_data):
        """Format API data into standard match format"""
        matches = []
        for match in api_data[:10]:  # Limit to 10 matches
            try:
                matches.append({
                    'player1': match.get('player1', {}).get('name', 'Player 1'),
                    'player2': match.get('player2', {}).get('name', 'Player 2'),
                    'tournament': match.get('competition', {}).get('name', 'Tournament'),
                    'surface': match.get('surface', 'Hard'),
                    'time': match.get('date', 'TBD'),
                    'round': match.get('round', 'R32')
                })
            except Exception as e:
                logger.error(f"Error formatting match: {e}")
                continue
        return matches
    
    def _get_simulated_matches(self):
        """Generate simulated tennis matches"""
        players = [
            'Novak Djokovic', 'Carlos Alcaraz', 'Daniil Medvedev', 'Jannik Sinner',
            'Alexander Zverev', 'Andrey Rublev', 'Stefanos Tsitsipas', 'Holger Rune',
            'Taylor Fritz', 'Casper Ruud', 'Grigor Dimitrov', 'Tommy Paul',
            'Iga Swiatek', 'Aryna Sabalenka', 'Coco Gauff', 'Elena Rybakina',
            'Jessica Pegula', 'Ons Jabeur', 'Qinwen Zheng', 'Karolina Muchova'
        ]
        
        tournaments_list = [
            'Australian Open', 'Miami Open', 'Indian Wells', 'Madrid Open',
            'Rome Masters', 'Dubai Championships', 'ATP Finals'
        ]
        
        matches = []
        num_matches = random.randint(4, 8)
        
        used_players = set()
        for _ in range(num_matches):
            # Select two unique players
            available = [p for p in players if p not in used_players]
            if len(available) < 2:
                used_players.clear()
                available = players
            
            player1, player2 = random.sample(available, 2)
            used_players.add(player1)
            used_players.add(player2)
            
            matches.append({
                'player1': player1,
                'player2': player2,
                'tournament': random.choice(tournaments_list),
                'surface': random.choice(self.surfaces),
                'time': f"{random.randint(10, 20)}:{random.choice(['00', '30'])}",
                'round': random.choice(['R64', 'R32', 'R16', 'QF', 'SF', 'F'])
            })
        
        return matches
    
    def analyze_match(self, player1, player2):
        """Analyze a tennis match between two players"""
        # Calculate probabilities based on player names (simulation)
        p1_score = sum(ord(c) for c in player1.lower()) % 100
        p2_score = sum(ord(c) for c in player2.lower()) % 100
        
        if p1_score + p2_score == 0:
            p1_score, p2_score = 50, 50
        
        total = p1_score + p2_score
        player1_prob = (p1_score / total) * 100
        player2_prob = (p2_score / total) * 100
        
        # Add some randomness for realism
        adjustment = random.uniform(-5, 5)
        player1_prob += adjustment
        player2_prob -= adjustment
        
        # Normalize to 100%
        total_prob = player1_prob + player2_prob
        player1_prob = (player1_prob / total_prob) * 100
        player2_prob = (player2_prob / total_prob) * 100
        
        # Determine winner
        predicted_winner = player1 if player1_prob > player2_prob else player2
        confidence = max(player1_prob, player2_prob)
        
        # Predicted score (best of 3 sets)
        if player1_prob > player2_prob:
            sets = random.choice(['2-0', '2-1'])
        else:
            sets = random.choice(['0-2', '1-2'])
        
        # Surface advantage
        surface = random.choice(self.surfaces)
        surface_specialist = random.choice([player1, player2])
        
        return {
            'player1': player1,
            'player2': player2,
            'probabilities': {
                'player1': round(player1_prob, 1),
                'player2': round(player2_prob, 1)
            },
            'predicted_winner': predicted_winner,
            'confidence': round(confidence, 1),
            'predicted_score': sets,
            'surface': surface,
            'surface_specialist': surface_specialist,
            'key_stats': {
                'aces_advantage': random.choice([player1, player2]),
                'break_points': f"{random.randint(3, 8)}/{random.randint(10, 15)}",
                'first_serve': f"{random.randint(60, 75)}%"
            }
        }
    
    def get_rankings(self, tour='atp'):
        """Get ATP or WTA rankings"""
        # Try API first
        if self.api.api_key:
            rankings_data = self.api.get_tennis_rankings(tour.lower())
            if rankings_data:
                return self._format_api_rankings(rankings_data, tour)
        
        # Fallback to simulation
        return self._get_simulated_rankings(tour)
    
    def _format_api_rankings(self, api_data, tour):
        """Format API rankings data"""
        rankings = []
        for rank in api_data[:20]:  # Top 20
            try:
                rankings.append({
                    'rank': rank.get('rank', 0),
                    'player': rank.get('player', {}).get('name', 'Unknown'),
                    'points': rank.get('points', 0),
                    'country': rank.get('player', {}).get('country', 'N/A')
                })
            except Exception as e:
                logger.error(f"Error formatting ranking: {e}")
                continue
        
        return {
            'tour': tour.upper(),
            'rankings': rankings
        }
    
    def _get_simulated_rankings(self, tour):
        """Generate simulated rankings"""
        if tour.lower() == 'atp':
            players = [
                ('Novak Djokovic', 'SRB', 9500),
                ('Carlos Alcaraz', 'ESP', 8800),
                ('Daniil Medvedev', 'RUS', 7600),
                ('Jannik Sinner', 'ITA', 7200),
                ('Alexander Zverev', 'GER', 6500),
                ('Andrey Rublev', 'RUS', 5800),
                ('Stefanos Tsitsipas', 'GRE', 5400),
                ('Holger Rune', 'DEN', 4900),
                ('Taylor Fritz', 'USA', 4600),
                ('Casper Ruud', 'NOR', 4300),
                ('Grigor Dimitrov', 'BUL', 3900),
                ('Tommy Paul', 'USA', 3700),
                ('Hubert Hurkacz', 'POL', 3500),
                ('Alex de Minaur', 'AUS', 3300),
                ('Karen Khachanov', 'RUS', 3100),
                ('Frances Tiafoe', 'USA', 2900),
                ('Cameron Norrie', 'GBR', 2700),
                ('Felix Auger-Aliassime', 'CAN', 2500),
                ('Lorenzo Musetti', 'ITA', 2300),
                ('Sebastian Baez', 'ARG', 2100)
            ]
        else:  # WTA
            players = [
                ('Iga Swiatek', 'POL', 9800),
                ('Aryna Sabalenka', 'BLR', 8600),
                ('Coco Gauff', 'USA', 7800),
                ('Elena Rybakina', 'KAZ', 7100),
                ('Jessica Pegula', 'USA', 6400),
                ('Ons Jabeur', 'TUN', 5900),
                ('Qinwen Zheng', 'CHN', 5400),
                ('Karolina Muchova', 'CZE', 4900),
                ('Marketa Vondrousova', 'CZE', 4500),
                ('Maria Sakkari', 'GRE', 4200),
                ('Barbora Krejcikova', 'CZE', 3900),
                ('Beatriz Haddad Maia', 'BRA', 3600),
                ('Jelena Ostapenko', 'LAT', 3400),
                ('Daria Kasatkina', 'RUS', 3200),
                ('Veronika Kudermetova', 'RUS', 3000),
                ('Liudmila Samsonova', 'RUS', 2800),
                ('Madison Keys', 'USA', 2600),
                ('Petra Kvitova', 'CZE', 2400),
                ('Caroline Garcia', 'FRA', 2200),
                ('Victoria Azarenka', 'BLR', 2000)
            ]
        
        rankings = [
            {
                'rank': i + 1,
                'player': name,
                'country': country,
                'points': points
            }
            for i, (name, country, points) in enumerate(players)
        ]
        
        return {
            'tour': tour.upper(),
            'rankings': rankings
        }
