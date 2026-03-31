import os
import requests
from datetime import datetime
import pytz
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from dotenv import load_dotenv
load_dotenv() # This tells Python to secretly read your .env file!

# Ensure you set these environment variables before running
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN") # xoxb...
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN") # xapp...

app = App(token=SLACK_BOT_TOKEN)

def check_day_baseball(target_date):
    # MLB Stats API endpoint for the schedule (sportId=1 is MLB)
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={target_date}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return f"Oops! I couldn't fetch the MLB schedule. Error: {e}"
    
    if not data.get('dates'):
        return f"There are no MLB games scheduled for {target_date}."
    
    games = data['dates'][0]['games']
    eastern = pytz.timezone('US/Eastern')
    
    day_games = []
    
    for game in games:
        # The MLB API returns gameDate in UTC
        game_time_utc = datetime.strptime(game['gameDate'], "%Y-%m-%dT%H:%M:%SZ")
        game_time_utc = pytz.utc.localize(game_time_utc)
        
        # Convert to Eastern Time
        game_time_est = game_time_utc.astimezone(eastern)
        
        # Check if the game is strictly before 16:00 (4:00 PM)
        if game_time_est.hour < 16:
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            time_str = game_time_est.strftime("%I:%M %p %Z")
            day_games.append(f"⚾ {away_team} @ {home_team} at {time_str}")
            
    if day_games:
        header = f"*YES! There is day baseball on {target_date}:*\n"
        return header + "\n".join(day_games)
    else:
        return f"*Nope.* No day baseball on {target_date}. All games are at or after 4 PM EST."

@app.command("/daybaseball")
def handle_day_baseball(ack, respond, command):
    # Acknowledge the command request immediately to prevent Slack from timing out
    ack()
    
    # Check if the user provided a specific date, otherwise use today's date in Eastern Time
    text = command.get('text', '').strip()
    eastern = pytz.timezone('US/Eastern')
    
    if text:
        # We expect format YYYY-MM-DD
        target_date = text 
    else:
        target_date = datetime.now(eastern).strftime("%Y-%m-%d")
        
    result = check_day_baseball(target_date)
    
# Send the response back to the user so the whole channel can see it!
    respond(result, response_type="in_channel")

if __name__ == "__main__":
    if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
        print("Error: Missing Slack tokens. Please set SLACK_BOT_TOKEN and SLACK_APP_TOKEN.")
    else:
        print("⚾ Day Baseball Bot is running! Waiting for /daybaseball commands...")
        SocketModeHandler(app, SLACK_APP_TOKEN).start()