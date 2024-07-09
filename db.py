import sqlite3


def init_db():
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Intake INTEGER,
        Surgery INTEGER,
        Bed_A INTEGER,
        Bed_B INTEGER,
        ER INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Queue_Surgery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        diagnosis TEXT,
        status TEXT,
        callback_url TEXT,
        duration REAL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Queue_Nursing_A (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        diagnosis TEXT,
        status TEXT,
        callback_url TEXT,
        duration REAL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Queue_Nursing_B (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        diagnosis TEXT,
        status TEXT,
        callback_url TEXT,
        duration REAL
    )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Queue_ER (
            patient_id TEXT,
            callback_url TEXT,
            duration REAL
        )
    ''')

    cursor.execute("INSERT INTO Resources (Intake, Surgery, Bed_A, Bed_B, ER) VALUES (4, 5, 30, 40, 9)")
    conn.commit()
    conn.close()


def update_resource(resource, count):
    """
    Update the resource with new count.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE Resources SET {resource} = ? WHERE id = 1", (count,))
    conn.commit()
    conn.close()


def get_resource(resource):
    """
    Get resource count.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT {resource} FROM Resources WHERE id = 1")
    result = cursor.fetchone()[0]
    conn.close()
    return result


def add_to_queue(queue_type, patient_id, diagnosis, status, callback_url):
    """
    Add a patient to the queue, ER patient has priority.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()

    if queue_type == 'Queue_Surgery':
        cursor.execute(
            "INSERT INTO Queue_Surgery (patient_id, diagnosis, status, callback_url, duration) VALUES (?, ?, ?,?,?)",
            (patient_id, diagnosis, status, callback_url, 0))
        conn.commit()

        if status == 'ER Treatment finished':
            cursor.execute(
                "SELECT patient_id, diagnosis, status, callback_url, duration FROM Queue_Surgery ORDER BY CASE WHEN status = 'ER Treatment finished' THEN 1 ELSE 2 END, id")
            sorted_queue = cursor.fetchall()
            cursor.execute("DELETE FROM Queue_Surgery")
            for patient in sorted_queue:
                cursor.execute(
                    "INSERT INTO Queue_Surgery (patient_id, diagnosis, status, callback_url, duration) VALUES (?, ?, ?, ?, ?)",
                    (patient[0], patient[1], patient[2], patient[3], patient[4]))
        conn.commit()
        conn.close()

    if queue_type == 'Queue_Nursing_A':
        cursor.execute(
            "INSERT INTO Queue_Nursing_A (patient_id, diagnosis, status, callback_url, duration) VALUES (?, ?, ?, ?,?)",
            (patient_id, diagnosis, status, callback_url, 0))
        conn.commit()

        if status == 'ER Treatment finished':
            cursor.execute(
                "SELECT patient_id, diagnosis, status, callback_url, duration FROM Queue_Nursing_A ORDER BY CASE WHEN status = 'ER Treatment finished' THEN 1 ELSE 2 END, id")
            sorted_queue = cursor.fetchall()
            cursor.execute("DELETE FROM Queue_Nursing_A")
            for patient in sorted_queue:
                cursor.execute(
                    "INSERT INTO Queue_Nursing_A (patient_id, diagnosis, status, callback_url, duration) VALUES (?, ?, ?, ?,?)",
                    (patient[0], patient[1], patient[2], patient[3], patient[4]))
        conn.commit()
        conn.close()

    if queue_type == 'Queue_Nursing_B':
        cursor.execute(
            "INSERT INTO Queue_Nursing_B (patient_id, diagnosis, status, callback_url, duration) VALUES (?, ?, ?, ?,?)",
            (patient_id, diagnosis, status, callback_url, 0))
        conn.commit()

        if status == 'ER Treatment finished':
            cursor.execute(
                "SELECT patient_id, diagnosis, status, callback_url, duration FROM Queue_Nursing_B ORDER BY CASE WHEN status = 'ER Treatment finished' THEN 1 ELSE 2 END, id")
            sorted_queue = cursor.fetchall()
            cursor.execute("DELETE FROM Queue_Nursing_B")
            for patient in sorted_queue:
                cursor.execute(
                    "INSERT INTO Queue_Nursing_B (patient_id, diagnosis, status, callback_url, duration) VALUES (?, ?, ?, ?,?)",
                    (patient[0], patient[1], patient[2], patient[3], patient[4]))
        conn.commit()
        conn.close()


def get_count_queue(queue_type, status):
    """
    Count patient in the queue according to given status.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()

    if queue_type == 'Queue_Surgery':
        cursor.execute("SELECT COUNT(*) FROM Queue_Surgery WHERE status = ?", (status,))
    if queue_type == 'Queue_Nursing_A':
        cursor.execute("SELECT COUNT(*) FROM Queue_Nursing_A WHERE status = ?", (status,))
    if queue_type == 'Queue_Nursing_B':
        cursor.execute("SELECT COUNT(*) FROM Queue_Nursing_A WHERE status = ?", (status,))

    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_queue(queue_type):
    """
    Get the queue.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()

    if queue_type == 'Queue_Surgery':
        cursor.execute("SELECT patient_id, diagnosis, status, callback_url, duration FROM Queue_Surgery")
    if queue_type == 'Queue_Nursing_A':
        cursor.execute("SELECT patient_id, diagnosis, status, callback_url, duration FROM Queue_Nursing_A")
    if queue_type == 'Queue_Nursing_B':
        cursor.execute("SELECT patient_id, diagnosis, status, callback_url, duration FROM Queue_Nursing_B")

    queue = cursor.fetchall()
    conn.close()
    return queue


def delete_from_queue(queue_type, callback_url):
    """
    Delete a patient from the queue.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()

    if queue_type == 'Queue_Surgery':
        cursor.execute("DELETE FROM Queue_Surgery WHERE callback_url = ?", (callback_url,))
    if queue_type == 'Queue_Nursing_A':
        cursor.execute("DELETE FROM Queue_Nursing_A WHERE callback_url = ?", (callback_url,))
    if queue_type == 'Queue_Nursing_B':
        cursor.execute("DELETE FROM Queue_Nursing_B WHERE callback_url = ?", (callback_url,))
    conn.commit()
    conn.close()


def update_queue(queue_type, callback_url, duration):
    """
    Update a patient's record in the Queue.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()
    if queue_type == 'Queue_Surgery':
        cursor.execute('''
                    UPDATE Queue_Surgery
                    SET duration = ?
                    WHERE callback_url = ?
                ''', (duration, callback_url))
    if queue_type == 'Queue_Nursing_A':
        cursor.execute('''
                    UPDATE Queue_Nursing_A
                    SET duration = ?
                    WHERE callback_url = ?
                ''', (duration, callback_url))
    if queue_type == 'Queue_Nursing_A':
        cursor.execute('''
                    UPDATE Queue_Nursing_B
                    SET duration = ?
                    WHERE callback_url = ?
                ''', (duration, callback_url))
    conn.commit()
    conn.close()


def add_to_queue_er(patient_id, callback_url):
    """
    Add a patient to queue er.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Queue_ER (patient_id, callback_url, duration) VALUES (?, ?, ?)", (patient_id, callback_url, 0))
    conn.commit()
    conn.close()


def delete_from_queue_er(callback_url):
    """
    Delete a patient from the queue er.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM Queue_ER WHERE callback_url = ?", (callback_url,))
    conn.commit()
    conn.close()


def get_queue_er():
    """
    Get the queue er.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()
    cursor.execute("SELECT patient_id, callback_url, duration FROM Queue_ER")
    queue = cursor.fetchall()
    conn.close()
    return queue
    # Close the connection


def update_queue_er(callback_url, duration):
    """
    Update a patient's record in the Queue_ER table.
    """
    conn = sqlite3.connect('hospital_resources.db')
    cursor = conn.cursor()
    cursor.execute('''
                UPDATE Queue_ER
                SET duration = ?
                WHERE callback_url = ?
            ''', (duration, callback_url))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()

