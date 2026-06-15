from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session
)

from models.database import (
    initialize_database,
    create_user,
    get_user
)

from players import get_players_by_team

from datetime import datetime

from datetime import datetime, timedelta

from models.database import get_connection
import os

print("DATABASE_URL:", os.environ.get("DATABASE_URL"))

app = Flask(__name__)
app.secret_key = "mundial2026"

initialize_database()

from models.database import seed_players
seed_players()

try:

    create_user(
        "admin",
        "Mundial2026!",
        "admin"
    )

except:
    pass


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    user = get_user(username)

    if user and user["password"] == password:

        session["user"] = username
        session["role"] = user["role"]

        return redirect("/dashboard")

    return render_template(
        "login.html",
        error="Λάθος όνομα χρήστη ή κωδικός"
    )

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    selected_date = request.args.get("date")

    if selected_date:

        cursor.execute("""
            SELECT *
            FROM matches
            WHERE kickoff LIKE %s
            ORDER BY kickoff ASC
        """, (selected_date + "%",))

    else:

        cursor.execute("""
            SELECT *
            FROM matches
            ORDER BY kickoff ASC
        """)

    matches = cursor.fetchall()

    conn.close()

    now = datetime.now() + timedelta(hours=3)

    for match in matches:

        match["home_players"] = get_players_by_team(match["home_team"])
        match["away_players"] = get_players_by_team(match["away_team"])

        try:
            kickoff = datetime.strptime(
                match["kickoff"],
                "%Y-%m-%d %H:%M"
            )

            match["locked"] = now >= kickoff

        except:
            match["locked"] = False

    return render_template(
        "dashboard.html",
        matches=matches,
        selected_date=selected_date,
        role=session.get("role"),
        username=session.get("user")
    )



@app.route("/admin")
def admin():

    # 🔐 SECURITY CHECK
    if "user" not in session:
        return redirect("/")

    if session.get("role") != "admin":
        return render_template(
            "access_denied.html",
            message="Δεν έχεις δικαίωμα πρόσβασης σε αυτή τη σελίδα."
        )

    conn = get_connection()
    cursor = conn.cursor()

    # 📋 fetch all matches
    cursor.execute("""
        SELECT *
        FROM matches
        ORDER BY finished ASC, kickoff ASC
    """)

    matches = cursor.fetchall()

    conn.close()

    return render_template("admin.html", matches=matches)


