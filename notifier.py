import os
import requests
import time
from datetime import datetime

# === Discord Webhook URL ===
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
# Uncomment for testing:
# DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/your_webhook_url_here"

# === Helper Functions ===

def is_extra_innings(linescore):
    return linescore.get('currentInning', 0) > 9 and linescore.get('inningState', '') in ['Top', 'Bottom']

def get_mlb_games():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
    response = requests.get(url)

    try:
        data = response.json()
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return []

    dates = data.get('dates', [])
    if not dates:
        print("[INFO] No MLB games found for today.")
        return []

    return dates[0].get('games', [])

def notify(game):
    home = game['teams']['home']['team']['name']
    away = game['teams']['away']['team']['name']
    message = f"⚾ Extra Innings: {away} vs {home} has entered extra innings!"

    # Send to Discord Webhook
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print(f"[SUCCESS] Notification sent: {message}")
        else:
            print(f"[ERROR] Discord response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERROR] Failed to send Discord notification: {e}")

# === Main Agent Loop ===

def run_agent():
    notified_games = set()
    print("[START] MLB extra innings notifier is running...")
    while True:
        try:
            games = get_mlb_games()
            if not games:
                print("[INFO] No games to process.")
            for game in games:
                game_pk = game.get('gamePk')
                if not game_pk:
                    continue

                teams = game.get('teams', {})
                home = teams.get('home', {}).get('team', {}).get('name', 'Unknown')
                away = teams.get('away', {}).get('team', {}).get('name', 'Unknown')
                print(f"[CHECK] {away} vs {home} (gamePk: {game_pk})")

                feed_url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/feed/live"
                response = requests.get(feed_url)
                detailed_game = response.json()
                linescore = detailed_game.get('liveData', {}).get('linescore', {})

                print(f"    Inning: {linescore.get('currentInning')} | State: {linescore.get('inningState')}")

                if is_extra_innings(linescore) and game_pk not in notified_games:
                    print(f"    [INFO] Game entered extra innings!")
                    notify(game)
                    notified_games.add(game_pk)
                else:
                    print(f"    [INFO] Not in extra innings yet or already notified.")

            time.sleep(60)  # Wait 1 minute before checking again
        except Exception as e:
            print(f"[ERROR] Unexpected failure in loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("[ERROR] DISCORD_WEBHOOK_URL is not set.")
    else:
        run_agent()
