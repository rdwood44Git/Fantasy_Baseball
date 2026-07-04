from flask import Flask, redirect, request, render_template, jsonify, session, send_from_directory
from flask_cors import CORS
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import os
import requests
from html import escape
from functools import wraps
from database import get_db_connection

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV", "production") != "development"
)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://localhost:8080",
                "https://fantasy-baseball-2.onrender.com"
            ],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    },
    supports_credentials=True
)

CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
CLIENT_SECRET = os.getenv("YAHOO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("YAHOO_REDIRECT_URI")

AUTHORIZATION_BASE_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"


# ============================================================
# Simple app password protection using a Flask session login
#
# In Render, add these Environment Variables:
# APP_USERNAME=your_username
# APP_PASSWORD=your_password
# APP_PASSWORD_ENABLED=true
# FLASK_SECRET_KEY=make-this-a-long-random-value
#
# For local testing only, you can set:
# APP_PASSWORD_ENABLED=false
# ============================================================
APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "change-me")
APP_PASSWORD_ENABLED = os.getenv("APP_PASSWORD_ENABLED", "true").lower() == "true"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
FRONTEND_ASSETS = os.path.join(FRONTEND_DIST, "assets")

PUBLIC_PATHS = {"/login", "/health"}


def is_app_logged_in():
    return bool(session.get("app_logged_in"))


@app.before_request
def require_app_login():
    if not APP_PASSWORD_ENABLED:
        return None

    if request.method == "OPTIONS":
        return None

    if request.path in PUBLIC_PATHS:
        return None

    if request.path.startswith("/assets/") or request.path.startswith("/static/"):
        return None

    # Keep Yahoo callback reachable after OAuth redirects back to the app.
    if request.path == "/callback":
        return None

    if is_app_logged_in():
        return None

    if request.path.startswith("/api/"):
        return jsonify({"error": "App login required"}), 401

    next_url = request.full_path if request.query_string else request.path
    return redirect(f"/login?next={next_url}")


@app.route("/login", methods=["GET", "POST"])
def app_login():
    error = None
    next_url = request.args.get("next") or request.form.get("next") or "/"

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == APP_USERNAME and password == APP_PASSWORD:
            session["app_logged_in"] = True
            return redirect(next_url or "/")

        error = "Invalid username or password."

    return f"""
    <!doctype html>
    <html lang=\"en\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Fantasy Baseball Login</title>
        <style>
          * {{ box-sizing: border-box; }}
          body {{
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #061b35 0%, #0d2f59 55%, #15477d 100%);
            font-family: Inter, Arial, Helvetica, sans-serif;
            color: #102033;
            padding: 24px;
          }}
          .login-card {{
            width: 100%;
            max-width: 430px;
            background: #ffffff;
            border-radius: 18px;
            box-shadow: 0 18px 55px rgba(0,0,0,0.35);
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.25);
          }}
          .login-header {{
            padding: 28px 28px 22px;
            background: #08264a;
            color: white;
            text-align: center;
            border-bottom: 4px solid #2a9cab;
          }}
          .logo {{
            width: 64px;
            height: 64px;
            margin: 0 auto 14px;
            border-radius: 50%;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
          }}
          h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.7px;
          }}
          .subtitle {{
            margin-top: 8px;
            color: #c7d7ea;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 1.2px;
            text-transform: uppercase;
          }}
          form {{ padding: 26px 28px 30px; }}
          label {{
            display: block;
            margin-bottom: 8px;
            font-size: 13px;
            font-weight: 900;
            color: #38506a;
            text-transform: uppercase;
            letter-spacing: 0.4px;
          }}
          input {{
            width: 100%;
            height: 44px;
            margin-bottom: 16px;
            padding: 0 12px;
            border: 1px solid #d6dee8;
            border-radius: 8px;
            font-size: 15px;
            outline: none;
          }}
          input:focus {{
            border-color: #2a9cab;
            box-shadow: 0 0 0 3px rgba(42,156,171,0.16);
          }}
          .error {{
            margin-bottom: 16px;
            padding: 12px;
            border-radius: 8px;
            background: #fdecec;
            color: #c62828;
            font-weight: 800;
            font-size: 13px;
          }}
          button {{
            width: 100%;
            height: 46px;
            border: 0;
            border-radius: 8px;
            background: #0b5cab;
            color: white;
            font-weight: 900;
            font-size: 15px;
            cursor: pointer;
          }}
          button:hover {{ background: #084b8d; }}
        </style>
      </head>
      <body>
        <div class=\"login-card\">
          <div class=\"login-header\">
            <div class=\"logo\">⚾</div>
            <h1>Millie's Fantasy Baseball</h1>
            <div class=\"subtitle\">Private Dashboard</div>
          </div>
          <form method=\"post\">
            <input type=\"hidden\" name=\"next\" value=\"{next_url}\" />
            {f'<div class=\"error\">{error}</div>' if error else ''}
            <label for=\"username\">Username</label>
            <input id=\"username\" name=\"username\" autocomplete=\"username\" required autofocus />
            <label for=\"password\">Password</label>
            <input id=\"password\" name=\"password\" type=\"password\" autocomplete=\"current-password\" required />
            <button type=\"submit\">Sign In</button>
          </form>
        </div>
      </body>
    </html>
    """