@app.route("/add_match", methods=["POST"])
def add_match():

    if "user" not in session:
        return redirect("/")

    if session["role"] != "admin":
        return "Δεν έχεις πρόσβαση"

    from models.database import get_connection
    try: 
        home = request.form["home_team"]
        away = request.form["away_team"]
        phase = request.form["phase"]
        kickoff = request.form["kickoff"]
        group = request.form["group_name"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO matches
            (home_team, away_team, phase, kickoff , group_name)
            VALUES (%s, %s, %s, %s, %s)
        """, (home, away, phase, kickoff, group))

        conn.commit()
        
    finally:
            conn.close()
    return redirect("/admin")


@app.route("/delete_match/<int:match_id>", methods=["POST"])
def delete_match(match_id):

    if "user" not in session:
        return redirect("/")

    if session.get("role") != "admin":
        return "Δεν έχεις πρόσβαση"

    conn = get_connection()
    cursor = conn.cursor()

    # πρώτα σβήνουμε προβλέψεις
    cursor.execute("""
        DELETE FROM predictions
        WHERE match_id= %s
    """, (match_id,))

    # μετά τον αγώνα
    cursor.execute("""
        DELETE FROM matches
        WHERE id= %s
    """, (match_id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/matches")
def matches():

    if "user" not in session:
        return redirect("/")

    from models.database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM matches ORDER BY kickoff ASC")
    matches = cursor.fetchall()

    conn.close()

    return render_template("matches.html", matches=matches)


@app.route("/predict/<int:match_id>", methods=["POST"])
def predict(match_id):

    # 🔒 admin block
    if session.get("role") == "admin":
        return "Admins cannot make predictions"

    # 🔒 login check
    if "user" not in session:
        return redirect("/")

    from models.database import get_connection
    from datetime import datetime

    conn = get_connection()
    cursor = conn.cursor()

    # 🔥 1. βρίσκουμε match kickoff
    cursor.execute("""
        SELECT kickoff
        FROM matches
        WHERE id= %s
    """, (match_id,))

    match = cursor.fetchone()

    if not match:
        conn.close()
        return "Match not found"

    # ⚠️ convert kickoff
    try:
        kickoff_time = datetime.strptime(match["kickoff"], "%Y-%m-%d %H:%M")
    except:
        conn.close()
        return "Invalid kickoff format in DB"

    now = datetime.now() + timedelta(hours=3)

    # 🔒 LOCK RULE
    if now >= kickoff_time:
        conn.close()
        return "⛔ Predictions are locked (match already started)"

   # 📥 form data
    home = int(request.form["home_score"])
    away = int(request.form["away_score"])

    home_scorers = request.form.getlist("home_scorers_" + str(match_id))
    away_scorers = request.form.getlist("away_scorers_" + str(match_id))

    home_other = request.form.get("home_other_" + str(match_id), "")
    away_other = request.form.get("away_other_" + str(match_id), "")

    if home_other:
        home_scorers.append(home_other)

    if away_other:
        away_scorers.append(away_other)

    # 🚨 VALIDATION (ΑΥΤΟ ΣΟΥ ΕΛΕΙΠΕ)
    if len(home_scorers) > home:
        return f"⛔ Max home scorers allowed: {home}"

    if len(away_scorers) > away:
        return f"⛔ Max away scorers allowed: {away}"

    # 💾 final format για DB
    scorers = ",".join(home_scorers + away_scorers)

    # 👤 user id
    cursor.execute("""
        SELECT id FROM users WHERE username= %s
    """, (session["user"],))

    user_row = cursor.fetchone()

    if not user_row:
        conn.close()
        return "User not found"

    user_id = user_row["id"]

    # 🔁 check existing prediction (ΔΙΚΟ ΣΟΥ LOGIC ΑΚΟΥΜΠΗΤΟ)
    cursor.execute("""
        SELECT id FROM predictions
        WHERE player_id=%s AND match_id=%s
    """, (user_id, match_id))

    existing = cursor.fetchone()

    if existing:
        conn.close()
        return render_template(
            "dashboard.html",
            role=session.get("role"),
            username=session.get("user"),
            error="Έχεις καταχωρήσει ήδη πρόβλεψη για αυτόν τον αγώνα."
        )

    # 💾 insert prediction
    cursor.execute("""
        INSERT INTO predictions
        (player_id, match_id, home_score, away_score, scorers)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, match_id, home, away, scorers))

    conn.commit()
    conn.close()

    return redirect("/dashboard#matches")

def get_result(home, away):
    if home > away:
        return "1"
    elif home < away:
        return "2"
    else:
        return "X"


def calculate_points(pred, real_home, real_away, real_scorers):

    points = 0
    exact = 0
    result = 0
    scorers_points = 0

    # EXACT SCORE
    if pred["home_score"] == real_home and pred["away_score"] == real_away:
        points += 5
        exact = 1

    # RESULT
    pred_result = get_result(pred["home_score"], pred["away_score"])
    real_result = get_result(real_home, real_away)

    if pred_result == real_result:
        points += 3
        result = 1

    # SCORERS
    if pred["scorers"]:
        predicted = [s.strip() for s in pred["scorers"].split(",")]
        real_list = [s.strip() for s in real_scorers.split(",")]

        for s in predicted:
            if s in real_list:
                points += 1
                scorers_points += 1

    return {
        "points": points,
        "exact": exact,
        "result": result,
        "scorers": scorers_points
    }

@app.route("/test-score")
def test_score():

    return "Scoring engine ready"


