
from database.db import get_db_connection, get_dict_cursor
from datetime import date, timedelta
import random

STUDENT_ID = 1
CLASS_ID = 1
SECTION_ID = 1

conn = get_db_connection()
cur = get_dict_cursor(conn)

# Subjects
cur.execute("SELECT id, name FROM subjects WHERE class_id = %s", (CLASS_ID,))
subjects = cur.fetchall()
if len(subjects) < 3:
    for sub_name in ['Mathematics', 'English', 'Science']:
        cur.execute(
            "INSERT INTO subjects (name, code, class_id) VALUES (%s, %s, %s)",
            (sub_name, sub_name[:3].upper(), CLASS_ID)
        )
    conn.commit()
    cur.execute("SELECT id, name FROM subjects WHERE class_id = %s", (CLASS_ID,))
    subjects = cur.fetchall()

sub_ids = {s['name']: s['id'] for s in subjects}
print("Subjects:", list(sub_ids.keys()))

# Teacher
cur.execute("SELECT id FROM teachers LIMIT 1")
teacher = cur.fetchone()
if not teacher:
    cur.execute("INSERT INTO users (full_name, email, password, role) VALUES (%s, %s, %s, %s) RETURNING id",
                ('Mrs. Khan', 'teacher@test.com', 'test123', 'teacher'))
    t_user_id = cur.fetchone()['id']
    cur.execute("INSERT INTO teachers (user_id, qualification) VALUES (%s, %s) RETURNING id",
                (t_user_id, 'M.Sc Mathematics'))
    teacher_id = cur.fetchone()['id']
    conn.commit()
else:
    teacher_id = teacher['id']

print("Teacher ID:", teacher_id)

# Attendance
cur.execute("DELETE FROM attendance WHERE student_id = %s", (STUDENT_ID,))
present = 0
for i in range(30):
    day = date.today() - timedelta(days=i)
    if day.weekday() == 6:
        continue
    status = 'present' if random.random() > 0.1 else 'absent'
    if status == 'present':
        present += 1
    cur.execute("INSERT INTO attendance (student_id, date, status, marked_by) VALUES (%s, %s, %s, %s)",
                (STUDENT_ID, day, status, teacher_id))
conn.commit()
print("Attendance done:", present, "present days")

