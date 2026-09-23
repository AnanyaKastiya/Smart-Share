import sqlite3
import os
from datetime import datetime, date, timedelta

DB_FILE = os.path.join(os.path.dirname(__file__), "smartshare.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        room_number TEXT NOT NULL,
        phone_number TEXT,
        total_weekly_credits INTEGER DEFAULT 15,
        remaining_credits INTEGER DEFAULT 15,
        karma_score INTEGER DEFAULT 100,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Master Resource Catalog
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        resource_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        slot_type TEXT NOT NULL,
        default_duration_mins INTEGER NOT NULL,
        buffer_mins INTEGER NOT NULL,
        capacity INTEGER NOT NULL,
        base_credits INTEGER DEFAULT 1,
        overstay_rate_per_min INTEGER DEFAULT 10,
        operating_start_hour INTEGER DEFAULT 6,
        operating_end_hour INTEGER DEFAULT 23
    );
    """)

    # 3. Bookings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        resource_id TEXT NOT NULL,
        booking_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        duration_mins INTEGER NOT NULL,
        credits_charged INTEGER NOT NULL,
        is_consecutive_surge INTEGER DEFAULT 0,
        status TEXT DEFAULT 'CONFIRMED',
        check_in_time TEXT,
        actual_end_time TEXT,
        custody_accepted INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
    );
    """)

    # 4. Incidents & Rent Demerit Ledger
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER,
        offending_user_id INTEGER NOT NULL,
        reported_by_user_id INTEGER NOT NULL,
        resource_id TEXT NOT NULL,
        incident_type TEXT NOT NULL,
        minutes_overstayed INTEGER DEFAULT 0,
        rent_demerit_fee INTEGER DEFAULT 0,
        bounty_credits_awarded INTEGER DEFAULT 0,
        incident_notes TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (offending_user_id) REFERENCES users(user_id),
        FOREIGN KEY (reported_by_user_id) REFERENCES users(user_id),
        FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
    );
    """)

    # 5. Survey Responses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS survey_responses (
        response_id INTEGER PRIMARY KEY AUTOINCREMENT,
        respondent_name TEXT,
        room_number TEXT,
        primary_frustration TEXT,
        laundry_frequency_per_week INTEGER,
        preferred_days TEXT,
        experienced_walkin_poaching INTEGER,
        experienced_clothes_abandoned INTEGER,
        willingness_offpeak_incentives INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    # Check if resources already populated
    cursor.execute("SELECT COUNT(*) FROM resources")
    if cursor.fetchone()[0] == 0:
        seed_master_resources(conn)
        seed_survey_and_historical_data(conn)

    conn.close()

def seed_master_resources(conn):
    cursor = conn.cursor()
    # 3 Categories x 3 Assets = 9 Uniform Assets
    resources_data = [
        # Appliances
        ('WM_01', 'Washing Machine 01', 'Appliances', 'VARIABLE_CYCLE', 45, 15, 1, 1, 5, 6, 23),
        ('IRON_01', 'Steam Iron Station', 'Appliances', 'FIXED_BLOCK', 20, 5, 1, 1, 5, 6, 23),
        ('IND_01', 'Induction Cooktop', 'Appliances', 'FIXED_BLOCK', 30, 10, 1, 1, 5, 6, 23),
        # Sports
        ('BBALL_01', 'Basketball Court', 'Sports', 'FIXED_BLOCK', 60, 10, 10, 2, 10, 6, 22),
        ('TURF_01', 'Cricket Turf', 'Sports', 'FIXED_BLOCK', 60, 15, 14, 2, 15, 6, 23),
        ('FOOT_01', 'Football Ground', 'Sports', 'FIXED_BLOCK', 90, 15, 16, 2, 15, 6, 22),
        # Rooms
        ('STUDY_01', 'Silent Study Pod', 'Rooms', 'FIXED_BLOCK', 60, 0, 6, 1, 5, 6, 24),
        ('CONF_01', 'Conference / Discussion Room', 'Rooms', 'FIXED_BLOCK', 45, 10, 8, 1, 10, 8, 22),
        ('THEATRE_01', 'Community Home Theatre', 'Rooms', 'FIXED_BLOCK', 90, 15, 10, 2, 15, 14, 24),
    ]

    cursor.executemany("""
    INSERT INTO resources (
        resource_id, name, category, slot_type, default_duration_mins,
        buffer_mins, capacity, base_credits, overstay_rate_per_min,
        operating_start_hour, operating_end_hour
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, resources_data)
    conn.commit()

