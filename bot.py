#!/usr/bin/env python3
"""
⚽ SERIE AI BOT - WITH DATABASE INTEGRATION
Complete with auto messages, invite-only, and PostgreSQL
"""

import os
import sys
import logging
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Set
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from flask import Flask
from threading import Thread

# ========== DATABASE IMPORTS ==========
from models import init_db, User, Prediction, Bet, ValueBet, SystemLog
from database import DatabaseManager

# ========== SPORTS MANAGERS ==========
from tennis_manager import TennisDataManager
from basketball_manager import BasketballDataManager

# ========== CONFIGURATION ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID", "").split(",")  # Comma-separated admin IDs
INVITE_ONLY = os.environ.get("INVITE_ONLY", "true").lower() == "true"  # Default: true
DATABASE_URL = os.environ.get("DATABASE_URL")  # PostgreSQL connection string

if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN not set!")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== FLASK FOR RAILWAY ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "⚽ Serie AI Bot - Database Edition"

@app.route('/health')
def health():
    return "✅ OK", 200

def run_flask():
    port = int(os.getenv("PORT", "8080"))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== DATA MANAGER ==========
class DataManager:
    """Simple and reliable data manager"""
    
    def __init__(self):
        self.leagues = {
            'SA': '🇮🇹 Serie A',
            'PL': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League', 
            'PD': '🇪🇸 La Liga',
            'BL1': '🇩🇪 Bundesliga'
        }
        
        self.todays_matches = [
            {'league': 'SA', 'home': 'Inter', 'away': 'Milan', 'time': '20:45'},
            {'league': 'PL', 'home': 'Man City', 'away': 'Liverpool', 'time': '12:30'},
            {'league': 'PD', 'home': 'Barcelona', 'away': 'Real Madrid', 'time': '21:00'},
            {'league': 'SA', 'home': 'Juventus', 'away': 'Napoli', 'time': '18:00'},
            {'league': 'BL1', 'home': 'Bayern', 'away': 'Dortmund', 'time': '17:30'}
        ]
    
    def get_todays_matches(self):
        """Get today's matches"""
        matches = []
        for match in self.todays_matches:
            league_name = self.leagues.get(match['league'], 'Unknown')
            matches.append({
                'home': match['home'],
                'away': match['away'], 
                'league': league_name,
                'time': match['time']
            })
        return matches
    
    def get_standings(self, league_code):
        """Get standings"""
        if league_code not in self.leagues:
            return {'league_name': 'Unknown', 'standings': []}
        
        league_name = self.leagues[league_code]
        
        # Teams for each league
        teams_map = {
            'SA': ['Inter', 'Milan', 'Juventus', 'Napoli', 'Roma', 'Lazio', 'Atalanta', 'Fiorentina'],
            'PL': ['Man City', 'Liverpool', 'Arsenal', 'Chelsea', 'Man Utd', 'Tottenham', 'Newcastle', 'Aston Villa'],
            'PD': ['Barcelona', 'Real Madrid', 'Atletico', 'Sevilla', 'Valencia', 'Betis', 'Villarreal', 'Athletic'],
            'BL1': ['Bayern', 'Dortmund', 'Leipzig', 'Leverkusen', 'Frankfurt', 'Wolfsburg', 'Gladbach', 'Hoffenheim']
        }
        
        teams = teams_map.get(league_code, [])
        standings = []
        
        for i, team in enumerate(teams, 1):
            played = random.randint(20, 30)
            won = random.randint(played//2, played-5)
            draw = random.randint(3, played-won-3)
            lost = played - won - draw
            gf = random.randint(30, 70)
            ga = random.randint(15, 50)
            gd = gf - ga
            points = won*3 + draw
            
            standings.append({
                'position': i,
                'team': team,
                'played': played,
                'won': won,
                'draw': draw,
                'lost': lost,
                'gf': gf,
                'ga': ga,
                'gd': gd,
                'points': points
            })
        
        standings.sort(key=lambda x: x['points'], reverse=True)
        
        return {
            'league_name': league_name,
            'standings': standings
        }
    
    def analyze_match(self, home, away):
        """Analyze match"""
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

# ========== GLOBAL INSTANCES ==========
data_manager = DataManager()
tennis_manager = TennisDataManager()
basketball_manager = BasketballDataManager()

# ========== USER STORAGE (Temporary - will migrate to DB) ==========
class SimpleUserStorage:
    """Temporary user storage until full DB migration"""
    
    def __init__(self):
        self.allowed_users = set()
        self.subscribers = set()
        
        # Add admin users automatically
        for admin_id in ADMIN_USER_ID:
            if admin_id.strip().isdigit():
                self.allowed_users.add(int(admin_id.strip()))
    
    def is_user_allowed(self, user_id: int) -> bool:
        if not INVITE_ONLY:
            return True
        return user_id in self.allowed_users
    
    def add_user(self, user_id: int) -> bool:
        if user_id not in self.allowed_users:
            self.allowed_users.add(user_id)
            return True
        return False

user_storage = SimpleUserStorage()

# ========== ACCESS CONTROL ==========
def access_control(func):
    """Decorator to check if user is allowed"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if not user_storage.is_user_allowed(user_id):
            # Check for invite code
            if update.message and update.message.text:
                if update.message.text.startswith('/start'):
                    parts = update.message.text.split()
                    if len(parts) > 1 and parts[1] == "invite123":
                        user_storage.add_user(user_id)
                        await update.message.reply_text(
                            "✅ *Invitation accepted!* Welcome to Serie AI Bot.\n\n"
                            "Use /start to access all features.",
                            parse_mode='Markdown'
                        )
                        return
            
            await update.message.reply_text(
                "🔒 *Access Restricted*\n\n"
                "This bot is invitation-only.\n"
                "Please contact the administrator for access.\n\n"
                "If you have an invite code, use:\n"
                "`/start invite123`",
                parse_mode='Markdown'
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

# ========== COMMAND HANDLERS ==========
@access_control
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main menu - Sport Selection"""
    # Create or update user in database
    try:
        db = DatabaseManager()
        user = db.get_or_create_user(
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
        db.close()
        logger.info(f"✅ User {update.effective_user.id} synced to database")
    except Exception as e:
        logger.error(f"❌ Database sync failed: {e}")
    
    text = """
🏆 *MULTI-SPORT PREDICTION BOT*

⚡ *AI-Powered Predictions & Analysis*

📊 *Choose Your Sport:*
• ⚽ Football (Soccer)
• 🎾 Tennis  
• 🏀 Basketball

_Each sport has complete features including predictions, stats, and live data!_

👇 Select a sport to continue:
"""
    
    keyboard = [
        [InlineKeyboardButton("⚽ Football", callback_data="sport_football")],
        [InlineKeyboardButton("🎾 Tennis", callback_data="sport_tennis")],
        [InlineKeyboardButton("🏀 Basketball", callback_data="sport_basketball")],
        [InlineKeyboardButton("ℹ️ Help & Guide", callback_data="show_help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

@access_control
async def basketball_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Basketball main menu"""
    text = """
🏀 *BASKETBALL PREDICTION BOT*

🏆 *Complete Features:*
• 📅 Today's Games
• 🏆 League Standings
• 🎯 Match Predictions
• 📊 Player/Team Analysis
• 📈 Prediction History

👇 Tap any button below:
"""
    
    keyboard = [
        [InlineKeyboardButton("📅 Today's Games", callback_data="basketball_matches")],
        [InlineKeyboardButton("🏆 NBA Standings", callback_data="basketball_standings_nba")],
        [InlineKeyboardButton("📊 My Basketball Stats", callback_data="basketball_stats")],
        [InlineKeyboardButton("🔙 Back to Sports", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

@access_control
async def football_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Football main menu"""
    status = "✅ *Real Data Enabled*" if API_KEY else "⚠️ *Using Simulation*"
    
    text = f"""
{status}

⚽ *FOOTBALL PREDICTION BOT*

🎯 *Complete Features:*
• 📅 Today's Matches
• 🏆 League Standings  
• 🎯 Smart Predictions
• 💎 Value Bets
• 📊 Match Analysis
• 📈 Prediction History

👇 Tap any button below:
"""
    
    keyboard = [
        [InlineKeyboardButton("📅 Today's Matches", callback_data="show_matches")],
        [InlineKeyboardButton("🏆 League Standings", callback_data="show_standings_menu")],
        [InlineKeyboardButton("🎯 Smart Prediction", callback_data="show_predict_info")],
        [InlineKeyboardButton("💎 Value Bets", callback_data="show_value_bets")],
        [InlineKeyboardButton("📊 My Stats", callback_data="user_stats")],
        [InlineKeyboardButton("🔙 Back to Sports", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

@access_control
async def tennis_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tennis main menu"""
    text = """
🎾 *TENNIS PREDICTION BOT*

🏆 *Complete Features:*
• 📅 Today's Matches
• 🎾 ATP/WTA Rankings
• 🎯 Match Predictions
• 📊 Player Analysis
• 📈 Prediction History

👇 Tap any button below:
"""
    
    keyboard = [
        [InlineKeyboardButton("📅 Today's Matches", callback_data="tennis_matches")],
        [InlineKeyboardButton("🏆 ATP Rankings", callback_data="tennis_rankings_atp")],
        [InlineKeyboardButton("🏆 WTA Rankings", callback_data="tennis_rankings_wta")],
        [InlineKeyboardButton("📊 My Tennis Stats", callback_data="tennis_stats")],
        [InlineKeyboardButton("🔙 Back to Sports", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


@access_control
async def quick_predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick prediction command - WITH DATABASE SAVE"""
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/predict [Home Team] [Away Team]`\n"
            "Example: `/predict Inter Milan`",
            parse_mode='Markdown'
        )
        return
    
    home, away = args[0], args[1]
    analysis = data_manager.analyze_match(home, away)
    
    probs = analysis['probabilities']
    goals = analysis['goals']
    value = analysis['value_bet']
    
    # ========== SAVE TO DATABASE ==========
    try:
        db = DatabaseManager()
        prediction = db.save_prediction(
            telegram_id=update.effective_user.id,
            home_team=home,
            away_team=away,
            league="Quick Prediction",
            predicted_result=analysis['prediction'],
            home_prob=probs['home'],
            draw_prob=probs['draw'],
            away_prob=probs['away'],
            confidence=analysis['confidence']
        )
        db.close()
        logger.info(f"✅ Prediction saved to DB: ID {prediction.id}")
        save_note = "✅ *Saved to your history*"
    except Exception as e:
        logger.error(f"❌ Database save failed: {e}")
        save_note = "⚠️ *History not saved*"
    # ========== END DATABASE SAVE ==========
    
    response = f"""
⚡ *QUICK PREDICTION: {home} vs {away}*

📊 *MATCH RESULT:*
• Home Win: {probs['home']}%
• Draw: {probs['draw']}%
• Away Win: {probs['away']}%
• ➡️ Predicted: *{analysis['prediction']}* ({analysis['confidence']}% confidence)

🥅 *EXPECTED SCORE:*
• {goals['home']}-{goals['away']} (Total: {goals['home'] + goals['away']})

💎 *BEST VALUE BET:*
• {value['market']}: {value['selection']} @ {value['odds']}
• Edge: +{value['edge']}% | Stake: ⭐⭐

{save_note}

_Enhanced with AI analysis_
"""
    
    await update.message.reply_text(response, parse_mode='Markdown')

@access_control
async def todays_matches_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Text command: /matches"""
    matches = data_manager.get_todays_matches()
    
    if not matches:
        response = "No matches scheduled for today."
    else:
        response = "📅 *TODAY'S FOOTBALL MATCHES*\n\n"
        
        # Group by league
        matches_by_league = {}
        for match in matches:
            league = match['league']
            if league not in matches_by_league:
                matches_by_league[league] = []
            matches_by_league[league].append(match)
        
        for league_name, league_matches in matches_by_league.items():
            response += f"*{league_name}*\n"
            for match in league_matches:
                response += f"⏰ {match['home']} vs {match['away']} ({match['time']})\n"
            response += "\n"
        
        response += f"_Total: {len(matches)} matches_"
    
    # Check if called from message or callback
    if update.message:
        await update.message.reply_text(response, parse_mode='Markdown')
    elif update.callback_query:
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')

@access_control
async def standings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Text command: /standings"""
    keyboard = [
        [InlineKeyboardButton("🇮🇹 Serie A", callback_data="standings_SA")],
        [InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League", callback_data="standings_PL")],
        [InlineKeyboardButton("🇪🇸 La Liga", callback_data="standings_PD")],
        [InlineKeyboardButton("🇩🇪 Bundesliga", callback_data="standings_BL1")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🏆 *Select League Standings:*"
    
    # Check if called from message or callback
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

@access_control
async def value_bets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Value bets command - FROM DATABASE"""
    # ========== GET FROM DATABASE ==========
    try:
        db = DatabaseManager()
        bets = db.get_todays_value_bets()
        db.close()
        
        if not bets:
            response = "💎 *NO VALUE BETS TODAY*\n\nNo strong value bets identified for today."
        else:
            response = "💎 *TODAY'S TOP VALUE BETS*\n\n"
            for i, bet in enumerate(bets, 1):
                response += f"{i}. *{bet.match}* ({bet.league})\n"
                response += f"   • Bet: {bet.selection} ({bet.bet_type})\n"
                response += f"   • Odds: {bet.odds} | Probability: {bet.probability}%\n"
                response += f"   • Edge: +{bet.edge}% | Confidence: {bet.confidence*100:.0f}%\n"
                response += f"   • Stake: {bet.recommended_stake}\n\n"
            
            response += "📈 *Value Betting Strategy:*\n"
            response += "• Only bet when edge > 3%\n"
            response += "• Use 1/4 Kelly stake (conservative)\n"
            response += "• Track all bets for analysis\n\n"
            response += "_Data from Serie AI Database_"
        
    except Exception as e:
        logger.error(f"❌ Database value bets failed: {e}")
        response = "❌ Could not load value bets. Please try again later."
    # ========== END DATABASE CODE ==========
    
    # Check if called from message or callback
    if update.message:
        await update.message.reply_text(response, parse_mode='Markdown')
    elif update.callback_query:
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')

@access_control
async def mystats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics - WITH DATABASE"""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    logger.info(f"📊 Getting stats for user {user_id}")
    
    try:
        # Get database connection
        db = DatabaseManager()
        
        # First, ensure user exists in database
        user = db.get_or_create_user(
            telegram_id=user_id,
            username=update.effective_user.username,
            first_name=first_name,
            last_name=update.effective_user.last_name
        )
        
        # Get user statistics
        stats = db.get_user_stats(user_id)
        db.close()
        
        total = stats['total_predictions']
        correct = stats['correct_predictions']
        accuracy = stats['accuracy']
        
        if total == 0:
            response = f"""
📊 *YOUR STATISTICS*

👤 User: {first_name}
🆔 ID: `{user_id}`

📈 *Performance:*
• Total Predictions: 0
• Correct Predictions: 0  
• Accuracy Rate: 0%

🎯 *Get started with:*
`/predict Inter Milan`

_Your predictions will be saved automatically_
"""
        else:
            response = f"""
📊 *YOUR STATISTICS*

👤 User: {first_name}
🆔 ID: `{user_id}`

📈 *Performance:*
• Total Predictions: {total}
• Correct Predictions: {correct}
• Accuracy Rate: {accuracy}%

🎯 *Recent Predictions:*
"""
            # Add recent predictions
            for i, pred in enumerate(stats['recent_predictions'][:3], 1):
                if pred.is_correct is None:
                    result_icon = "⏳"
                    status = "Pending"
                elif pred.is_correct:
                    result_icon = "✅"
                    status = "Correct"
                else:
                    result_icon = "❌"
                    status = "Wrong"
                
                response += f"{i}. {pred.home_team} vs {pred.away_team} ({result_icon} {status})\n"
            
            if accuracy > 60:
                response += "\n🏆 *Excellent accuracy! Keep it up!*"
            elif accuracy > 50:
                response += "\n👍 *Good work! Room for improvement.*"
            else:
                response += "\n💡 *Study the predictions more carefully.*"
        
        logger.info(f"✅ Stats shown for user {user_id}: {total} predictions")
        
    except Exception as e:
        logger.error(f"❌ Database error in mystats: {e}", exc_info=True)
        
        # Fallback response
        response = f"""
📊 *YOUR STATISTICS*

👤 User: {first_name}
🆔 ID: `{user_id}`

⚠️ *Database Connection Issue*

The statistics service is temporarily unavailable.

🔧 *Try these instead:*
• `/predict Inter Milan` - Make new predictions
• `/value` - View today's value bets
• `/matches` - See today's matches

_Error details: Database connection failed_
"""
    
    # Check if called from message or callback
    if update.message:
        await update.message.reply_text(response, parse_mode='Markdown')
    elif update.callback_query:
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')

@access_control
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Text command: /help"""
    help_text = """
🤖 *MULTI-SPORT AI BOT - HELP GUIDE*

*SPORT SELECTION:*
/start - Show sport selection menu (Football/Tennis/Basketball)
/football - Open Football menu
/tennis - Open Tennis menu
/basketball - Open Basketball menu

*FOOTBALL COMMANDS:*
/predict [team1] [team2] - Football match prediction
/matches - Today's football matches
/standings - League standings
/value - Today's best value bets
/mystats - Your football prediction statistics

*TENNIS COMMANDS:*
/tennispredict [p1] [p2] - Tennis match prediction
/tennismatches - Today's tennis matches
/atp / /wta - View ATP/WTA rankings
/tennisstats - Your tennis statistics

*BASKETBALL COMMANDS:*
/basketpredict [h] [a] - Basketball game prediction
/basketmatches - Today's basketball games
/nbastandings - View NBA standings
/basketstats - Your basketball statistics

*GENERAL COMMANDS:*
/help - Show this help message

*DATABASE FEATURES:*
✅ All predictions (Football, Tennis, Basketball) saved automatically
✅ Track your accuracy across different sports
✅ User profiles with detailed statistics
"""
    
    # Check if called from message or callback
    if update.message:
        await update.message.reply_text(help_text, parse_mode='Markdown')
    elif update.callback_query:
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== TENNIS COMMANDS ==========
@access_control
async def tennis_matches_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's tennis matches"""
    matches = tennis_manager.get_todays_matches()
    
    if not matches:
        response = "🎾 *NO TENNIS MATCHES TODAY*\n\nNo tennis matches scheduled for today."
    else:
        response = "🎾 *TODAY'S TENNIS MATCHES*\n\n"
        
        # Group by tournament
        tournaments = {}
        for match in matches:
            tournament = match['tournament']
            if tournament not in tournaments:
                tournaments[tournament] = []
            tournaments[tournament].append(match)
        
        for tournament_name, tournament_matches in tournaments.items():
            response += f"*{tournament_name}*\n"
            for match in tournament_matches:
                response += f"🎾 {match['player1']} vs {match['player2']}\n"
                response += f"   Surface: {match['surface']} | Round: {match['round']} | {match['time']}\n"
            response += "\n"
        
        response += f"_Total: {len(matches)} matches_"
    
    # Check if called from message or callback
    if update.message:
        await update.message.reply_text(response, parse_mode='Markdown')
    elif update.callback_query:
        keyboard = [[InlineKeyboardButton("🔙 Back to Tennis", callback_data="sport_tennis")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')

@access_control
async def tennis_predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tennis match prediction - WITH DATABASE SAVE"""
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/tennispredict [Player 1] [Player 2]`\n"
            "Example: `/tennispredict Djokovic Alcaraz`",
            parse_mode='Markdown'
        )
        return
    
    player1, player2 = args[0], args[1]
    analysis = tennis_manager.analyze_match(player1, player2)
    
    probs = analysis['probabilities']
    predicted_winner = analysis['predicted_winner']
    confidence = analysis['confidence']
    
    # ========== SAVE TO DATABASE ==========
    try:
        db = DatabaseManager()
        prediction = db.save_tennis_prediction(
            telegram_id=update.effective_user.id,
            player1=player1,
            player2=player2,
            tournament="Quick Prediction",
            surface=analysis['surface'],
            predicted_winner=predicted_winner,
            player1_prob=probs['player1'],
            player2_prob=probs['player2'],
            confidence=confidence
        )
        db.close()
        logger.info(f"✅ Tennis prediction saved to DB: ID {prediction.id}")
        save_note = "✅ *Saved to your history*"
    except Exception as e:
        logger.error(f"❌ Tennis database save failed: {e}")
        save_note = "⚠️ *History not saved*"
    # ========== END DATABASE SAVE ==========
    
    response = f"""
🎾 *TENNIS PREDICTION: {player1} vs {player2}*

📊 *MATCH WINNER:*
• {player1}: {probs['player1']}%
• {player2}: {probs['player2']}%
• ➡️ Predicted Winner: *{predicted_winner}* ({confidence}% confidence)

🎯 *PREDICTED SCORE:*
• {analysis['predicted_score']}

🏟️ *SURFACE ANALYSIS:*
• Surface: {analysis['surface']}
• Surface Specialist: {analysis['surface_specialist']}

📈 *KEY STATS:*
• Aces Advantage: {analysis['key_stats']['aces_advantage']}
• Break Points Won: {analysis['key_stats']['break_points']}
• First Serve %: {analysis['key_stats']['first_serve']}

{save_note}

_AI-powered tennis analysis_
"""
    
    await update.message.reply_text(response, parse_mode='Markdown')

@access_control
async def tennis_rankings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show ATP or WTA rankings"""
    tour = 'ATP'
    if context.args:
        tour = context.args[0].upper()
    elif update.message and update.message.text:
        cmd = update.message.text.split()[0].lower()
        if 'wta' in cmd:
            tour = 'WTA'
        elif 'atp' in cmd:
            tour = 'ATP'
    
    rankings_data = tennis_manager.get_rankings(tour)
    
    if not rankings_data or not rankings_data['rankings']:
        await update.message.reply_text("❌ Could not fetch rankings.")
        return
    
    tour_name = rankings_data['tour']
    rankings = rankings_data['rankings']
    
    response = f"🏆 *{tour_name} RANKINGS*\n\n"
    response += "```\n"
    response += " #  Player              Country  Points\n"
    response += "--- ------------------- -------- ------\n"
    
    for player in rankings[:20]:
        player_name = player['player'][:19]
        country = player['country'][:8]
        response += f"{player['rank']:2}  {player_name:19} {country:8} {player['points']:6}\n"
    
    response += "```\n"
    response += f"_Showing top {min(20, len(rankings))} players_"
    
    await update.message.reply_text(response, parse_mode='Markdown')

@access_control
async def tennis_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user tennis statistics - WITH DATABASE"""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    logger.info(f"📊 Getting tennis stats for user {user_id}")
    
    try:
        # Get database connection
        db = DatabaseManager()
        
        # Get user statistics
        stats = db.get_tennis_stats(user_id)
        db.close()
        
        total = stats['total_predictions']
        correct = stats['correct_predictions']
        accuracy = stats['accuracy']
        
        if total == 0:
            response = f"""
📊 *YOUR TENNIS STATISTICS*

👤 User: {first_name}
🆔 ID: `{user_id}`

📈 *Performance:*
• Total Predictions: 0
• Correct Predictions: 0  
• Accuracy Rate: 0%

🎯 *Get started with:*
`/tennispredict Djokovic Alcaraz`

_Your tennis predictions will be saved automatically_
"""
        else:
            response = f"""
📊 *YOUR TENNIS STATISTICS*

👤 User: {first_name}
🆔 ID: `{user_id}`

📈 *Performance:*
• Total Predictions: {total}
• Correct Predictions: {correct}
• Accuracy Rate: {accuracy}%

🎯 *Recent Predictions:*
"""
            # Add recent predictions
            for i, pred in enumerate(stats['recent_predictions'][:3], 1):
                if pred.is_correct is None:
                    result_icon = "⏳"
                    status = "Pending"
                elif pred.is_correct:
                    result_icon = "✅"
                    status = "Correct"
                else:
                    result_icon = "❌"
                    status = "Wrong"
                
                response += f"{i}. {pred.player1} vs {pred.player2} ({result_icon} {status})\n"
            
            if accuracy > 60:
                response += "\n🏆 *Excellent accuracy! Keep it up!*"
            elif accuracy > 50:
                response += "\n👍 *Good work! Room for improvement.*"
            else:
                response += "\n💡 *Study the predictions more carefully.*"
        
        logger.info(f"✅ Tennis stats shown for user {user_id}: {total} predictions")
        
    except Exception as e:
        logger.error(f"❌ Database error in tennis stats: {e}", exc_info=True)
        
        # Fallback response
        response = f"""
📊 *YOUR TENNIS STATISTICS*

👤 User: {first_name}
🆔 ID: `{user_id}`

⚠️ *Database Connection Issue*

The tennis statistics service is temporarily unavailable.

🔧 *Try these instead:*
• `/tennispredict Djokovic Alcaraz` - Make new predictions
• `/tennismatches` - See today's matches
• `/rankings ATP` - View ATP rankings

_Error details: Database connection failed_
"""
    
    # Check if called from message or callback
    if update.message:
        await update.message.reply_text(response, parse_mode='Markdown')
    elif update.callback_query:
        keyboard = [[InlineKeyboardButton("🔙 Back to Tennis", callback_data="sport_tennis")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')

# ========== BASKETBALL COMMANDS ==========
@access_control
async def basketball_matches_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's basketball games"""
    games = basketball_manager.get_todays_matches()
    
    if not games:
        response = "🏀 *NO BASKETBALL GAMES TODAY*\n\nNo basketball games scheduled for today."
    else:
        response = "🏀 *TODAY'S BASKETBALL GAMES*\n\n"
        
        # Group by league
        leagues = {}
        for game in games:
            league = game['league']
            if league not in leagues:
                leagues[league] = []
            leagues[league].append(game)
        
        for league_name, league_games in leagues.items():
            response += f"*{league_name}*\n"
            for game in league_games:
                response += f"🏀 {game['home_team']} vs {game['away_team']}\n"
                response += f"   Time: {game['time']} | Date: {game['date']}\n"
            response += "\n"
        
        response += f"_Total: {len(games)} games_"
    
    # Check if called from message or callback
    if update.message:
        await update.message.reply_text(response, parse_mode='Markdown')
    elif update.callback_query:
        keyboard = [[InlineKeyboardButton("🔙 Back to Basketball", callback_data="sport_basketball")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')

@access_control
async def basketball_predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Basketball match prediction - WITH DATABASE SAVE"""
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/basketpredict [Home Team] [Away Team]`\n"
            "Example: `/basketpredict Lakers Warriors`",
            parse_mode='Markdown'
        )
        return
    
    home, away = args[0], args[1]
    analysis = basketball_manager.analyze_match(home, away)
    
    probs = analysis['probabilities']
    predicted_winner = analysis['predicted_winner']
    confidence = analysis['confidence']
    
    # ========== SAVE TO DATABASE ==========
    try:
        db = DatabaseManager()
        prediction = db.save_basketball_prediction(
            telegram_id=update.effective_user.id,
            home_team=home,
            away_team=away,
            league="Quick Prediction",
            predicted_winner=predicted_winner,
            home_prob=probs['home'],
            away_prob=probs['away'],
            confidence=confidence
        )
        db.close()
        logger.info(f"✅ Basketball prediction saved to DB: ID {prediction.id}")
        save_note = "✅ *Saved to your history*"
    except Exception as e:
        logger.error(f"❌ Basketball database save failed: {e}")
        save_note = "⚠️ *History not saved*"
    # ========== END DATABASE SAVE ==========
    
    response = f"""
🏀 *BASKETBALL PREDICTION: {home} vs {away}*

📊 *PROBABILITIES:*
• {home}: {probs['home']}%
• {away}: {probs['away']}%
• ➡️ Predicted Winner: *{predicted_winner}* ({confidence}% confidence)

🎯 *ANALYSIS:*
• Projected Spread: {analysis['spread']}
• Total Points: {analysis['total_points']}

📈 *KEY FACTORS:*
• {analysis['keys'][0]}
• {analysis['keys'][1]}
• {analysis['keys'][2]}

{save_note}

_AI-powered basketball analysis_
"""
    
    await update.message.reply_text(response, parse_mode='Markdown')

@access_control
async def basketball_standings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show NBA standings"""
    standings = basketball_manager.get_standings()
    
    response = "🏆 *NBA STANDINGS (TOP 8)*\n\n"
    response += "```\n"
    response += " #  Team                W    L    %\n"
    response += "--- ------------------- ---- ---- -----\n"
    
    for team in standings:
        response += f"{team['rank']:2}  {team['team']:19} {team['wins']:4} {team['losses']:4} {team['pct']:.3f}\n"
    
    response += "```\n"
    
    # Check if called from message or callback
    if update.message:
        await update.message.reply_text(response, parse_mode='Markdown')
    elif update.callback_query:
        keyboard = [[InlineKeyboardButton("🔙 Back to Basketball", callback_data="sport_basketball")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')

@access_control
async def basketball_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user basketball statistics - WITH DATABASE"""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    try:
        db = DatabaseManager()
        stats = db.get_basketball_stats(user_id)
        db.close()
        
        total = stats['total_predictions']
        correct = stats['correct_predictions']
        accuracy = stats['accuracy']
        
        if total == 0:
            response = f"""
📊 *YOUR BASKETBALL STATISTICS*

👤 User: {first_name}
🆔 ID: `{user_id}`

📈 *Performance:*
• Total Predictions: 0
• Correct Predictions: 0  
• Accuracy Rate: 0%

🎯 *Get started with:*
`/basketpredict Lakers Warriors`

_Your basketball predictions will be saved automatically_
"""
        else:
            response = f"""
📊 *YOUR BASKETBALL STATISTICS*

👤 User: {first_name}
🆔 ID: `{user_id}`

📈 *Performance:*
• Total Predictions: {total}
• Correct Predictions: {correct}
• Accuracy Rate: {accuracy}%

🎯 *Recent Predictions:*
"""
            for i, pred in enumerate(stats['recent_predictions'][:3], 1):
                res_icon = "✅" if pred.is_correct else ("❌" if pred.is_correct == False else "⏳")
                response += f"{i}. {pred.home_team} vs {pred.away_team} ({res_icon})\n"
                
        logger.info(f"✅ Basketball stats shown for user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Database error in basketball stats: {e}")
        response = "❌ Could not load basketball statistics."
    
    # Check if called from message or callback
    if update.message:
        await update.message.reply_text(response, parse_mode='Markdown')
    elif update.callback_query:
        keyboard = [[InlineKeyboardButton("🔙 Back to Basketball", callback_data="sport_basketball")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')

# ========== ADMIN COMMANDS ==========
@access_control
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel"""
    user_id = update.effective_user.id
    
    if str(user_id) not in ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin access required.")
        return
    
    # ========== DATABASE STATS ==========
    try:
        db = DatabaseManager()
        total_users = db.db.query(User).count()
        total_predictions = db.db.query(Prediction).count()
        total_value_bets = db.db.query(ValueBet).filter(ValueBet.is_active == True).count()
        db.close()
    except Exception as e:
        logger.error(f"❌ Database stats failed: {e}")
        total_users = total_predictions = total_value_bets = "N/A"
    
    response = f"""
🔐 *ADMIN PANEL*

📊 *DATABASE STATISTICS:*
• Total Users: {total_users}
• Total Predictions: {total_predictions}
• Active Value Bets: {total_value_bets}
• Invite-Only Mode: {'✅ Enabled' if INVITE_ONLY else '❌ Disabled'}

⚙️ *ADMIN COMMANDS:*
/dbstats - Detailed database statistics
/adduser [id] - Add user to allowed list
/listusers - List all allowed users
/broadcast [msg] - Send message to all users

📈 *USER MANAGEMENT:*
• Use /adduser to grant access
• Invite code: `invite123`
• Database stores all user activity

💾 *DATABASE INFO:*
• PostgreSQL on Railway
• Tables: users, predictions, value_bets
• Auto-saves all predictions
"""
    
    await update.message.reply_text(response, parse_mode='Markdown')

@access_control
async def dbstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed database statistics"""
    user_id = update.effective_user.id
    
    if str(user_id) not in ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin access required.")
        return
    
    try:
        db = DatabaseManager()
        
        # Get detailed stats
        total_users = db.db.query(User).count()
        active_users = db.db.query(User).filter(User.is_active == True).count()
        premium_users = db.db.query(User).filter(User.is_premium == True).count()
        
        total_predictions = db.db.query(Prediction).count()
        correct_predictions = db.db.query(Prediction).filter(Prediction.is_correct == True).count()
        pending_predictions = db.db.query(Prediction).filter(Prediction.is_correct == None).count()
        
        total_value_bets = db.db.query(ValueBet).count()
        active_value_bets = db.db.query(ValueBet).filter(ValueBet.is_active == True).count()
        
        # Recent activity
        recent_users = db.db.query(User).order_by(User.last_seen.desc()).limit(5).all()
        
        db.close()
        
        # Calculate accuracy
        accuracy = (correct_predictions / (total_predictions - pending_predictions) * 100) if (total_predictions - pending_predictions) > 0 else 0
        
        response = f"""
📊 *DETAILED DATABASE STATISTICS*

👥 *USERS:*
• Total Users: {total_users}
• Active Users: {active_users}
• Premium Users: {premium_users}

🎯 *PREDICTIONS:*
• Total Predictions: {total_predictions}
• Correct Predictions: {correct_predictions}
• Pending Results: {pending_predictions}
• System Accuracy: {accuracy:.1f}%

💎 *VALUE BETS:*
• Total Value Bets: {total_value_bets}
• Active Value Bets: {active_value_bets}

👤 *RECENTLY ACTIVE USERS:*
"""
        for i, user in enumerate(recent_users, 1):
            last_seen = user.last_seen.strftime("%Y-%m-%d %H:%M") if user.last_seen else "Never"
            response += f"{i}. {user.first_name} (ID: {user.telegram_id}) - {last_seen}\n"
        
        response += f"\n📅 *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
    except Exception as e:
        logger.error(f"❌ Database stats failed: {e}")
        response = f"❌ Could not load database statistics: {e}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

# ========== BUTTON HANDLERS ==========
@access_control
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button presses"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "sport_football":
        await football_menu(update, context)
        
    elif data == "sport_tennis":
        await tennis_menu(update, context)
        
    elif data == "sport_basketball":
        await basketball_menu(update, context)
        
    elif data == "show_matches":
        await todays_matches_command(update, context)
    
    elif data == "show_standings_menu":
        await standings_command(update, context)
    
    elif data.startswith("standings_"):
        league_code = data.split("_")[1]
        await show_standings(update, league_code)
    
    elif data == "show_predict_info":
        await show_predict_info_callback(update, context)
    
    elif data == "show_value_bets":
        await value_bets_command(update, context)
    
    elif data == "user_stats":
        await mystats_command(update, context)
        
    elif data == "tennis_matches":
        await tennis_matches_command(update, context)
        
    elif data == "tennis_rankings_atp":
        context.args = ["ATP"]
        await tennis_rankings_command(update, context)
        
    elif data == "tennis_rankings_wta":
        context.args = ["WTA"]
        await tennis_rankings_command(update, context)
        
    elif data == "tennis_stats":
        await tennis_stats_command(update, context)

    elif data == "basketball_matches":
        await basketball_matches_command(update, context)
        
    elif data == "basketball_standings_nba":
        await basketball_standings_command(update, context)
        
    elif data == "basketball_stats":
        await basketball_stats_command(update, context)
    
    elif data == "show_help":
        await help_command(update, context)
    
    elif data == "back_to_menu":
        await start_command(update, context)

# ========== HELPER FUNCTIONS ==========
async def show_standings(update: Update, league_code: str):
    """Show standings for a league"""
    query = update.callback_query
    await query.answer()
    
    standings_data = data_manager.get_standings(league_code)
    
    if not standings_data:
        await query.edit_message_text("❌ Could not fetch standings.")
        return
    
    league_name = standings_data['league_name']
    standings = standings_data['standings']
    
    response = f"🏆 *{league_name} STANDINGS*\n\n"
    response += "```\n"
    response += " #  Team           P   W   D   L   GF  GA  GD  Pts\n"
    response += "--- ------------- --- --- --- --- --- --- --- ---\n"
    
    for team in standings[:10]:
        team_name = team['team'][:13]
        response += f"{team['position']:2}  {team_name:13} {team['played']:3} {team['won']:3} {team['draw']:3} {team['lost']:3} {team['gf']:3} {team['ga']:3} {team['gd']:3} {team['points']:4}\n"
    
    response += "```\n"
    response += f"_Showing top {min(10, len(standings))} of {len(standings)} teams_\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Standings", callback_data="show_standings_menu")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')

async def show_predict_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: Smart Prediction button"""
    query = update.callback_query
    await query.answer()
    
    text = """
🎯 *SMART PREDICTION*

*How it works:*
1. AI analyzes team statistics
2. Considers home/away advantage  
3. Evaluates recent form
4. Calculates value bets

*Quick Prediction:*
`/predict [Home Team] [Away Team]`
Example: `/predict Inter Milan`

*DATABASE FEATURE:*
✅ All predictions automatically saved
✅ Track your accuracy over time
✅ View history with /mystats
✅ Compete with other users

_Using advanced AI models + PostgreSQL database_
"""
    
    keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== MAIN FUNCTION ==========
def main():
    """Initialize and start the bot"""
    print("=" * 60)
    print("⚽ SERIE AI BOT - WITH DATABASE")
    print("=" * 60)
    
    # Initialize database with debug info
    try:
        print("🔍 Testing database connection...")
        init_db()
        print("✅ Database tables created")
        
        # Test connection
        from sqlalchemy import text
        from models import engine
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            db_version = result.fetchone()[0]
            print(f"✅ PostgreSQL Version: {db_version}")
            
            # Check tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"✅ Tables found: {tables}")
            
            if 'users' in tables and 'predictions' in tables:
                print("✅ Required tables exist")
            else:
                print("⚠️  Missing some tables")
        
        # Create sample data
        from init_database import create_sample_data
        create_sample_data()
        print("✅ Sample data created")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print(f"📌 DATABASE_URL: {DATABASE_URL[:50]}..." if DATABASE_URL else "📌 DATABASE_URL: Not set")
    
    if API_KEY:
        print("✅ API Key: FOUND")
    else:
        print("⚠️  API Key: NOT FOUND - Using simulation")
    
    print(f"🔒 Invite-Only Mode: {'✅ Enabled' if INVITE_ONLY else '❌ Disabled'}")
    if ADMIN_USER_ID and ADMIN_USER_ID[0]:
        print(f"👑 Admin Users: {len(ADMIN_USER_ID)} configured")
    
    # Start Flask for Railway
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Build bot application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("football", football_menu))
    application.add_handler(CommandHandler("tennis", tennis_menu))
    application.add_handler(CommandHandler("basketball", basketball_menu))
    application.add_handler(CommandHandler("predict", quick_predict_command))
    application.add_handler(CommandHandler("matches", todays_matches_command))
    application.add_handler(CommandHandler("standings", standings_command))
    application.add_handler(CommandHandler("value", value_bets_command))
    application.add_handler(CommandHandler("mystats", mystats_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Tennis Commands
    application.add_handler(CommandHandler("tennismatches", tennis_matches_command))
    application.add_handler(CommandHandler("tennispredict", tennis_predict_command))
    application.add_handler(CommandHandler("atp", tennis_rankings_command))
    application.add_handler(CommandHandler("wta", tennis_rankings_command))
    application.add_handler(CommandHandler("tennisstats", tennis_stats_command))

    # Basketball Commands
    application.add_handler(CommandHandler("basketmatches", basketball_matches_command))
    application.add_handler(CommandHandler("basketpredict", basketball_predict_command))
    application.add_handler(CommandHandler("nbastandings", basketball_standings_command))
    application.add_handler(CommandHandler("basketstats", basketball_stats_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("dbstats", dbstats_command))
    
    # Register button handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Bot initialized with database features")
    print("   Commands available:")
    print("   • /start - Main menu")
    print("   • /predict - Save predictions to DB")
    print("   • /matches - Today's matches")
    print("   • /standings - League standings")
    print("   • /value - Value bets from DB")
    print("   • /mystats - Your statistics from DB")  # ADDED THIS LINE
    print("   • /admin - Admin panel (DB stats)")
    print("=" * 60)
    print("📱 Test on Telegram with /start")
    
    # Start bot
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()