"""
PERSONAL HEALTH & WELLNESS MONITORING SYSTEM
Main Flask Application
"""

import os
import io
import base64
import re
from datetime import datetime, date, timedelta

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import MySQLdb.cursors

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from config import Config

# ----------------------------------------------------------------
# APP INITIALIZATION
# ----------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)

sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'sans-serif'


# ----------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------
def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None


def is_valid_password(password):
    # At least 6 chars, one letter, one number
    if len(password) < 6:
        return False
    if not re.search(r'[A-Za-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True


def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 1)


def bmi_category(bmi):
    if bmi < 18.5:
        return 'Underweight'
    elif bmi < 25:
        return 'Normal'
    elif bmi < 30:
        return 'Overweight'
    else:
        return 'Obese'


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100, transparent=True)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64


def get_health_score(user_id, cur):
    """A simple composite health score out of 100."""
    score = 50  # baseline

    # BMI contribution
    cur.execute("SELECT bmi_value FROM bmi_records WHERE user_id=%s ORDER BY recorded_at DESC LIMIT 1", (user_id,))
    bmi_row = cur.fetchone()
    if bmi_row:
        bmi_val = bmi_row['bmi_value']
        if 18.5 <= bmi_val < 25:
            score += 15
        elif bmi_val < 18.5 or (25 <= bmi_val < 30):
            score += 5

    # Water contribution (today)
    today = date.today()
    cur.execute("SELECT SUM(amount_ml) AS total FROM water_tracker WHERE user_id=%s AND log_date=%s", (user_id, today))
    water_row = cur.fetchone()
    if water_row and water_row['total']:
        cur.execute("SELECT water_goal_ml FROM health_profile WHERE user_id=%s", (user_id,))
        goal_row = cur.fetchone()
        goal = goal_row['water_goal_ml'] if goal_row and goal_row['water_goal_ml'] else 2000
        ratio = min(water_row['total'] / goal, 1)
        score += int(ratio * 15)

    # Sleep contribution
    cur.execute("SELECT duration_hours FROM sleep_tracker WHERE user_id=%s ORDER BY log_date DESC LIMIT 1", (user_id,))
    sleep_row = cur.fetchone()
    if sleep_row and 6.5 <= sleep_row['duration_hours'] <= 9:
        score += 10

    # Exercise contribution (last 7 days)
    week_ago = today - timedelta(days=7)
    cur.execute("SELECT COUNT(*) AS cnt FROM exercise_tracker WHERE user_id=%s AND log_date >= %s", (user_id, week_ago))
    ex_row = cur.fetchone()
    if ex_row and ex_row['cnt'] >= 3:
        score += 10

    return min(score, 100)


# ----------------------------------------------------------------
# CONTEXT PROCESSOR (available in all templates)
# ----------------------------------------------------------------
@app.context_processor
def inject_user():
    user_name = session.get('full_name')
    return dict(logged_in=('user_id' in session), current_user_name=user_name)


# ----------------------------------------------------------------
# HOME PAGE
# ----------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


