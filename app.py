from flask import Flask, request, render_template, redirect, url_for, jsonify, flash, session  
import psycopg2
import psycopg2.extras


app = Flask(__name__)

#connection (change this based on your db)
db_config = {
    'dbname': 'TransportationEvents',
    'user': 'postgres',
    'password': 'shaheen1',
    'host': 'localhost',
    'port': '5432'
}

def time_to_seconds(time_str):
    hours, minutes = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60

@app.route('/', methods=['GET', 'POST'])
def create():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    person_id = request.args.get('personId')
    event_link_id = request.args.get('linkId')
    link_id_table = request.args.get('linkIdLinkTable')
    start_time = request.args.get('startTime')
    end_time = request.args.get('endTime')
    try:
        # Connect to your postgres DB
        conn = psycopg2.connect(**db_config)
        # Open a cursor to perform database operations
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        results_list = []

        if person_id:
            cur.execute("SELECT * FROM Events WHERE Person = %s ORDER BY Time ASC", (person_id,))
            results = cur.fetchall()
            results_list.extend([dict(event) for event in results])

        if event_link_id:
            # Check if start_time and end_time are provided
            if start_time and end_time:
                start_seconds = time_to_seconds(start_time)
                end_seconds = time_to_seconds(end_time)
                cur.execute(
                    "SELECT * FROM Events WHERE Link = %s AND Time BETWEEN %s AND %s ORDER BY Time ASC",
                    (event_link_id, start_seconds, end_seconds)
                )
            else:
                cur.execute("SELECT * FROM Events WHERE Link = %s ORDER BY Time ASC", (event_link_id,))
            results = cur.fetchall()
            results_list.extend([dict(event) for event in results])

        if link_id_table:
            cur.execute("SELECT * FROM Links WHERE LinkID = %s", (link_id_table,))
            results = cur.fetchall()
            results_list.extend([dict(link) for link in results])

        if not results_list:
            return jsonify({'error': 'Invalid or missing search parameters'}), 400

    except Exception as e:
        return jsonify({'error': 'Database operation failed', 'details': str(e)}), 500
    finally:
        # Close communication with the database if open
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return jsonify(results_list)

if __name__ == '__main__':
    app.run(debug=True)