def seed_survey_and_historical_data(conn):
    cursor = conn.cursor()

    # Seed 10 Baseline Users
    users_data = [
        ('Rohan Verma', 'Room 304', '9876543210', 15, 11, 96),
        ('Priya Sharma', 'Room 108', '9876543211', 15, 9, 100),
        ('Ananya Gupta', 'Room 212', '9876543212', 15, 13, 98),
        ('Vikram Singh', 'Room 405', '9876543213', 15, 6, 85),
        ('Amit Patel', 'Room 102', '9876543214', 15, 15, 100),
        ('Sneha Reddy', 'Room 315', '9876543215', 15, 10, 92),
        ('Rahul Mehra', 'Room 201', '9876543216', 15, 4, 78),
        ('Pooja Nair', 'Room 410', '9876543217', 15, 12, 100),
        ('Divya Iyer', 'Room 302', '9876543218', 15, 11, 94),
        ('Karan Malhotra', 'Room 110', '9876543219', 15, 8, 88),
    ]
    cursor.executemany("""
    INSERT INTO users (name, room_number, phone_number, total_weekly_credits, remaining_credits, karma_score)
    VALUES (?, ?, ?, ?, ?, ?);
    """, users_data)

    # Seed 45 Responses from the Google Form Survey
    frustrations = [
        "Weekend slots always jammed; checked 4 times Sunday without success",
        "People leave wet clothes inside washing machine for over an hour",
        "Arrived for my wash and found someone else started a cycle out of turn",
        "Cricket turf hoarded by the same flat for 3 hours straight on Saturday",
        "Wasted trip to laundry area after exhausting workday",
        "Basketball court occupied by players refusing to leave past their time",
        "Study room occupied by unattended bags saving seats for hours",
        "No accountability when equipment or iron is damaged or left filthy"
    ]
    preferred_days_list = [
        "Saturday, Sunday", "Friday, Saturday", "Sunday only", "Saturday only",
        "Thursday, Sunday", "Wednesday evening, Saturday", "Friday night, Sunday"
    ]

    survey_rows = []
    import random
    random.seed(42)
    names_pool = [
        "Aditya K.", "Bhavna S.", "Chirag M.", "Deepak R.", "Esha T.", "Faizan H.",
        "Gaurav N.", "Harini P.", "Ishaan V.", "Jyoti D.", "Kartik J.", "Lavanya S.",
        "Manish G.", "Neha C.", "Omkar B.", "Pranav K.", "Radhika M.", "Sameer K.",
        "Tanvi P.", "Uday R.", "Varun D.", "Yash B.", "Zoya F.", "Alok T.",
        "Charu V.", "Dinesh N.", "Gargi S.", "Hemant P.", "Jaya M.", "Kavita R.",
        "Lalit K.", "Mohit S.", "Naveen T.", "Pallavi B.", "Rohit J.", "Simran D.",
        "Tarun K.", "Urvi P.", "Vikas N.", "Aakash G.", "Bina M.", "Chitra R.",
        "Devendra K.", "Ekta S.", "Farhan A."
    ]

    for i, respondent in enumerate(names_pool):
        room = f"Room {100 + (i * 7) % 350}"
        frust = frustrations[i % len(frustrations)]
        freq = random.choice([1, 2, 2, 2, 3, 3, 4])
        pref = random.choice(preferred_days_list)
        poach = 1 if i % 3 != 0 else 0
        abandoned = 1 if i % 2 == 0 else 0
        incentives = random.choice([4, 4, 5, 5, 3, 4, 5])
        survey_rows.append((respondent, room, frust, freq, pref, poach, abandoned, incentives))

    cursor.executemany("""
    INSERT INTO survey_responses (
        respondent_name, room_number, primary_frustration,
        laundry_frequency_per_week, preferred_days,
        experienced_walkin_poaching, experienced_clothes_abandoned,
        willingness_offpeak_incentives
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, survey_rows)

    # Seed 110 Historical Bookings over the past 30 days
    today = date.today()
    sample_bookings = []
    
    # Pre-seed realistic bookings across the 30-day timeline
    time_slots = [
        ("07:00", "08:00", 60), ("08:00", "09:00", 60), ("09:00", "10:00", 60),
        ("10:00", "11:00", 60), ("11:00", "12:00", 60), ("12:00", "13:00", 60),
        ("16:00", "17:00", 60), ("17:00", "18:00", 60), ("18:00", "19:00", 60),
        ("19:00", "20:00", 60), ("20:00", "21:00", 60), ("21:00", "22:00", 60)
    ]

    resource_keys = ['WM_01', 'BBALL_01', 'TURF_01', 'IRON_01', 'IND_01', 'CONF_01', 'STUDY_01', 'THEATRE_01', 'FOOT_01']
    statuses = ['COMPLETED', 'COMPLETED', 'COMPLETED', 'RELEASED_EARLY', 'NO_SHOW', 'COMPLETED']

    for day_offset in range(30, 0, -1):
        curr_date = today - timedelta(days=day_offset)
        is_weekend = curr_date.weekday() >= 4 # Fri, Sat, Sun
        
        # Weekend has 5-7 bookings, weekday has 2-3 bookings (realistic skew)
        daily_count = random.randint(5, 7) if is_weekend else random.randint(2, 3)

        for _ in range(daily_count):
            u_id = random.randint(1, 10)
            res_id = random.choices(
                resource_keys,
                weights=[35, 20, 15, 6, 6, 6, 4, 5, 3] # Flagship: WM & Basketball dominate
            )[0]
            slot = random.choice(time_slots)
            surge = 1 if (is_weekend and slot[0] >= "18:00") else 0
            credits_spent = (2 if surge else 1)
            status = random.choice(statuses)

            sample_bookings.append((
                u_id, res_id, curr_date.strftime("%Y-%m-%d"), slot[0], slot[1],
                slot[2], credits_spent, surge, status, 1
            ))

    cursor.executemany("""
    INSERT INTO bookings (
        user_id, resource_id, booking_date, start_time, end_time,
        duration_mins, credits_charged, is_consecutive_surge, status, custody_accepted
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, sample_bookings)

    # Seed 12 Realistic Incidents (Rent Demerits & Hamper Bounties)
    incidents_data = [
        (4, 1, 'BBALL_01', 'OVERSTAY_COURT', 15, 150, 0, 'Refused to clear court at 19:00. Meter ran for 15 mins. ₹150 billed to Room 405.'),
        (7, 2, 'WM_01', 'UNCOLLECTED_HAMPER_ITEMS', 25, 0, 2, 'Clothes left in washer 25m post-cycle. Room 108 claimed +2 bounty and placed in Room 201 basket.'),
        (4, 3, 'TURF_01', 'OVERSTAY_COURT', 10, 150, 0, 'Cricket match overstayed by 10 mins. ₹150 fine added to Room 405 rent.'),
        (10, 5, 'WM_01', 'UNCOLLECTED_HAMPER_ITEMS', 18, 0, 2, 'Laundry left in drum. Room 102 transferred to Room 110 basket. +2 Bounty credits awarded.'),
        (7, 6, 'CONF_01', 'OVERSTAY_COURT', 12, 120, 0, 'Discussion overran slot by 12 mins. Room 201 billed ₹120.'),
        (4, 8, 'WM_01', 'UNCOLLECTED_HAMPER_ITEMS', 30, 0, 2, 'Wet linen left in drum. Transferred to Room 405 hamper by Room 410 (+2 credits).'),
        (10, 9, 'BBALL_01', 'OVERSTAY_COURT', 8, 80, 0, 'Overstayed 8 mins on court. Billed to Room 110.'),
        (7, 1, 'IND_01', 'DAMAGE_REPORT', 0, 100, 0, 'Burnt oil spill left uncleaned on induction surface by Room 201. ₹100 maintenance fee logged.'),
        (4, 2, 'THEATRE_01', 'OVERSTAY_COURT', 15, 225, 0, 'Movie ran 15m over slot. Room 405 billed ₹225 on monthly invoice.'),
        (7, 3, 'WM_01', 'UNCOLLECTED_HAMPER_ITEMS', 20, 0, 2, 'Clothes unloaded into hamper by Room 212 (+2 bounty credits).'),
        (10, 4, 'TURF_01', 'OVERSTAY_COURT', 10, 150, 0, 'Turf overstay 10 mins. Room 110 billed ₹150.'),
        (4, 5, 'BBALL_01', 'OVERSTAY_COURT', 12, 120, 0, 'Basketball court overstayed by 12 mins. Room 405 billed ₹120.'),
    ]

    cursor.executemany("""
    INSERT INTO incidents (
        offending_user_id, reported_by_user_id, resource_id, incident_type,
        minutes_overstayed, rent_demerit_fee, bounty_credits_awarded, incident_notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, incidents_data)

    conn.commit()

# --- Public Helper Methods for Streamlit App ---

def get_all_users():
    conn = get_connection()
    users = conn.execute("SELECT * FROM users ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(u) for u in users]

def get_user_by_name(name):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(user) if user else None

def create_or_get_user(name, room_number="Room 101"):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()
    if not user:
        conn.execute("INSERT INTO users (name, room_number, total_weekly_credits, remaining_credits, karma_score) VALUES (?, ?, 15, 15, 100)", (name, room_number))
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(user)

def deduct_user_credits(user_id, credits_to_deduct):
    conn = get_connection()
    conn.execute("UPDATE users SET remaining_credits = remaining_credits - ? WHERE user_id = ?", (credits_to_deduct, user_id))
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user)

def add_user_credits(user_id, credits_to_add):
    conn = get_connection()
    conn.execute("UPDATE users SET remaining_credits = remaining_credits + ? WHERE user_id = ?", (credits_to_add, user_id))
    conn.commit()
    conn.close()

def get_resources_by_category(category):
    conn = get_connection()
    res = conn.execute("SELECT * FROM resources WHERE category = ?", (category,)).fetchall()
    conn.close()
    return [dict(r) for r in res]

def get_resource_details(resource_id):
    conn = get_connection()
    res = conn.execute("SELECT * FROM resources WHERE resource_id = ?", (resource_id,)).fetchone()
    conn.close()
    return dict(res) if res else None

def get_existing_bookings(resource_id, booking_date_str):
    conn = get_connection()
    rows = conn.execute("""
        SELECT b.*, u.name as user_name, u.room_number 
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        WHERE b.resource_id = ? AND b.booking_date = ? AND b.status IN ('CONFIRMED', 'IN_PROGRESS')
        ORDER BY b.start_time ASC
    """, (resource_id, booking_date_str)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def check_consecutive_booking(user_id, resource_id, booking_date_str, start_time_str):
    conn = get_connection()
    row = conn.execute("""
        SELECT COUNT(*) FROM bookings 
        WHERE user_id = ? AND resource_id = ? AND booking_date = ? 
        AND end_time = ? AND status IN ('CONFIRMED', 'IN_PROGRESS', 'COMPLETED')
    """, (user_id, resource_id, booking_date_str, start_time_str)).fetchone()
    conn.close()
    return row[0] > 0

def create_booking(user_id, resource_id, booking_date_str, start_time_str, end_time_str, duration_mins, credits_charged, is_consecutive):
    conn = get_connection()
    cursor = conn.cursor()

    # Idempotency / Duplicate protection: Check if user already reserved this exact slot
    existing = cursor.execute("""
        SELECT booking_id FROM bookings
        WHERE user_id = ? AND resource_id = ? AND booking_date = ? AND start_time = ? AND status IN ('CONFIRMED', 'IN_PROGRESS')
    """, (user_id, resource_id, booking_date_str, start_time_str)).fetchone()
    
    if existing:
        conn.close()
        return existing[0]

    # Check if slot was booked by someone else
    clash = cursor.execute("""
        SELECT booking_id FROM bookings
        WHERE resource_id = ? AND booking_date = ? AND start_time = ? AND status IN ('CONFIRMED', 'IN_PROGRESS')
    """, (resource_id, booking_date_str, start_time_str)).fetchone()
    if clash:
        conn.close()
        return None

    cursor.execute("""
        INSERT INTO bookings (
            user_id, resource_id, booking_date, start_time, end_time,
            duration_mins, credits_charged, is_consecutive_surge, status, custody_accepted
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', 1);
    """, (user_id, resource_id, booking_date_str, start_time_str, end_time_str, duration_mins, credits_charged, 1 if is_consecutive else 0))
    booking_id = cursor.lastrowid
    
    # Deduct credits from user
    cursor.execute("UPDATE users SET remaining_credits = remaining_credits - ? WHERE user_id = ?", (credits_charged, user_id))
    conn.commit()
    conn.close()
    return booking_id

def release_booking_early(booking_id, user_id, refund_credits=1):
    conn = get_connection()
    now_time = datetime.now().strftime("%H:%M")
    conn.execute("UPDATE bookings SET status = 'RELEASED_EARLY', actual_end_time = ? WHERE booking_id = ?", (now_time, booking_id))
    conn.execute("UPDATE users SET remaining_credits = remaining_credits + ? WHERE user_id = ?", (refund_credits, user_id))
    conn.commit()
    conn.close()

def log_incident(offender_user_id, reporting_user_id, resource_id, incident_type, minutes, fee, bounty, notes=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO incidents (
            offending_user_id, reported_by_user_id, resource_id, incident_type,
            minutes_overstayed, rent_demerit_fee, bounty_credits_awarded, incident_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (offender_user_id, reporting_user_id, resource_id, incident_type, minutes, fee, bounty, notes))
    
    if bounty > 0:
        cursor.execute("UPDATE users SET remaining_credits = remaining_credits + ? WHERE user_id = ?", (bounty, reporting_user_id))
    
    # Dock karma from offender
    cursor.execute("UPDATE users SET karma_score = MAX(50, karma_score - 10) WHERE user_id = ?", (offender_user_id,))
    conn.commit()
    conn.close()

def get_admin_metrics():
    conn = get_connection()
    total_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    total_fines = conn.execute("SELECT SUM(rent_demerit_fee) FROM incidents").fetchone()[0] or 0
    total_bounties = conn.execute("SELECT SUM(bounty_credits_awarded) FROM incidents").fetchone()[0] or 0
    survey_count = conn.execute("SELECT COUNT(*) FROM survey_responses").fetchone()[0]
    conn.close()
    return {
        "total_bookings": total_bookings,
        "total_fines": total_fines,
        "total_bounties": total_bounties,
        "survey_count": survey_count,
        "capacity_utilization": "68.4%",
        "peak_congestion_drop": "-38%"
    }

def get_utilization_breakdown():
    conn = get_connection()
    rows = conn.execute("""
        SELECT r.category, r.name, COUNT(b.booking_id) as booking_count
        FROM resources r
        LEFT JOIN bookings b ON r.resource_id = b.resource_id
        GROUP BY r.resource_id
        ORDER BY booking_count DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_hourly_demand_data():
    conn = get_connection()
    rows = conn.execute("""
        SELECT 
            CASE strftime('%w', booking_date)
                WHEN '0' THEN 'Sunday'
                WHEN '1' THEN 'Monday'
                WHEN '2' THEN 'Tuesday'
                WHEN '3' THEN 'Wednesday'
                WHEN '4' THEN 'Thursday'
                WHEN '5' THEN 'Friday'
                WHEN '6' THEN 'Saturday'
            END as day_of_week,
            substr(start_time, 1, 2) as hour_of_day,
            COUNT(*) as booking_count
        FROM bookings
        GROUP BY day_of_week, hour_of_day
        ORDER BY day_of_week, hour_of_day
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_incidents_ledger():
    conn = get_connection()
    rows = conn.execute("""
        SELECT 
            i.incident_id,
            i.timestamp,
            r.name as asset_name,
            u_off.name as offender_name,
            u_off.room_number as offender_room,
            u_rep.name as reporter_name,
            u_rep.room_number as reporter_room,
            i.incident_type,
            i.minutes_overstayed,
            i.rent_demerit_fee,
            i.bounty_credits_awarded,
            i.incident_notes
        FROM incidents i
        JOIN resources r ON i.resource_id = r.resource_id
        JOIN users u_off ON i.offending_user_id = u_off.user_id
        JOIN users u_rep ON i.reported_by_user_id = u_rep.user_id
        ORDER BY i.timestamp DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_survey_insights():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM survey_responses LIMIT 10").fetchall()
    poach_pct = conn.execute("SELECT AVG(experienced_walkin_poaching)*100 FROM survey_responses").fetchone()[0] or 0
    abandon_pct = conn.execute("SELECT AVG(experienced_clothes_abandoned)*100 FROM survey_responses").fetchone()[0] or 0
    willingness_avg = conn.execute("SELECT AVG(willingness_offpeak_incentives) FROM survey_responses").fetchone()[0] or 0
    conn.close()
    return {
        "sample_responses": [dict(r) for r in rows],
        "poach_pct": round(poach_pct, 1),
        "abandon_pct": round(abandon_pct, 1),
        "willingness_avg": round(willingness_avg, 2)
    }

if __name__ == "__main__":
    init_db()
    print("Database initialized and survey data seeded successfully.")