# ----------------------------------------------------------------
# MODULE 2: AUTHENTICATION
# ----------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # ---- Validation ----
        if not all([full_name, email, phone, age, gender, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'danger')
            return redirect(url_for('register'))

        if not is_valid_password(password):
            flash('Password must be at least 6 characters and include letters and numbers.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        try:
            age = int(age)
        except ValueError:
            flash('Age must be a number.', 'danger')
            return redirect(url_for('register'))

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # ---- Duplicate Email Check ----
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            flash('An account with this email already exists.', 'danger')
            cur.close()
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)

        cur.execute("""
            INSERT INTO users (full_name, email, phone, age, gender, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (full_name, email, phone, age, gender, password_hash))
        mysql.connection.commit()

        user_id = cur.lastrowid
        cur.execute("INSERT INTO health_profile (user_id) VALUES (%s)", (user_id,))
        mysql.connection.commit()
        cur.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password_hash'], password):
            session.permanent = True
            session['user_id'] = user['user_id']
            session['full_name'] = user['full_name']
            session['email'] = user['email']
            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


# ----------------------------------------------------------------
# MODULE 3: PROFILE MANAGEMENT
# ----------------------------------------------------------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        height = request.form.get('height') or None
        weight = request.form.get('weight') or None
        medical_conditions = request.form.get('medical_conditions', '').strip()
        fitness_goal = request.form.get('fitness_goal', '').strip()
        water_goal_ml = request.form.get('water_goal_ml') or 2000

        # Profile picture upload
        file = request.files.get('profile_picture')
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"user_{user_id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            cur.execute("UPDATE users SET profile_picture=%s WHERE user_id=%s", (filename, user_id))

        cur.execute("""
            UPDATE health_profile
            SET height=%s, weight=%s, medical_conditions=%s, fitness_goal=%s, water_goal_ml=%s
            WHERE user_id=%s
        """, (height, weight, medical_conditions, fitness_goal, water_goal_ml, user_id))
        mysql.connection.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.execute("SELECT * FROM health_profile WHERE user_id=%s", (user_id,))
    health_profile = cur.fetchone()
    cur.close()

    return render_template('profile.html', user=user, profile=health_profile)


# ----------------------------------------------------------------
# MODULE 4: BMI CALCULATOR
# ----------------------------------------------------------------
@app.route('/bmi', methods=['GET', 'POST'])
@login_required
def bmi():
    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    bmi_result = None
    category = None

    if request.method == 'POST':
        try:
            height = float(request.form.get('height'))
            weight = float(request.form.get('weight'))
        except (TypeError, ValueError):
            flash('Please enter valid numeric height and weight.', 'danger')
            return redirect(url_for('bmi'))

        if height <= 0 or weight <= 0:
            flash('Height and weight must be positive numbers.', 'danger')
            return redirect(url_for('bmi'))

        bmi_result = calculate_bmi(weight, height)
        category = bmi_category(bmi_result)

        cur.execute("""
            INSERT INTO bmi_records (user_id, height, weight, bmi_value, bmi_category)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, height, weight, bmi_result, category))
        mysql.connection.commit()

        # also update health_profile current height/weight
        cur.execute("UPDATE health_profile SET height=%s, weight=%s WHERE user_id=%s", (height, weight, user_id))
        mysql.connection.commit()

        flash('BMI calculated and saved!', 'success')

    cur.execute("SELECT * FROM bmi_records WHERE user_id=%s ORDER BY recorded_at DESC LIMIT 10", (user_id,))
    history = cur.fetchall()
    cur.close()

    chart = None
    if history:
        df_dates = [h['recorded_at'].strftime('%d-%b') for h in reversed(history)]
        df_vals = [h['bmi_value'] for h in reversed(history)]
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.lineplot(x=df_dates, y=df_vals, marker='o', color='#FF7043', ax=ax)
        ax.set_title('BMI History')
        ax.set_ylabel('BMI')
        plt.xticks(rotation=30)
        chart = fig_to_base64(fig)

    return render_template('bmi.html', bmi_result=bmi_result, category=category,
                            history=history, chart=chart)


