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


@app.route('/', methods=['GET', 'POST'])
def create():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    person_id = request.args.get('personId')
    
    # Connect to your postgres DB
    conn = psycopg2.connect(**db_config)

    # Open a cursor to perform database operations
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Execute a query
    cur.execute("SELECT * FROM Events WHERE Person = %s ORDER BY Time ASC", (person_id,))

    # Retrieve query results
    events = cur.fetchall()

    # Close communication with the database
    cur.close()
    conn.close()

    # Convert the events to a list of dicts to jsonify
    events_list = [dict(event) for event in events]
    
    return jsonify(events_list)

if __name__ == '__main__':
    app.run(debug=True)