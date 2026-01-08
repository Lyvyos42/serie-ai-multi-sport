
import logging
from tennis_manager import TennisDataManager
from basketball_manager import BasketballDataManager

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_managers():
    print("🧪 Testing Managers...")
    
    # 1. Test Tennis Rankings
    print("\n🎾 Testing Tennis Rankings (ATP)...")
    tm = TennisDataManager()
    try:
        rankings = tm.get_rankings('ATP')
        if rankings and rankings.get('rankings'):
            print(f"✅ Success! Got {len(rankings['rankings'])} rankings.")
            print(f"Top player: {rankings['rankings'][0]}")
        else:
            print("❌ Failed: Returned empty rankings.")
    except Exception as e:
        print(f"❌ CRASH: {e}")

    # 2. Test Tennis Matches
    print("\n🎾 Testing Tennis Matches...")
    try:
        matches = tm.get_todays_matches()
        print(f"✅ Success! Got {len(matches)} matches.")
    except Exception as e:
        print(f"❌ CRASH: {e}")

    # 3. Test Basketball Standings
    print("\n🏀 Testing Basketball Standings...")
    bm = BasketballDataManager()
    try:
        standings = bm.get_standings()
        if standings:
            print(f"✅ Success! Got {len(standings)} teams.")
            print(f"Top team: {standings[0]}")
        else:
            print("❌ Failed: Returned empty standings.")
    except Exception as e:
        print(f"❌ CRASH: {e}")

    # 4. Test Basketball Matches
    print("\n🏀 Testing Basketball Matches...")
    try:
        matches = bm.get_todays_matches()
        print(f"✅ Success! Got {len(matches)} matches.")
    except Exception as e:
        print(f"❌ CRASH: {e}")

if __name__ == "__main__":
    test_managers()