@app.route("/logout")
def app_logout():
    session.pop("app_logged_in", None)
    return redirect("/login")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})

STAT_NAMES = {
    "7": "R",
    "12": "HR",
    "13": "RBI",
    "16": "SB",
    "4": "OBP",
    "28": "W",
    "42": "K",
    "26": "ERA",
    "27": "WHIP",
    "89": "SV+H"
}

SCORING_STATS = ["7", "12", "13", "16", "4", "28", "42", "26", "27", "89"]

categories = {
    "7": "Runs",
    "12": "Home Runs",
    "13": "RBI",
    "16": "Stolen Bases",
    "4": "OBP",
    "28": "Wins",
    "89": "Saves + Holds",
    "42": "Strikeouts",
    "26": "ERA",
    "27": "WHIP",
}

lower_is_better = {"26", "27"}


def classify_player_from_positions(positions):
    pitcher_positions = {"P", "SP", "RP"}
    ignored_positions = {"IL", "NA", "BN"}

    clean_positions = {
        str(p).strip().upper()
        for p in positions
        if p and str(p).strip()
    }

    real_positions = clean_positions - ignored_positions

    if not real_positions:
        return None

    if real_positions & pitcher_positions:
        return "pitcher"

    return "hitter"


def get_team_name(team):
    return team[0][2]["name"]


def get_team_key(team):
    return team[0][0]["team_key"]


def get_team_points(team):
    return float(team[1]["team_points"]["total"])


def to_number(value):
    try:
        return float(value)
    except:
        return 0


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


def parse_matchups(data):
    results = []

    try:
        matchups = data["fantasy_content"]["league"][1]["scoreboard"]["0"]["matchups"]

        for key in matchups:
            if key == "count":
                continue

            matchup = matchups[key]["matchup"]

            teams = matchup["0"]["teams"]

            team1 = teams["0"]["team"]
            team2 = teams["1"]["team"]

            team1_name = team1[0][2]["name"]
            team2_name = team2[0][2]["name"]

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
                totals[team_name]["stats"][stat_id] += to_number(value)

    return sorted(
        totals.values(),
        key=lambda x: x["category_points"],
        reverse=True
    )


def build_category_tables(team_totals):
    category_tables = {}

    for cat, label in categories.items():
        reverse = cat not in lower_is_better

        ranked = sorted(
            team_totals,
            key=lambda team: team["stats"].get(cat, 0),
            reverse=reverse
        )

        category_tables[cat] = {
            "label": label,
            "rows": [
                {
                    "rank": index + 1,
                    "team": team["team"],
                    "value": team["stats"].get(cat, 0)
                }
                for index, team in enumerate(ranked)
            ]
        }

    return category_tables


