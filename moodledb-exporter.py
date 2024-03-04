import os
import time
import mysql.connector
from prometheus_client import start_http_server, Gauge

# Environment variables for database configuration
HOST = os.getenv('DB_HOST', 'localhost')
USER = os.getenv('DB_USER', 'root')
PASSWORD = os.getenv('DB_PASSWORD', 'password')
DATABASE = os.getenv('DB_NAME', 'moodle')

# Additional configurations from environment variables
INTERVAL = int(os.getenv('SLEEP_INTERVAL', '60'))  # How often to fetch new data, in seconds
SERVER_PORT = int(os.getenv('SERVER_PORT', '8899'))  # Port for the Prometheus HTTP server

# Prometheus metrics setup
gauge_active = Gauge(
    'moodle_active_user_counter',
    'Counts active users of the last 5 minutes from Moodle database'
)
gauge_online = Gauge(
    'moodle_online_user_counter',
    'Counts online users of the last 5 minutes from Moodle database'
)
gauge_all = Gauge(
    'moodle_all_user_counter',
    'Counts all users from Moodle database'
)
gauge_db_size = Gauge(
    'moodle_db_size_counter',
    'Returns the size of Moodle database in MB'
)
gauge_enrolled_per_course = Gauge(
    'moodle_enrolled_per_course',
    'Number of users enrolled per course',
    ['courseid', 'coursename']
)
gauge_avg_time_on_site = Gauge(
    'moodle_avg_time_on_site',
    'Average time spent on site by users'
)
gauge_failed_logins = Gauge(
    'moodle_failed_logins',
    'Number of failed login attempts'
)
gauge_assignments_submitted = Gauge(
    'moodle_assignments_submitted',
    'Number of assignments submitted'
)
gauge_course_completion_rate = Gauge(
    'moodle_course_completion_rate',
    'Percentage of users who have completed the course',
    ['courseid', 'coursename']
)
gauge_quiz_attempts = Gauge(
    'moodle_quiz_attempts',
    'Number of attempts for each quiz',
    ['quizid']
)
gauge_quiz_success_rate = Gauge(
    'moodle_quiz_success_rate',
    'Success rate for each quiz',
    ['quizid']
)
gauge_certification_achievements = Gauge(
    'moodle_certification_achievements',
    'Number of certifications achieved',
    ['certificationid', 'certificationname']
)
gauge_grades_distribution = Gauge(
    'moodle_grades_distribution',
    'Average grade per course',
    ['courseid', 'coursename']
)
gauge_issued_badges = Gauge(
    'moodle_issued_badges',
    'Number of issued badges in Moodle',
    ['badge_name']
)

# Function to fetch and return metrics from the Moodle database.
def get_metrics(connection):
    cursor = connection.cursor()

    queries = {
        'active_users': (
            "SELECT COUNT(*) FROM mdl_user WHERE deleted=0 AND "
            "lastaccess > UNIX_TIMESTAMP(NOW() - INTERVAL 5 MINUTE);"
        ),
        'online_users': (
            "SELECT COUNT(*) FROM mdl_user WHERE "
            "lastaccess > UNIX_TIMESTAMP(NOW() - INTERVAL 5 MINUTE);"
        ),
        'all_users': (
            "SELECT COUNT(*) FROM mdl_user WHERE deleted=0;"
        ),
        'db_size': (
            f"SELECT SUM(data_length + index_length) / 1024 / 1024 "
            f"FROM information_schema.tables WHERE table_schema = '{DATABASE}';"
        ),
        'avg_time_on_site': (
            "SELECT AVG(lastaccess - firstaccess) FROM mdl_user WHERE "
            "lastaccess != 0 AND firstaccess != 0;"
        ),
        'failed_logins': (
            "SELECT COUNT(*) FROM mdl_logstore_standard_log WHERE "
            "action = 'login_failed';"
        ),
        'assignments_submitted': (
            "SELECT COUNT(*) FROM mdl_assign_submission WHERE status = 'submitted';"
        ),
        'enrolled_per_course': (
            "SELECT c.id AS courseid, c.fullname AS coursename, "
            "COUNT(ue.userid) AS enrolled_users "
            "FROM mdl_user_enrolments ue "
            "JOIN mdl_enrol e ON ue.enrolid = e.id "
            "JOIN mdl_course c ON e.courseid = c.id "
            "GROUP BY c.id, c.fullname;"
        ),
        'course_completion_rates': (
            "SELECT c.id, c.fullname, COUNT(cc.course) AS total_enrolled, "
            "SUM(CASE WHEN cc.timecompleted IS NOT NULL THEN 1 ELSE 0 END) "
            "AS total_completed "
            "FROM mdl_course c "
            "LEFT JOIN mdl_course_completions cc ON c.id = cc.course "
            "GROUP BY c.id;"
        ),
        'quiz_attempts_and_success': (
            "SELECT q.id, COUNT(qa.id) AS total_attempts, "
            "SUM(CASE WHEN qa.sumgrades >= q.grade THEN 1 ELSE 0 END) "
            "AS total_success "
            "FROM mdl_quiz q "
            "LEFT JOIN mdl_quiz_attempts qa ON q.id = qa.quiz "
            "WHERE qa.state = 'finished' "
            "GROUP BY q.id;"
        ),
        'certification_achievements': (
            "SELECT cert.id, cert.name, COUNT(certissue.id) AS total_issued "
            "FROM mdl_customcert cert "
            "LEFT JOIN mdl_customcert_issues certissue "
            "ON cert.id = certissue.customcertid "
            "GROUP BY cert.id;"
        ),
        'grades_distribution': (
            "SELECT c.id, c.fullname, AVG(gg.finalgrade) AS average_grade "
            "FROM mdl_course c "
            "JOIN mdl_grade_items gi ON c.id = gi.courseid AND gi.itemtype = 'course' "
            "JOIN mdl_grade_grades gg ON gi.id = gg.itemid "
            "WHERE gg.finalgrade IS NOT NULL "
            "GROUP BY c.id;"
        ),
        'issued_badges': (
            "SELECT b.name, COUNT(bi.id) FROM mdl_badge_issued bi "
            "INNER JOIN mdl_badge b ON bi.badgeid = b.id "
            "GROUP BY b.name;"
        )
    }

    results = {}

    # Execute each query and store the result in the results dictionary.
    for key, query in queries.items():
        cursor.execute(query)
        if key in [
            'enrolled_per_course', 'course_completion_rates',
            'quiz_attempts_and_success', 'certification_achievements',
            'grades_distribution', 'issued_badges'
        ]:
            results[key] = cursor.fetchall()
        else:
            results[key] = cursor.fetchone()[0]

    cursor.close()
    return results

