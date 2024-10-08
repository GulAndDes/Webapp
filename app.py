from flask import Flask, request, render_template, redirect, url_for, jsonify
import sqlite3
import hashlib
import time
import threading
import requests

app = Flask(__name__)

# Global variables
global_bank = 0
highest_score = 0
highest_scorer = None
timer_started = False
timer_end_time = 0
timer_lock = threading.Lock()
# Глобальные переменные для управления таймером и рекордами
timer_end_time = None
timer_started = False
timer_lock = threading.Lock()
high_scores = []  # Список для хранения рекордов


@app.route("/")
def index():
    return render_template("index.html")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def start_timer():
    global timer_started, timer_end_time

    with timer_lock:
        if not timer_started:
            timer_started = True
            timer_end_time = time.time() + 30  # Set the timer for 30 seconds
            threading.Thread(target=timer_thread).start()


def timer_thread():
    global highest_score, highest_scorer, global_bank, timer_started

    while True:
        with timer_lock:
            if time.time() >= timer_end_time:
                # End the game and distribute the bank
                if highest_scorer:
                    conn = sqlite3.connect("users.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET coins = coins + ? WHERE username = ?",
                        (int(global_bank * 0.9), highest_scorer),
                    )
                    conn.commit()
                    conn.close()

                # Reset all game state
                global_bank = 0
                highest_score = 0
                highest_scorer = None
                timer_started = False
                break

        time.sleep(1)


def end_game():
    global highest_score, highest_scorer, global_bank, timer_started

    with timer_lock:
        if highest_scorer:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET coins = coins + ? WHERE username = ?",
                (int(global_bank * 0.9), highest_scorer),
            )
            conn.commit()
            conn.close()

        # Reset all game state
        global_bank = 0
        highest_score = 0
        highest_scorer = None
        timer_started = False

        # Clear high scores
        requests.post("http://localhost:5000/clear_high_scores")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, coins) VALUES (?, ?, 500)",
                (username, password),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "User already exists", 400
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and user[0] == password:
            return redirect(url_for("game", username=username))
        else:
            return "Invalid credentials", 400
    return render_template("login.html")


@app.route("/game")
def game():
    username = request.args.get("username")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE username = ?", (username,))
    coins = cursor.fetchone()[0]
    conn.close()
    return render_template(
        "game.html", username=username, coins=coins, global_bank=global_bank
    )


@app.route("/place_bet", methods=["POST"])
def place_bet():
    global global_bank, highest_score, highest_scorer, timer_started

    username = request.form["username"]
    bet_amount = int(request.form["bet"])

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT coins FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    if result and result[0] >= bet_amount:
        cursor.execute(
            "UPDATE users SET coins = coins - ? WHERE username = ?",
            (bet_amount, username),
        )
        conn.commit()

        global_bank += bet_amount
        if not timer_started:
            start_timer()

        cursor.execute("SELECT coins FROM users WHERE username = ?", (username,))
        updated_balance = cursor.fetchone()[0]

        conn.close()

        return jsonify(
            success=True, coinBalance=updated_balance, globalBank=global_bank
        )
    else:
        conn.close()
        return jsonify(success=False, message="Insufficient coins")


@app.route("/update_score", methods=["POST"])
def update_score():
    global high_scores

    data = request.form
    username = data.get("username")
    score = int(data.get("score"))

    # Добавляем новый рекорд в список и сортируем по убыванию
    high_scores.append({"username": username, "score": score})
    high_scores = sorted(high_scores, key=lambda x: x["score"], reverse=True)

    # Обнуляем рекорды
    if len(high_scores) > 10:
        high_scores = high_scores[:10]

    return jsonify({"success": True})


def update_all_users_coins():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = 500 WHERE coins < 500")
    conn.commit()
    conn.close()


@app.route("/get_timer", methods=["GET"])
def get_timer():
    global timer_end_time, timer_started

    with timer_lock:
        if timer_started:
            time_left = max(0, int(timer_end_time - time.time()))
        else:
            time_left = 0

    return jsonify({"timeLeft": time_left})


@app.route("/get_high_scores", methods=["GET"])
def get_high_scores():
    global high_scores

    # Возвращаем рекорды
    return jsonify({"scores": high_scores})


@app.route("/reset_game", methods=["POST"])
def reset_game():
    global highest_score, highest_scorer

    with timer_lock:
        highest_score = 0
        highest_scorer = None

    return jsonify(success=True)


@app.route("/clear_high_scores", methods=["POST"])
def clear_high_scores():
    global high_scores
    high_scores = []  # Clear the high scores list
    return jsonify(success=True)


update_all_users_coins()

if __name__ == "__main__":
    app.run(debug=True)