@app.route("/api/admin/update-yahoo-positions")
def update_yahoo_positions():
    access_token = session.get("access_token")

    if not access_token:
        return jsonify({"error": "Not logged into Yahoo"}), 401

    league_key = "469.l.64625"
    game_key = league_key.split(".")[0]

    conn = get_db_connection()

    existing_cols = [
        row["name"]
        for row in conn.execute("PRAGMA table_info(players)").fetchall()
    ]

    if "yahoo_position" not in existing_cols:
        conn.execute("ALTER TABLE players ADD COLUMN yahoo_position TEXT")

    if "yahoo_positions" not in existing_cols:
        conn.execute("ALTER TABLE players ADD COLUMN yahoo_positions TEXT")

    if "player_type" not in existing_cols:
        conn.execute("ALTER TABLE players ADD COLUMN player_type TEXT")

    players = conn.execute("""
        SELECT yahoo_player_id, yahoo_name
        FROM players
        WHERE yahoo_player_id IS NOT NULL
    """).fetchall()

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    updated = 0
    missing = []
    batch_size = 25

    for i in range(0, len(players), batch_size):
        batch = players[i:i + batch_size]

        player_keys = []

        for p in batch:
            yahoo_player_id = str(p["yahoo_player_id"])

            if ".p." not in yahoo_player_id:
                player_key = f"{game_key}.p.{yahoo_player_id}"
            else:
                player_key = yahoo_player_id

            player_keys.append(player_key)

        url = (
            "https://fantasysports.yahooapis.com/fantasy/v2/"
            f"players;player_keys={','.join(player_keys)}?format=json"
        )

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        yahoo_players = data["fantasy_content"]["players"]

        for key, value in yahoo_players.items():
            if key == "count":
                continue

            player = value["player"]

            yahoo_player_id = None
            yahoo_name = None
            display_position = None
            eligible_positions = []

            for item in player[0]:
                if not isinstance(item, dict):
                    continue

                if "player_id" in item:
                    yahoo_player_id = str(item["player_id"])

                if "name" in item:
                    yahoo_name = item["name"].get("full")

                if "display_position" in item:
                    display_position = item["display_position"]

                if "eligible_positions" in item:
                    for pos_item in item["eligible_positions"]:
                        if "position" in pos_item:
                            eligible_positions.append(pos_item["position"])

            if not yahoo_player_id:
                missing.append(yahoo_name or "Unknown")
                continue

            yahoo_positions = ",".join(eligible_positions)
            player_type = classify_player_from_positions(eligible_positions)

            cur = conn.execute("""
                UPDATE players
                SET
                    yahoo_position = ?,
                    yahoo_positions = ?,
                    player_type = ?
                WHERE yahoo_player_id = ?
                   OR yahoo_player_id = ?
            """, (
                display_position,
                yahoo_positions,
                player_type,
                yahoo_player_id,
                f"{game_key}.p.{yahoo_player_id}"
            ))

            updated += cur.rowcount

    conn.commit()
    conn.close()

    return jsonify({
        "updated": updated,
        "missing": missing
    })

def get_current_yahoo_week():
    try:
        from yahoo_oauth import OAuth2

        oauth = OAuth2(None, None, from_file="oauth2.json")

        if not oauth.token_is_valid():
            oauth.refresh_access_token()

        access_token = oauth.token["access_token"]
        league_key = "469.l.64625"

        url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/settings?format=json"

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15
        )
        response.raise_for_status()

        data = response.json()
        settings = data["fantasy_content"]["league"][1]["settings"][0]

        return max(int(settings.get("current_week", 1)), 1)

    except Exception as e:
        print("Could not determine Yahoo current week:", e)
        return 13