@app.route("/leaderboard")
def leaderboard():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, points, exact_scores, correct_results, correct_scorers
        FROM users
        WHERE role != 'admin'
        ORDER BY points DESC,
                 exact_scores DESC,
                 correct_results DESC,
                 correct_scorers DESC
    """)

    users = cursor.fetchall()
    conn.close()

    return render_template("leaderboard.html", users=users)


@app.route("/finish_match/<int:match_id>", methods=["POST"])
def finish_match(match_id):

    from models.database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    # 🔒 1. CHECK IF ALREADY FINISHED
    cursor.execute("""
        SELECT finished
        FROM matches
        WHERE id=%s
    """, (match_id,))

    match = cursor.fetchone()

    if not match:
        conn.close()
        return "Match not found"

    if match["finished"] == 1:
        conn.close()
        return "⛔ Match already finished (no double scoring allowed)"

    # 📥 input
    home_score = int(request.form["home_score"])
    away_score = int(request.form["away_score"])
    scorers = request.form.get("scorers", "")

    # 🟢 2. update match (mark finished FIRST)
    cursor.execute("""
        UPDATE matches
        SET home_score=%s,
            away_score=%s,
            scorers=%s,
            finished=1
        WHERE id=%s
    """, (home_score, away_score, scorers, match_id))

    # 👇 fetch predictions
    cursor.execute("""
        SELECT player_id, home_score, away_score, scorers
        FROM predictions
        WHERE match_id=%s
    """, (match_id,))

    predictions = cursor.fetchall()

    # 🧠 scoring
    for p in predictions:

        pred = {
            "home_score": p["home_score"],
            "away_score": p["away_score"],
            "scorers": p["scorers"]
        }

        result = calculate_points(pred, home_score, away_score, scorers)

        cursor.execute("""
            UPDATE users
            SET points = points + %s,
                exact_scores = exact_scores + %s,
                correct_results = correct_results + %s,
                correct_scorers = correct_scorers + %s
            WHERE id=%s
        """, (
            result["points"],
            result["exact"],
            result["result"],
            result["scorers"],
            p["player_id"]
        ))

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/predictions")
def predictions():

    player = request.args.get("player")

    conn = get_connection()
    cursor = conn.cursor()

    # μόνο finished matches στο default view
    base_query = """
        SELECT 
            m.home_team,
            m.away_team,
            m.finished,
            u.username,
            p.home_score,
            p.away_score,
            p.scorers
        FROM predictions p
        JOIN users u ON u.id = p.player_id
        JOIN matches m ON m.id = p.match_id
        WHERE m.finished = 1
    """

    params = []

    # filter αν υπάρχει player
    if player:
        base_query += " AND u.username = %s"
        params.append(player)

    base_query += " ORDER BY u.username, m.id"

    cursor.execute(base_query, params)
    rows = cursor.fetchall()

    # grouping
    grouped = {}
    for r in rows:
        user = r["username"]
        grouped.setdefault(user, []).append(r)

    # users για dropdown
        cursor.execute("""
        SELECT username
        FROM users
        WHERE role != 'admin'
        ORDER BY username
    """)
    users = cursor.fetchall()

    conn.close()

    return render_template(
        "predictions.html",
        grouped=grouped,
        users=users,
        selected_player=player
    )


@app.route("/profile/<username>")
def profile(username):

    conn = get_connection()
    cursor = conn.cursor()

    # user info
    cursor.execute("""
        SELECT id, username, points, exact_scores, correct_results, correct_scorers
        FROM users
        WHERE username=%s
    """, (username,))

    user = cursor.fetchone()

    # check if viewer is the same user
    viewer = session.get("user")

    if viewer == username:
        # 👤 OWNER → βλέπει ΟΛΑ τα predictions
        cursor.execute("""
            SELECT m.home_team, m.away_team, m.finished,
                   p.home_score, p.away_score, p.scorers
            FROM predictions p
            JOIN matches m ON m.id = p.match_id
            JOIN users u ON u.id = p.player_id
            WHERE u.username=%s
            ORDER BY m.id DESC
        """, (username,))
    else:
        # 👀 OTHERS → μόνο finished
        cursor.execute("""
            SELECT m.home_team, m.away_team, m.finished,
                   p.home_score, p.away_score, p.scorers
            FROM predictions p
            JOIN matches m ON m.id = p.match_id
            JOIN users u ON u.id = p.player_id
            WHERE u.username=%s
            AND m.finished = 1
            ORDER BY m.id DESC
        """, (username,))

    history = cursor.fetchall()

    conn.close()

    return render_template("profile.html", user=user, history=history)


@app.route("/match/<int:match_id>")
def match_page(match_id):

    conn = get_connection()
    cursor = conn.cursor()

    # match info
    cursor.execute("""
        SELECT *
        FROM matches
        WHERE id=%s
    """, (match_id,))

    match = cursor.fetchone()

    # predictions with usernames
    cursor.execute("""
        SELECT u.username, p.home_score, p.away_score, p.scorers
        FROM predictions p
        JOIN users u ON u.id = p.player_id
        WHERE p.match_id=%s
        ORDER BY u.username
    """, (match_id,))

    predictions = cursor.fetchall()

    conn.close()

    return render_template(
        "match.html",
        match=match,
        predictions=predictions
    )


@app.route("/groups")
def groups():

    from models.database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT group_name, team_name
        FROM groups
        ORDER BY group_name
    """)

    data = cursor.fetchall()
    conn.close()

    groups_dict = {}

    for row in data:

        g = row["group_name"]
        team = row["team_name"]

        if g not in groups_dict:
            groups_dict[g] = []

        groups_dict[g].append(team)

    return render_template("groups.html", groups=groups_dict)