# Main function where the program execution begins.
def main():
        # ASCII Art Banner
    ascii_art_banner = """
    __ __              _  _       ___  ___   __ __        _        _            ___                      _            
   |  \  \ ___  ___  _| || | ___ | . \| . > |  \  \ ___ _| |_ _ _ <_> ___  ___ | __>__   ___  ___  _ _ _| |_ ___  _ _ 
   |     |/ . \/ . \/ . || |/ ._>| | || . \ |     |/ ._> | | | '_>| |/ | '<_-< | _> \ \/| . \/ . \| '_> | | / ._>| '_>
   |_|_|_|\___/\___/\___||_|\___.|___/|___/ |_|_|_|\___. |_| |_|  |_|\_|_./__/ |___>/\_\|  _/\___/|_|   |_| \___.|_|  
                                                                                        |_|                                                  
    """
    print(ascii_art_banner, flush=True)                                                             

    start_http_server(SERVER_PORT)
    print(f"MoodleDB Metrics Exporter started. Listening on port:", SERVER_PORT, flush=True)

    # Establish a database connection and repeatedly fetch metrics at specified intervals.
    connection = mysql.connector.connect(
        host=HOST, user=USER, password=PASSWORD, database=DATABASE,
        autocommit=True, buffered=True, connection_timeout=5,
        sql_mode='STRICT_TRANS_TABLES'
    )

    try:
        # Set the READ COMMITTED isolation level after connecting
        cursor = connection.cursor()
        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        cursor.close()
    
        while True:
            metrics = get_metrics(connection)
            #print(metrics, flush=True) # debug
   
            # Update the Prometheus gauges with the fetched metrics.
            gauge_active.set(metrics['active_users'])
            gauge_online.set(metrics['online_users'])
            gauge_all.set(metrics['all_users'])
            gauge_db_size.set(metrics['db_size'])
            gauge_avg_time_on_site.set(metrics['avg_time_on_site'])
            gauge_failed_logins.set(metrics['failed_logins'])
            gauge_assignments_submitted.set(metrics['assignments_submitted'])

            # Special handling for the 'enrolled_per_course' metric that contains multiple records.
            for courseid, coursename, count in metrics['enrolled_per_course']:
                gauge_enrolled_per_course.labels(courseid=str(courseid), coursename=coursename).set(count)

            # For course completion rates:
            for course_id, course_name, total_enrolled, total_completed in metrics['course_completion_rates']:
                if total_enrolled > 0:
                    completion_rate = (total_completed / total_enrolled) * 100
                    gauge_course_completion_rate.labels(courseid=str(course_id), coursename=course_name).set(completion_rate)

            # For quiz attempts and success rates:
            for quiz_id, total_attempts, total_success in metrics['quiz_attempts_and_success']:
                gauge_quiz_attempts.labels(quizid=str(quiz_id)).set(total_attempts)
                if total_attempts > 0:
                    success_rate = (total_success / total_attempts) * 100
                    gauge_quiz_success_rate.labels(quizid=str(quiz_id)).set(success_rate)

            # For certification achievements:
            for certification_id, certification_name, total_issued in metrics['certification_achievements']:
                gauge_certification_achievements.labels(certificationid=str(certification_id), certificationname=certification_name).set(total_issued)

            # For grades distribution:
            for course_id, course_name, average_grade in metrics['grades_distribution']:
                if average_grade is not None:
                    gauge_grades_distribution.labels(courseid=str(course_id), coursename=course_name).set(average_grade)
        
            # For issued badges:
            for badge_name, badge_count in metrics['issued_badges']:
                    gauge_issued_badges.labels(badge_name=badge_name).set(badge_count)

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("Script interrupted by user. Exiting...", flush=True)

if __name__ == "__main__":
    main()