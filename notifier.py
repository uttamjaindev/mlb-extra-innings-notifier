import os
import requests
import time
from datetime import datetime

# === Discord Webhook URL ===
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# === Helper Functions ===

def is_extra_innings(linescore):
    return linescore.get('currentInning', 0) > 9 and linescore.get('inningState', '') in ['Top', 'Bottom']

def get_mlb_games():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
    response = requests.get(url)
    games = response.json().get('dates', [])[0].get('games', [])
    return games

def notify(game):
    home = game['teams']['home']['team']['name']
    away = game['teams']['away']['team']['name']
    message = f"⚾ Extra Innings: {away} vs {home} has entered extra innings!"

    # Send to Discord Webhook
    payload = {
        "content": message
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    
    if response.status_code == 204:
        print(f"Notification sent successfully: {message}")
    else:
        print(f"Failed to send notification: {response.status_code}, {response.text}")

# === Main Agent Loop ===

def run_agent():
    notified_games = set()
    print("Starting MLB extra innings notifier...")
    while True:
        try:
            games = get_mlb_games()
            for game in games:
                game_pk = game['gamePk']
                feed_url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/feed/live"
                detailed_game = requests.get(feed_url).json()
                linescore = detailed_game.get('liveData', {}).get('linescore', {})

                if is_extra_innings(linescore) and game_pk not in notified_games:
                    notify(game)
                    notified_games.add(game_pk)

            time.sleep(60)  # Wait 1 minute before checking again
        except Exception as e:
            print("Error:", e)
            time.sleep(60)

if __name__ == "__main__":
    run_agent()
