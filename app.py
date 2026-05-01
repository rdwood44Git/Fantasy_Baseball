from flask import Flask, redirect, request, render_template, jsonify, session
from flask_cors import CORS
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import os
import requests
from html import escape


load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
CLIENT_SECRET = os.getenv("YAHOO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("YAHOO_REDIRECT_URI")

AUTHORIZATION_BASE_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"

def parse_matchups(data):
    results = []

    try:
        matchups = data["fantasy_content"]["league"][1]["scoreboard"]["0"]["matchups"]

        for key in matchups:
            if key == "count":
                continue

            matchup = matchups[key]["matchup"]

            # ✅ FIXED LINE (this was the problem)
            teams = matchup["0"]["teams"]

            team1 = teams["0"]["team"]
            team2 = teams["1"]["team"]

            # ✅ team names
            team1_name = team1[0][2]["name"]
            team2_name = team2[0][2]["name"]

            # ✅ matchup score
            team1_points = team1[1]["team_points"]["total"]
            team2_points = team2[1]["team_points"]["total"]

            results.append({
                "team1": team1_name,
                "team2": team2_name,
                "score": f"{team1_points} - {team2_points}"
            })

    except Exception as e:
        print("Parse error:", e)

    return results

STAT_NAMES = {
    "7": "R",
    "12": "HR",
    "13": "RBI",
    "16": "SB",
    "4": "AVG",
    "28": "W",
    "42": "K",
    "26": "ERA",
    "27": "WHIP",
    "89": "SV+H"
}

SCORING_STATS = ["7", "12", "13", "16", "4", "28", "42", "26", "27", "89"]


def get_team_name(team):
    return team[0][2]["name"]


def get_team_key(team):
    return team[0][0]["team_key"]


def get_team_points(team):
    return float(team[1]["team_points"]["total"])


def get_team_stats(team):
    stats = {}

    raw_stats = team[1]["team_stats"]["stats"]

    for item in raw_stats:
        stat = item["stat"]
        stat_id = stat["stat_id"]
        value = stat["value"]

        if stat_id in SCORING_STATS:
            stats[stat_id] = value

    return stats


def get_week_scoreboard(access_token, league_key, week):
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/scoreboard;week={week}?format=json"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def parse_week_matchups(data):
    results = []

    matchups = data["fantasy_content"]["league"][1]["scoreboard"]["0"]["matchups"]

    for key in matchups:
        if key == "count":
            continue

        matchup = matchups[key]["matchup"]

        # Only include completed weeks
        if matchup.get("status") != "postevent":
            continue

        week = matchup["week"]
        week_start = matchup["week_start"]
        week_end = matchup["week_end"]

        teams = matchup["0"]["teams"]

        team1 = teams["0"]["team"]
        team2 = teams["1"]["team"]

        team1_key = get_team_key(team1)
        team2_key = get_team_key(team2)

        team1_name = get_team_name(team1)
        team2_name = get_team_name(team2)

        team1_points = get_team_points(team1)
        team2_points = get_team_points(team2)

        team1_stats = get_team_stats(team1)
        team2_stats = get_team_stats(team2)

        results.append({
            "week": week,
            "week_start": week_start,
            "week_end": week_end,
            "team1_key": team1_key,
            "team2_key": team2_key,
            "team1_name": team1_name,
            "team2_name": team2_name,
            "team1_points": team1_points,
            "team2_points": team2_points,
            "team1_stats": team1_stats,
            "team2_stats": team2_stats
        })

    return results


def to_number(value):
    try:
        return float(value)
    except:
        return 0


def build_totals(all_matchups):
    totals = {}

    for matchup in all_matchups:
        for side in ["team1", "team2"]:
            team_name = matchup[f"{side}_name"]
            points = matchup[f"{side}_points"]
            stats = matchup[f"{side}_stats"]

            if team_name not in totals:
                totals[team_name] = {
                    "team": team_name,
                    "weeks": 0,
                    "category_points": 0,
                    "stats": {stat_id: 0 for stat_id in SCORING_STATS}
                }

            totals[team_name]["weeks"] += 1
            totals[team_name]["category_points"] += points

            for stat_id in SCORING_STATS:
                value = stats.get(stat_id, "0")

                # AVG, ERA, WHIP should be averaged, not summed
                if stat_id in ["4", "26", "27"]:
                    totals[team_name]["stats"][stat_id] += to_number(value)
                else:
                    totals[team_name]["stats"][stat_id] += to_number(value)

    return sorted(
        totals.values(),
        key=lambda x: x["category_points"],
        reverse=True
    )

def render_dashboard(all_matchups, totals):
    return render_template(
        "dashboard.html",
        all_matchups=all_matchups,
        totals=totals,
        SCORING_STATS=SCORING_STATS,
        STAT_NAMES=STAT_NAMES
    )



app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
CORS(app)



@app.route("/demo")
def demo():
    players = [
        {"name": "Aaron Judge", "team": "NYY", "position": "OF", "hr": 58, "rbi": 130, "sb": 10, "obp": .410},
        {"name": "Bobby Witt Jr.", "team": "KC", "position": "SS", "hr": 32, "rbi": 109, "sb": 45, "obp": .389},
        {"name": "Jose Ramirez", "team": "CLE", "position": "3B", "hr": 39, "rbi": 118, "sb": 41, "obp": .372},
    ]

    return render_template("dashboard.html", players=players)



@app.route("/")
def login():
 

    yahoo = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    authorization_url, state = yahoo.authorization_url(AUTHORIZATION_BASE_URL)
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    yahoo = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)

    token = yahoo.fetch_token(
        TOKEN_URL,
        client_secret=CLIENT_SECRET,
        authorization_response=request.url,
    )

    access_token = token["access_token"]
    session["access_token"] = access_token
    league_key = "469.l.64625"

    all_matchups = []

    # Your league has weeks 1 through 25, but this only keeps completed weeks
    for week in range(1, 26):
        try:
            data = get_week_scoreboard(access_token, league_key, week)
            week_matchups = parse_week_matchups(data)
            all_matchups.extend(week_matchups)
        except Exception as e:
            print(f"Skipping week {week}. Error: {e}")

    totals = build_totals(all_matchups)

    return render_dashboard(all_matchups, totals)


@app.route("/api/dashboard")
def api_dashboard():
    access_token = session.get("access_token")

    if not access_token:
        return jsonify({"error": "Not logged into Yahoo"}), 401

    league_key = "469.l.64625"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/standings?format=json"

    response = requests.get(url, headers=headers)

    print("Yahoo status:", response.status_code)
    print("Yahoo response:", response.text[:1000])

    return jsonify({
        "status_code": response.status_code,
        "raw_response_preview": response.text[:1000]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)