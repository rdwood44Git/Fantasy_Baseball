from flask import Flask, redirect, request
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import os
import requests
import xmltodict
from html import escape

import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

import requests

def get_week_scoreboard(access_token, league_key, week):
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/scoreboard;week={week}?format=json"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()

load_dotenv()

app = Flask(__name__)

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
    html = """
    <html>
    <head>
        <title>Fantasy Baseball Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 24px;
                background: #f7f7f7;
            }
            h1, h2 {
                color: #222;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                background: white;
                margin-bottom: 32px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
                font-size: 14px;
            }
            th {
                background: #222;
                color: white;
                position: sticky;
                top: 0;
            }
            tr:nth-child(even) {
                background: #f2f2f2;
            }
            .team {
                font-weight: bold;
                text-align: left;
            }
            .score {
                font-weight: bold;
            }
        </style>
    </head>
    <body>
    """

    html += "<h1>Fantasy Baseball Matchup Dashboard</h1>"

    # -----------------------------
    # Season totals by category
    # -----------------------------
    html += "<h2>Season Totals by Team</h2>"

    html += """
    <table>
        <tr>
            <th>Rank</th>
            <th>Team</th>
            <th>Weeks</th>
            <th>Category Points</th>
    """

    for stat_id in SCORING_STATS:
        html += f"<th>Total {STAT_NAMES[stat_id]}</th>"

    html += "</tr>"

    for index, team in enumerate(totals, start=1):
        html += f"""
        <tr>
            <td>{index}</td>
            <td class="team">{escape(team["team"])}</td>
            <td>{team["weeks"]}</td>
            <td>{team["category_points"]}</td>
        """

        for stat_id in SCORING_STATS:
            value = team["stats"][stat_id]

            if stat_id in ["4", "26", "27"]:
                # AVG / ERA / WHIP totals are not true weighted totals here,
                # so show average instead of misleading sum.
                display_value = f"{value / team['weeks']:.3f}"
            else:
                display_value = int(value)

            html += f"<td>{display_value}</td>"

        html += "</tr>"

    html += "</table>"

    # -----------------------------
    # Per-week averages by category
    # -----------------------------
    html += "<h2>Average Per Week by Team</h2>"

    html += """
    <table>
        <tr>
            <th>Rank</th>
            <th>Team</th>
            <th>Weeks</th>
            <th>Avg Category Points</th>
    """

    for stat_id in SCORING_STATS:
        html += f"<th>Avg {STAT_NAMES[stat_id]}</th>"

    html += "</tr>"

    for index, team in enumerate(totals, start=1):
        weeks = team["weeks"]

        html += f"""
        <tr>
            <td>{index}</td>
            <td class="team">{escape(team["team"])}</td>
            <td>{weeks}</td>
            <td>{team["category_points"] / weeks:.2f}</td>
        """

        for stat_id in SCORING_STATS:
            value = team["stats"][stat_id] / weeks

            if stat_id in ["4", "26", "27"]:
                display_value = f"{value:.3f}"
            else:
                display_value = f"{value:.1f}"

            html += f"<td>{display_value}</td>"

        html += "</tr>"

    html += "</table>"

    # -----------------------------
    # Weekly matchup detail table
    # -----------------------------
    html += "<h2>Weekly Matchup Category Stats</h2>"

    html += """
    <table>
        <tr>
            <th>Week</th>
            <th>Dates</th>
            <th>Team</th>
            <th>Score</th>
    """

    for stat_id in SCORING_STATS:
        html += f"<th>{STAT_NAMES[stat_id]}</th>"

    html += "</tr>"

    for matchup in all_matchups:
        week = matchup["week"]
        dates = f'{matchup["week_start"]} to {matchup["week_end"]}'
        score = f'{matchup["team1_points"]} - {matchup["team2_points"]}'

        for side in ["team1", "team2"]:
            team_name = matchup[f"{side}_name"]
            team_stats = matchup[f"{side}_stats"]

            html += f"""
            <tr>
                <td>{week}</td>
                <td>{dates}</td>
                <td class="team">{escape(team_name)}</td>
                <td class="score">{score}</td>
            """

            for stat_id in SCORING_STATS:
                html += f"<td>{team_stats.get(stat_id, '')}</td>"

            html += "</tr>"

    html += """
    </table>
    </body>
    </html>
    """

    return html



@app.route("/")
def login():
    print("CLIENT_ID:", CLIENT_ID)
    print("REDIRECT_URI:", REDIRECT_URI)

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



if __name__ == "__main__":
    app.run()