@app.route('/bmi/delete/<int:record_id>')
@login_required
def delete_bmi(record_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM bmi_records WHERE bmi_id=%s AND user_id=%s", (record_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('BMI record deleted.', 'info')
    return redirect(url_for('bmi'))


# ----------------------------------------------------------------
# MODULE 5: WATER INTAKE TRACKER
# ----------------------------------------------------------------
@app.route('/water', methods=['GET', 'POST'])
@login_required
def water():
    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    today = date.today()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'set_goal':
            goal = request.form.get('water_goal_ml')
            cur.execute("UPDATE health_profile SET water_goal_ml=%s WHERE user_id=%s", (goal, user_id))
            mysql.connection.commit()
            flash('Water goal updated!', 'success')
        else:
            amount = request.form.get('amount_ml')
            try:
                amount = int(amount)
            except (TypeError, ValueError):
                flash('Enter a valid amount.', 'danger')
                return redirect(url_for('water'))
            cur.execute("INSERT INTO water_tracker (user_id, amount_ml, log_date) VALUES (%s, %s, %s)",
                        (user_id, amount, today))
            mysql.connection.commit()
            flash(f'Added {amount} ml of water!', 'success')
        return redirect(url_for('water'))

    cur.execute("SELECT water_goal_ml FROM health_profile WHERE user_id=%s", (user_id,))
    goal_row = cur.fetchone()
    goal = goal_row['water_goal_ml'] if goal_row else 2000

    cur.execute("SELECT SUM(amount_ml) AS total FROM water_tracker WHERE user_id=%s AND log_date=%s", (user_id, today))
    today_total = cur.fetchone()['total'] or 0

    cur.execute("""
        SELECT log_date, SUM(amount_ml) AS total FROM water_tracker
        WHERE user_id=%s GROUP BY log_date ORDER BY log_date DESC LIMIT 7
    """, (user_id,))
    weekly = cur.fetchall()
    cur.close()

    progress_pct = min(int((today_total / goal) * 100), 100) if goal else 0

    chart = None
    if weekly:
        dates = [w['log_date'].strftime('%d-%b') for w in reversed(weekly)]
        totals = [w['total'] for w in reversed(weekly)]
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.barplot(x=dates, y=totals, color='#2196F3', ax=ax)
        ax.set_title('Weekly Water Intake (ml)')
        plt.xticks(rotation=30)
        chart = fig_to_base64(fig)

    return render_template('water.html', goal=goal, today_total=today_total,
                            progress_pct=progress_pct, weekly=weekly, chart=chart)


# ----------------------------------------------------------------
# MODULE 6: WEIGHT TRACKER
# ----------------------------------------------------------------
@app.route('/weight', methods=['GET', 'POST'])
@login_required
def weight():
    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        try:
            weight_val = float(request.form.get('weight'))
        except (TypeError, ValueError):
            flash('Enter a valid weight.', 'danger')
            return redirect(url_for('weight'))
        notes = request.form.get('notes', '').strip()
        log_date = request.form.get('log_date') or date.today().isoformat()

        cur.execute("INSERT INTO weight_tracker (user_id, weight, log_date, notes) VALUES (%s, %s, %s, %s)",
                    (user_id, weight_val, log_date, notes))
        mysql.connection.commit()
        cur.execute("UPDATE health_profile SET weight=%s WHERE user_id=%s", (weight_val, user_id))
        mysql.connection.commit()
        flash('Weight recorded successfully!', 'success')
        return redirect(url_for('weight'))

    cur.execute("SELECT * FROM weight_tracker WHERE user_id=%s ORDER BY log_date DESC LIMIT 15", (user_id,))
    history = cur.fetchall()
    cur.close()

    chart = None
    if history:
        dates = [h['log_date'].strftime('%d-%b') for h in reversed(history)]
        vals = [h['weight'] for h in reversed(history)]
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.lineplot(x=dates, y=vals, marker='o', color='#009688', ax=ax)
        ax.set_title('Weight Progress (kg)')
        plt.xticks(rotation=30)
        chart = fig_to_base64(fig)

    return render_template('weight.html', history=history, chart=chart)


@app.route('/weight/delete/<int:record_id>')
@login_required
def delete_weight(record_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM weight_tracker WHERE weight_id=%s AND user_id=%s", (record_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Weight record deleted.', 'info')
    return redirect(url_for('weight'))


# ----------------------------------------------------------------
# MODULE 7: SLEEP TRACKER
# ----------------------------------------------------------------
@app.route('/sleep', methods=['GET', 'POST'])
@login_required
def sleep():
    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        sleep_time_str = request.form.get('sleep_time')
        wake_time_str = request.form.get('wake_time')
        log_date = request.form.get('log_date') or date.today().isoformat()

        try:
            sleep_t = datetime.strptime(sleep_time_str, '%H:%M')
            wake_t = datetime.strptime(wake_time_str, '%H:%M')
        except (TypeError, ValueError):
            flash('Please provide valid sleep and wake times.', 'danger')
            return redirect(url_for('sleep'))

        duration = (wake_t - sleep_t).total_seconds() / 3600
        if duration <= 0:
            duration += 24  # overnight sleep

        cur.execute("""
            INSERT INTO sleep_tracker (user_id, sleep_time, wake_time, duration_hours, log_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, sleep_time_str, wake_time_str, round(duration, 2), log_date))
        mysql.connection.commit()
        flash(f'Sleep logged: {round(duration, 1)} hours.', 'success')
        return redirect(url_for('sleep'))

    cur.execute("SELECT * FROM sleep_tracker WHERE user_id=%s ORDER BY log_date DESC LIMIT 14", (user_id,))
    history = cur.fetchall()
    cur.close()

    chart = None
    if history:
        dates = [h['log_date'].strftime('%d-%b') for h in reversed(history)]
        vals = [h['duration_hours'] for h in reversed(history)]
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.barplot(x=dates, y=vals, color='#7E57C2', ax=ax)
        ax.set_title('Sleep Duration (hours)')
        plt.xticks(rotation=30)
        chart = fig_to_base64(fig)

    return render_template('sleep.html', history=history, chart=chart)


@app.route('/sleep/delete/<int:record_id>')
@login_required
def delete_sleep(record_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM sleep_tracker WHERE sleep_id=%s AND user_id=%s", (record_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Sleep record deleted.', 'info')
    return redirect(url_for('sleep'))


# ----------------------------------------------------------------
# MODULE 8: EXERCISE TRACKER
# ----------------------------------------------------------------
@app.route('/exercise', methods=['GET', 'POST'])
@login_required
def exercise():
    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        exercise_name = request.form.get('exercise_name', '').strip()
        try:
            duration = int(request.form.get('duration_minutes'))
            calories = float(request.form.get('calories_burned'))
        except (TypeError, ValueError):
            flash('Please enter valid numeric values.', 'danger')
            return redirect(url_for('exercise'))
        log_date = request.form.get('log_date') or date.today().isoformat()

        cur.execute("""
            INSERT INTO exercise_tracker (user_id, exercise_name, duration_minutes, calories_burned, log_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, exercise_name, duration, calories, log_date))
        mysql.connection.commit()
        flash('Exercise logged successfully!', 'success')
        return redirect(url_for('exercise'))

    cur.execute("SELECT * FROM exercise_tracker WHERE user_id=%s ORDER BY log_date DESC LIMIT 15", (user_id,))
    history = cur.fetchall()
    cur.close()

    chart = None
    if history:
        names = [h['exercise_name'] for h in history[:7]]
        calories = [h['calories_burned'] for h in history[:7]]
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.pie(calories, labels=names, autopct='%1.0f%%',
               colors=sns.color_palette('YlOrRd', len(names)))
        ax.set_title('Calories Burned Breakdown')
        chart = fig_to_base64(fig)

    return render_template('exercise.html', history=history, chart=chart)


@app.route('/exercise/delete/<int:record_id>')
@login_required
def delete_exercise(record_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM exercise_tracker WHERE exercise_id=%s AND user_id=%s", (record_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Exercise record deleted.', 'info')
    return redirect(url_for('exercise'))


# ----------------------------------------------------------------
# MODULE 9: DASHBOARD
# ----------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    today = date.today()

    cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()

    cur.execute("SELECT * FROM health_profile WHERE user_id=%s", (user_id,))
    profile_data = cur.fetchone()

    cur.execute("SELECT * FROM bmi_records WHERE user_id=%s ORDER BY recorded_at DESC LIMIT 1", (user_id,))
    latest_bmi = cur.fetchone()

    cur.execute("SELECT SUM(amount_ml) AS total FROM water_tracker WHERE user_id=%s AND log_date=%s", (user_id, today))
    water_today = cur.fetchone()['total'] or 0

    cur.execute("SELECT * FROM weight_tracker WHERE user_id=%s ORDER BY log_date DESC LIMIT 1", (user_id,))
    latest_weight = cur.fetchone()

    cur.execute("SELECT * FROM sleep_tracker WHERE user_id=%s ORDER BY log_date DESC LIMIT 1", (user_id,))
    latest_sleep = cur.fetchone()

    week_ago = today - timedelta(days=7)
    cur.execute("SELECT COUNT(*) AS cnt, SUM(calories_burned) AS cal FROM exercise_tracker WHERE user_id=%s AND log_date >= %s",
                (user_id, week_ago))
    exercise_week = cur.fetchone()

    cur.execute("""
        SELECT COUNT(*) AS total_count FROM (
            SELECT bmi_id AS id FROM bmi_records WHERE user_id=%s
            UNION ALL SELECT water_id FROM water_tracker WHERE user_id=%s
            UNION ALL SELECT weight_id FROM weight_tracker WHERE user_id=%s
            UNION ALL SELECT sleep_id FROM sleep_tracker WHERE user_id=%s
            UNION ALL SELECT exercise_id FROM exercise_tracker WHERE user_id=%s
        ) AS combined
    """, (user_id, user_id, user_id, user_id, user_id))
    total_activities = cur.fetchone()['total_count']

    health_score = get_health_score(user_id, cur)

    water_goal = profile_data['water_goal_ml'] if profile_data and profile_data['water_goal_ml'] else 2000
    water_pct = min(int((water_today / water_goal) * 100), 100) if water_goal else 0

    cur.close()

    return render_template('dashboard.html', user=user, profile=profile_data,
                            latest_bmi=latest_bmi, water_today=water_today, water_pct=water_pct,
                            latest_weight=latest_weight, latest_sleep=latest_sleep,
                            exercise_week=exercise_week, total_activities=total_activities,
                            health_score=health_score)


# ----------------------------------------------------------------
# MODULE 10: REPORTS
# ----------------------------------------------------------------
@app.route('/reports')
@login_required
def reports():
    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cur.execute("SELECT * FROM bmi_records WHERE user_id=%s ORDER BY recorded_at DESC", (user_id,))
    bmi_data = cur.fetchall()

    cur.execute("SELECT log_date, SUM(amount_ml) AS total FROM water_tracker WHERE user_id=%s GROUP BY log_date ORDER BY log_date DESC LIMIT 30", (user_id,))
    water_data = cur.fetchall()

    cur.execute("SELECT * FROM weight_tracker WHERE user_id=%s ORDER BY log_date DESC", (user_id,))
    weight_data = cur.fetchall()

    cur.execute("SELECT * FROM sleep_tracker WHERE user_id=%s ORDER BY log_date DESC", (user_id,))
    sleep_data = cur.fetchall()

    cur.execute("SELECT * FROM exercise_tracker WHERE user_id=%s ORDER BY log_date DESC", (user_id,))
    exercise_data = cur.fetchall()
    cur.close()

    charts = {}

    if bmi_data:
        dates = [b['recorded_at'].strftime('%d-%b') for b in reversed(bmi_data[:10])]
        vals = [b['bmi_value'] for b in reversed(bmi_data[:10])]
        fig, ax = plt.subplots(figsize=(6, 3.2))
        sns.lineplot(x=dates, y=vals, marker='o', color='#4CAF50', ax=ax)
        ax.set_title('BMI Trend')
        plt.xticks(rotation=30)
        charts['bmi'] = fig_to_base64(fig)

    if water_data:
        dates = [w['log_date'].strftime('%d-%b') for w in reversed(water_data[:10])]
        vals = [w['total'] for w in reversed(water_data[:10])]
        fig, ax = plt.subplots(figsize=(6, 3.2))
        sns.barplot(x=dates, y=vals, color='#2196F3', ax=ax)
        ax.set_title('Water Intake Trend (ml)')
        plt.xticks(rotation=30)
        charts['water'] = fig_to_base64(fig)

    if weight_data:
        dates = [w['log_date'].strftime('%d-%b') for w in reversed(weight_data[:10])]
        vals = [w['weight'] for w in reversed(weight_data[:10])]
        fig, ax = plt.subplots(figsize=(6, 3.2))
        sns.lineplot(x=dates, y=vals, marker='o', color='#009688', ax=ax)
        ax.set_title('Weight Trend (kg)')
        plt.xticks(rotation=30)
        charts['weight'] = fig_to_base64(fig)

    if sleep_data:
        dates = [s['log_date'].strftime('%d-%b') for s in reversed(sleep_data[:10])]
        vals = [s['duration_hours'] for s in reversed(sleep_data[:10])]
        fig, ax = plt.subplots(figsize=(6, 3.2))
        sns.barplot(x=dates, y=vals, color='#7E57C2', ax=ax)
        ax.set_title('Sleep Duration Trend (hrs)')
        plt.xticks(rotation=30)
        charts['sleep'] = fig_to_base64(fig)

    if exercise_data:
        from collections import defaultdict
        cal_by_type = defaultdict(float)
        for e in exercise_data:
            cal_by_type[e['exercise_name']] += e['calories_burned']
        fig, ax = plt.subplots(figsize=(6, 3.2))
        ax.pie(list(cal_by_type.values()), labels=list(cal_by_type.keys()),
               autopct='%1.0f%%', colors=sns.color_palette('YlOrRd', len(cal_by_type)))
        ax.set_title('Calories Burned by Exercise Type')
        charts['exercise'] = fig_to_base64(fig)

    return render_template('reports.html', bmi_data=bmi_data, water_data=water_data,
                            weight_data=weight_data, sleep_data=sleep_data,
                            exercise_data=exercise_data, charts=charts)


# ----------------------------------------------------------------
# ERROR HANDLERS
# ----------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# ----------------------------------------------------------------
# RUN APPLICATION
# ----------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