@app.route("/api/player-category-summary")
def player_category_summary():
    conn = get_db_connection()

    weeks_elapsed = get_current_yahoo_week()

    hitter_weekly_ab = 26
    starter_weekly_ip = 6.5
    reliever_weekly_ip = 2.5

    hitters = conn.execute("""
        SELECT
            p.yahoo_player_id,
            p.yahoo_name,
            p.yahoo_team,
            p.fantasy_team_name,
            p.is_available,
            p.is_on_my_team,
            p.yahoo_hitter_season_rank,
            p.yahoo_hitter_30_day_rank,
            p.yahoo_position,
            p.yahoo_positions,
            p.player_type,
            p.injury_status,

            ys.hr AS current_hr,
            ys.r AS current_r,
            ys.rbi AS current_rbi,
            ys.sb AS current_sb,
            ys.obp AS active_obp,
            ys.pa_basis AS PA_basis,

            fg.g AS projected_games,
            fg.pa AS projected_pa,
            fg.hr AS projected_hr,
            fg.r AS projected_r,
            fg.rbi AS projected_rbi,
            fg.sb AS projected_sb,
            fg.obp AS projected_obp_weekly,

            ys.hitter_xwoba_14,
            ys.hitter_xwoba_30,
            ys.hitter_xwoba_season,
            ys.hitter_woba_14,
            ys.hitter_woba_30,
            ys.hitter_woba_season,

            CASE
                WHEN ys.pa_basis > 0 THEN ROUND((ys.hr / ys.pa_basis) * ?, 1)
                ELSE 0
            END AS active_hr_weekly,

            CASE
                WHEN ys.pa_basis > 0 THEN ROUND((ys.r / ys.pa_basis) * ?, 1)
                ELSE 0
            END AS active_r_weekly,

            CASE
                WHEN ys.pa_basis > 0 THEN ROUND((ys.rbi / ys.pa_basis) * ?, 1)
                ELSE 0
            END AS active_rbi_weekly,

            CASE
                WHEN ys.pa_basis > 0 THEN ROUND((ys.sb / ys.pa_basis) * ?, 1)
                ELSE 0
            END AS active_sb_weekly,

            CASE
                WHEN fg.pa > 0 THEN ROUND((fg.hr / fg.pa) * ?, 1)
                ELSE 0
            END AS projected_hr_weekly,

            CASE
                WHEN fg.pa > 0 THEN ROUND((fg.r / fg.pa) * ?, 1)
                ELSE 0
            END AS projected_r_weekly,

            CASE
                WHEN fg.pa > 0 THEN ROUND((fg.rbi / fg.pa) * ?, 1)
                ELSE 0
            END AS projected_rbi_weekly,

            CASE
                WHEN fg.pa > 0 THEN ROUND((fg.sb / fg.pa) * ?, 1)
                ELSE 0
            END AS projected_sb_weekly,

            CASE
                WHEN ys.pa_basis > 0 THEN
                    ROUND(
                        MIN(
                            100,
                            (ys.pa_basis / (? * ?)) * 100
                        ),
                        0
                    )
                ELSE 0
            END AS availability_pct

        FROM players p
        JOIN fangraphs_hitters_ros fg
            ON p.fangraphs_name = fg.player_name
        LEFT JOIN yahoo_current_stats ys
            ON p.yahoo_player_id = ys.yahoo_player_id
        WHERE p.match_confidence IS NOT NULL
          AND p.match_confidence != 'unmatched'
          AND p.player_type = 'hitter'
        ORDER BY p.is_on_my_team DESC, p.is_available DESC, fg.hr DESC
    """, (
        hitter_weekly_ab,
        hitter_weekly_ab,
        hitter_weekly_ab,
        hitter_weekly_ab,

        hitter_weekly_ab,
        hitter_weekly_ab,
        hitter_weekly_ab,
        hitter_weekly_ab,

        hitter_weekly_ab,
        weeks_elapsed,
    )).fetchall()

    pitchers = conn.execute("""
        SELECT
            p.yahoo_player_id,
            p.yahoo_name,
            p.yahoo_team,
            p.fantasy_team_name,
            p.is_available,
            p.is_on_my_team,
            p.yahoo_pitcher_season_rank,
            p.yahoo_pitcher_30_day_rank,
            p.yahoo_position,
            p.yahoo_positions,
            p.player_type,
            p.injury_status,

            ys.ip AS current_ip,
            ys.w AS current_w,
            ys.sv_hld AS current_sv_hld,
            ys.so AS current_k,
            ys.era AS active_era,
            ys.whip AS active_whip,

            fg.ip AS projected_ip,
            fg.w AS projected_w,
            fg.sv_hld AS projected_sv_hld,
            fg.so AS projected_k,
            fg.era AS projected_era_weekly,
            fg.whip AS projected_whip_weekly,

            ys.pitcher_xwoba_against_14,
            ys.pitcher_xwoba_against_30,
            ys.pitcher_xwoba_against_season,
            ys.pitcher_woba_against_14,
            ys.pitcher_woba_against_30,
            ys.pitcher_woba_against_season,

            CASE
                WHEN p.yahoo_positions LIKE '%SP%' THEN ?
                ELSE ?
            END AS role_weekly_ip,

            CASE
                WHEN ys.ip > 0 THEN
                    ROUND(
                        (ys.w / ys.ip) *
                        CASE WHEN p.yahoo_positions LIKE '%SP%' THEN ? ELSE ? END,
                        1
                    )
                ELSE 0
            END AS active_w_weekly,

            CASE
                WHEN ys.ip > 0 THEN
                    ROUND(
                        (ys.sv_hld / ys.ip) *
                        CASE WHEN p.yahoo_positions LIKE '%SP%' THEN ? ELSE ? END,
                        1
                    )
                ELSE 0
            END AS active_sv_hld_weekly,

            CASE
                WHEN ys.ip > 0 THEN
                    ROUND(
                        (ys.so / ys.ip) *
                        CASE WHEN p.yahoo_positions LIKE '%SP%' THEN ? ELSE ? END,
                        1
                    )
                ELSE 0
            END AS active_k_weekly,

            CASE
                WHEN fg.ip > 0 THEN
                    ROUND(
                        (fg.w / fg.ip) *
                        CASE WHEN p.yahoo_positions LIKE '%SP%' THEN ? ELSE ? END,
                        1
                    )
                ELSE 0
            END AS projected_w_weekly,

            CASE
                WHEN fg.ip > 0 THEN
                    ROUND(
                        (fg.sv_hld / fg.ip) *
                        CASE WHEN p.yahoo_positions LIKE '%SP%' THEN ? ELSE ? END,
                        1
                    )
                ELSE 0
            END AS projected_sv_hld_weekly,

            CASE
                WHEN fg.ip > 0 THEN
                    ROUND(
                        (fg.so / fg.ip) *
                        CASE WHEN p.yahoo_positions LIKE '%SP%' THEN ? ELSE ? END,
                        1
                    )
                ELSE 0
            END AS projected_k_weekly,

            CASE
                WHEN ys.ip > 0 THEN
                    ROUND(
                        MIN(
                            100,
                            (
                                ys.ip /
                                (
                                    CASE WHEN p.yahoo_positions LIKE '%SP%' THEN ? ELSE ? END
                                    * ?
                                )
                            ) * 100
                        ),
                        0
                    )
                ELSE 0
            END AS availability_pct

        FROM players p
        JOIN fangraphs_pitchers_ros fg
            ON p.fangraphs_name = fg.player_name
        LEFT JOIN yahoo_current_stats ys
            ON p.yahoo_player_id = ys.yahoo_player_id
        WHERE p.match_confidence IS NOT NULL
          AND p.match_confidence != 'unmatched'
          AND p.player_type = 'pitcher'
        ORDER BY p.is_on_my_team DESC, p.is_available DESC, fg.sv_hld DESC
    """, (
        starter_weekly_ip,
        reliever_weekly_ip,

        starter_weekly_ip,
        reliever_weekly_ip,

        starter_weekly_ip,
        reliever_weekly_ip,

        starter_weekly_ip,
        reliever_weekly_ip,

        starter_weekly_ip,
        reliever_weekly_ip,

        starter_weekly_ip,
        reliever_weekly_ip,

        starter_weekly_ip,
        reliever_weekly_ip,

        starter_weekly_ip,
        reliever_weekly_ip,
        weeks_elapsed,
    )).fetchall()

    conn.close()

    return jsonify({
        "hitters": [dict(row) for row in hitters],
        "pitchers": [dict(row) for row in pitchers],
    })