@app.route("/add_group_team", methods=["POST"])
def add_group_team():

    if session.get("role") != "admin":
        return "No access"

    group_name = request.form["group_name"]
    team_name = request.form["team_name"]

    from models.database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO groups (group_name, team_name)
        VALUES (%s, %s)
    """, (group_name, team_name))

    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/standings")
def standings():

    from models.database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT home_team,
               away_team,
               home_score,
               away_score,
               group_name
        FROM matches
        WHERE finished = 1
    """)

    matches = cursor.fetchall()
    conn.close()

    table = {}

    def init_team(group, team):
        if group not in table:
            table[group] = {}

        if team not in table[group]:
            table[group][team] = {
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "gf": 0,
                "ga": 0,
                "points": 0
            }

    for row in matches:

        h = row["home_team"]
        a = row["away_team"]
        hs = row["home_score"]
        aw = row["away_score"]
        group = row["group_name"]

        init_team(group, h)
        init_team(group, a)

        # stats
        for team_data in [(h, hs, aw), (a, aw, hs)]:
            t, gf, ga = team_data

            table[group][t]["played"] += 1
            table[group][t]["gf"] += gf
            table[group][t]["ga"] += ga

        # points
        if hs > aw:

            table[group][h]["wins"] += 1
            table[group][a]["losses"] += 1
            table[group][h]["points"] += 3

        elif aw > hs:

            table[group][a]["wins"] += 1
            table[group][h]["losses"] += 1
            table[group][a]["points"] += 3

        else:

            table[group][h]["draws"] += 1
            table[group][a]["draws"] += 1

            table[group][h]["points"] += 1
            table[group][a]["points"] += 1

    for group in table:

        table[group] = dict(
            sorted(
                table[group].items(),
                key=lambda x: (
                    x[1]["points"],
                    x[1]["gf"] - x[1]["ga"],
                    x[1]["gf"]
                ),
                reverse=True
            )
        )

    return render_template(
        "standings.html",
        table=table
    )


@app.route("/adjust_points/<int:user_id>", methods=["POST"])
def adjust_points(user_id):

    if session.get("role") != "admin":
        return render_template(
            "access_denied.html",
            message="Δεν έχεις δικαίωμα πρόσβασης"
        ), 403

    points_change = int(request.form["points"])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET points = points + %s
        WHERE id = %s
    """, (points_change, user_id))

    conn.commit()
    conn.close()

    return redirect("/leaderboard")


if __name__ == "__main__":
    app.run(debug=True)