# Exams + Results
cur.execute("DELETE FROM results WHERE student_id = %s", (STUDENT_ID,))
exam_data = [
    ('Mid-Term Exam', 100, date.today() - timedelta(days=45)),
    ('Quiz 1', 20, date.today() - timedelta(days=20)),
    ('Final Exam', 100, date.today() - timedelta(days=5)),
]
for sub_name in ['Mathematics', 'English', 'Science']:
    sub_id = sub_ids.get(sub_name)
    if not sub_id:
        continue
    for exam_name, total, exam_date in exam_data:
        cur.execute("INSERT INTO exam (name, class_id, subject_id, exam_date, total_marks, passing_marks) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (exam_name, CLASS_ID, sub_id, exam_date, total, int(total * 0.4)))
        exam_id = cur.fetchone()['id']
        marks = round(total * random.uniform(0.75, 0.95), 1)
        pct = (marks / total) * 100
        grade = 'A+' if pct >= 90 else 'A' if pct >= 80 else 'B' if pct >= 70 else 'C'
        cur.execute("INSERT INTO results (student_id, exam_id, subject_id, marks_obtained, grade, remarks) VALUES (%s, %s, %s, %s, %s, %s)",
                    (STUDENT_ID, exam_id, sub_id, marks, grade, 'Good work!'))
conn.commit()
print("Exams + Results done")

# Homework
cur.execute("DELETE FROM homework WHERE student_id = %s", (STUDENT_ID,))
hw = [
    ('Algebra Exercise 5.1', 'Solve questions 1-10 from page 45', 7),
    ('English Essay', 'Write 200 words on My Favorite Season', 5),
    ('Science Project', 'Draw and label parts of a plant cell', 10),
    ('Math Quiz Prep', 'Revise multiplication tables 1-15', 3),
    ('Reading Assignment', 'Read chapter 3 and answer questions', 4),
]
for title, desc, days in hw:
    sub_id = sub_ids.get(random.choice(['Mathematics', 'English', 'Science']))
    cur.execute("INSERT INTO homework (student_id, subject_id, teacher_id, title, description, deadline) VALUES (%s, %s, %s, %s, %s, %s)",
                (STUDENT_ID, sub_id, teacher_id, title, desc, date.today() + timedelta(days=days)))
conn.commit()
print("Homework done")

# Assignments
cur.execute("DELETE FROM assignment WHERE student_id = %s", (STUDENT_ID,))
asg = [
    ('Math Assignment 1', 'Complete worksheet on fractions', 6),
    ('English Creative Writing', 'Write a short story', 8),
    ('Science Lab Report', 'Write report on experiment', 4),
]
for title, desc, days in asg:
    sub_id = sub_ids.get(random.choice(['Mathematics', 'English', 'Science']))
    cur.execute("INSERT INTO assignment (student_id, subject_id, teacher_id, title, description, deadline) VALUES (%s, %s, %s, %s, %s, %s)",
                (STUDENT_ID, sub_id, teacher_id, title, desc, date.today() + timedelta(days=days)))
conn.commit()
print("Assignments done")

# Fees
cur.execute("DELETE FROM fee_payment WHERE student_id = %s", (STUDENT_ID,))
cur.execute("INSERT INTO fee_payment (student_id, monthly_fee, yearly_fee, amount, payment_date, payment_mod) VALUES (%s, %s, %s, %s, %s, %s)",
            (STUDENT_ID, 5000, 60000, 5000, date.today() - timedelta(days=60), 'cash'))
cur.execute("INSERT INTO fee_payment (student_id, monthly_fee, yearly_fee, amount, payment_date, payment_mod) VALUES (%s, %s, %s, %s, %s, %s)",
            (STUDENT_ID, 5000, 60000, 5000, date.today() - timedelta(days=30), 'online'))
conn.commit()
print("Fees done")

# Notices
cur.execute("DELETE FROM notice_board WHERE class_id = %s", (CLASS_ID,))
for title, context in [
    ('PTM Next Week', 'Parent-Teacher Meeting on Friday 3pm.'),
    ('Sports Day', 'Annual Sports Day on 25th. Students wear sports uniform.'),
    ('Exam Schedule', 'Final exams start next Monday.'),
]:
    cur.execute("INSERT INTO notice_board (title, context, class_id, section_id, posted_by, is_active) VALUES (%s, %s, %s, %s, %s, TRUE)",
                (title, context, CLASS_ID, SECTION_ID, teacher_id))
conn.commit()
print("Notices done")

# Timetable
cur.execute("DELETE FROM timetable WHERE class_id = %s AND section_id = %s", (CLASS_ID, SECTION_ID))
days_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
periods = [('08:00', '09:00'), ('09:00', '10:00'), ('10:15', '11:15'), ('11:15', '12:15')]
for day in days_list:
    for i, (start, end) in enumerate(periods):
        sub_name = ['Mathematics', 'English', 'Science', 'Mathematics'][i]
        sub_id = sub_ids.get(sub_name)
        cur.execute("INSERT INTO timetable (class_id, section_id, subject_id, teacher_id, day_of_week, start_time, end_time) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (CLASS_ID, SECTION_ID, sub_id, teacher_id, day, start, end))
conn.commit()
print("Timetable done")

# Study Material
cur.execute("DELETE FROM study_material WHERE class_id = %s", (CLASS_ID,))
for title, desc in [
    ('Chapter 5 Notes', 'Complete notes on Algebra'),
    ('English Grammar Guide', 'Tenses, articles, prepositions'),
    ('Science Diagrams', 'Important diagrams for exam'),
]:
    sub_id = sub_ids.get(random.choice(['Mathematics', 'English', 'Science']))
    cur.execute("INSERT INTO study_material (class_id, subject_id, section_id, teacher_id, title, description, file_path) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (CLASS_ID, sub_id, SECTION_ID, teacher_id, title, desc, '/uploads/sample.pdf'))
conn.commit()
print("Study material done")

conn.close()
print()
print("=" * 50)
print("SAARA TEST DATA ADD HO GAYA!")
print("=" * 50)