@app.route("/api/team-weekly-averages")
def team_weekly_averages():
    conn = get_db_connection()

    player_type = request.args.get("type", "hitters")
    week = request.args.get("week", "average")

    if week != "average":
        if player_type == "hitters":
            rows = conn.execute("""
                SELECT
                    fantasy_team_name,
                    r AS r_weekly,
                    hr AS hr_weekly,
                    rbi AS rbi_weekly,
                    sb AS sb_weekly,
                    obp AS obp_avg
                FROM team_weekly_stats
                WHERE week = ?
                ORDER BY r DESC
            """, (week,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT
                    fantasy_team_name,
                    w AS w_weekly,
                    k AS k_weekly,
                    sv_hld AS sv_hld_weekly,
                    era AS era_avg,
                    whip AS whip_avg
                FROM team_weekly_stats
                WHERE week = ?
                ORDER BY k DESC
            """, (week,)).fetchall()

        conn.close()
        return jsonify([dict(row) for row in rows])

    if player_type == "hitters":
        rows = conn.execute("""
            WITH ranked_hitters AS (
                SELECT
                    p.fantasy_team_name,
                    p.yahoo_name,

                    CASE WHEN ys.pa_basis > 0 THEN ROUND((ys.r / ys.pa_basis) * 25, 1)
                         ELSE 0 END AS r_wk,

                    CASE WHEN ys.pa_basis > 0 THEN ROUND((ys.hr / ys.pa_basis) * 25, 1)
                         ELSE 0 END AS hr_wk,

                    CASE WHEN ys.pa_basis > 0 THEN ROUND((ys.rbi / ys.pa_basis) * 25, 1)
                         ELSE 0 END AS rbi_wk,

                    CASE WHEN ys.pa_basis > 0 THEN ROUND((ys.sb / ys.pa_basis) * 25, 1)
                         ELSE 0 END AS sb_wk,

                    ys.obp AS obp,

                    ROW_NUMBER() OVER (
                        PARTITION BY p.fantasy_team_name
                        ORDER BY
                            COALESCE(
                                CASE WHEN ys.pa_basis > 0 THEN
                                    (
                                        ((ys.r / ys.pa_basis) * 25) +
                                        ((ys.hr / ys.pa_basis) * 25) +
                                        ((ys.rbi / ys.pa_basis) * 25) +
                                        ((ys.sb / ys.pa_basis) * 25)
                                    )
                                ELSE 0 END,
                                0
                            ) DESC
                    ) AS starter_rank

                FROM players p
                LEFT JOIN yahoo_current_stats ys
                    ON p.yahoo_player_id = ys.yahoo_player_id
                WHERE p.fantasy_team_name IS NOT NULL
                  AND p.player_type = 'hitter'
            )

            SELECT
                fantasy_team_name,
                COUNT(*) AS starters_count,
                ROUND(SUM(r_wk), 1) AS r_weekly,
                ROUND(SUM(hr_wk), 1) AS hr_weekly,
                ROUND(SUM(rbi_wk), 1) AS rbi_weekly,
                ROUND(SUM(sb_wk), 1) AS sb_weekly,
                ROUND(AVG(obp), 3) AS obp_avg
            FROM ranked_hitters
            WHERE starter_rank <= 10
            GROUP BY fantasy_team_name
            ORDER BY r_weekly DESC
        """).fetchall()

    else:
        rows = conn.execute("""
            WITH ranked_pitchers AS (
                SELECT
                    p.fantasy_team_name,
                    p.yahoo_name,

                    CASE
                        WHEN p.yahoo_positions LIKE '%SP%' THEN 11
                        ELSE 3.5
                    END AS role_weekly_ip,

                    CASE WHEN ys.ip > 0 THEN ROUND((ys.w / ys.ip) *
                        CASE WHEN p.yahoo_positions LIKE '%SP%' THEN 11 ELSE 3.5 END, 1)
                        ELSE 0 END AS w_wk,

                    CASE WHEN ys.ip > 0 THEN ROUND((ys.so / ys.ip) *
                        CASE WHEN p.yahoo_positions LIKE '%SP%' THEN 11 ELSE 3.5 END, 1)
                        ELSE 0 END AS k_wk,

                    CASE WHEN ys.ip > 0 THEN ROUND((ys.sv_hld / ys.ip) *
                        CASE WHEN p.yahoo_positions LIKE '%SP%' THEN 11 ELSE 3.5 END, 1)
                        ELSE 0 END AS sv_hld_wk,

                    ys.era,
                    ys.whip,

                    ROW_NUMBER() OVER (
                        PARTITION BY p.fantasy_team_name
                        ORDER BY
                            COALESCE(
                                CASE WHEN ys.ip > 0 THEN
                                    (
                                        ((ys.w / ys.ip) *
                                            CASE WHEN p.yahoo_positions LIKE '%SP%' THEN 11 ELSE 3.5 END
                                        ) +
                                        ((ys.so / ys.ip) *
                                            CASE WHEN p.yahoo_positions LIKE '%SP%' THEN 11 ELSE 3.5 END
                                        ) +
                                        ((ys.sv_hld / ys.ip) *
                                            CASE WHEN p.yahoo_positions LIKE '%SP%' THEN 11 ELSE 3.5 END
                                        )
                                    )
                                ELSE 0 END,
                                0
                            ) DESC
                    ) AS starter_rank

                FROM players p
                LEFT JOIN yahoo_current_stats ys
                    ON p.yahoo_player_id = ys.yahoo_player_id
                WHERE p.fantasy_team_name IS NOT NULL
                  AND p.player_type = 'pitcher'
            )

            SELECT
                fantasy_team_name,
                COUNT(*) AS starters_count,
                ROUND(SUM(w_wk), 1) AS w_weekly,
                ROUND(SUM(k_wk), 1) AS k_weekly,
                ROUND(SUM(sv_hld_wk), 1) AS sv_hld_weekly,
                ROUND(AVG(era), 3) AS era_avg,
                ROUND(AVG(whip), 3) AS whip_avg
            FROM ranked_pitchers
            WHERE starter_rank <= 9
            GROUP BY fantasy_team_name
            ORDER BY k_weekly DESC
        """).fetchall()

    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/demo")
def demo():
    players = [
        {"name": "Aaron Judge", "team": "NYY", "position": "OF", "hr": 58, "rbi": 130, "sb": 10, "obp": .410},
        {"name": "Bobby Witt Jr.", "team": "KC", "position": "SS", "hr": 32, "rbi": 109, "sb": 45, "obp": .389},
        {"name": "Jose Ramirez", "team": "CLE", "position": "3B", "hr": 39, "rbi": 118, "sb": 41, "obp": .372},
    ]

    return render_template("dashboard.html", players=players)


@app.route("/yahoo-login")
def yahoo_login():
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

    for week in range(1, 26):
        try:
            data = get_week_scoreboard(access_token, league_key, week)
            week_matchups = parse_week_matchups(data)
            all_matchups.extend(week_matchups)
        except Exception as e:
            print(f"Skipping week {week}. Error: {e}")

    totals = build_totals(all_matchups)

    return redirect("/")


@app.route("/api/dashboard")
def api_dashboard():
    access_token = session.get("access_token")

    if not access_token:
        return jsonify({"error": "Not logged into Yahoo"}), 401

    league_key = "469.l.64625"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/teams/stats?format=json"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    team_totals = []

    try:
        yahoo_teams = data["fantasy_content"]["league"][1]["teams"]

        for key, value in yahoo_teams.items():
            if key == "count":
                continue

            team = value["team"]
            team_name = get_team_name(team)

            stats = {}
            raw_stats = team[1]["team_stats"]["stats"]

            for item in raw_stats:
                stat = item["stat"]
                stat_id = stat["stat_id"]
                value = stat.get("value", "0")

                if stat_id in SCORING_STATS:
                    stats[stat_id] = to_number(value)

            team_totals.append({
                "team": team_name,
                "stats": stats
            })

    except Exception as e:
        print("Parsing season stats error:", e)
        return jsonify({"error": "Failed to parse Yahoo season stats"}), 500

    category_tables = build_category_tables(team_totals)

    return jsonify({
        "categoryTables": [
            {
                "key": key,
                "label": value["label"],
                "rows": value["rows"]
            }
            for key, value in category_tables.items()
        ]
    })


# ============================================================
# Serve the built React frontend from frontend/dist
# Render build command should run: cd frontend && npm install && npm run build
# Start command should run this Flask app.
# ============================================================
@app.route("/")
def serve_frontend():
    index_path = os.path.join(FRONTEND_DIST, "index.html")

    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIST, "index.html")

    return "Frontend build not found. Run: cd frontend && npm run build", 500


@app.route("/assets/<path:path>")
def serve_frontend_assets(path):
    return send_from_directory(FRONTEND_ASSETS, path)


@app.route("/<path:path>")
def serve_frontend_fallback(path):
    if path.startswith("api/"):
        return jsonify({"error": "API route not found"}), 404

    requested_file = os.path.join(FRONTEND_DIST, path)
    if os.path.exists(requested_file) and os.path.isfile(requested_file):
        return send_from_directory(FRONTEND_DIST, path)

    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIST, "index.html")

    return "Frontend build not found. Run: cd frontend && npm run build", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)