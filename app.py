from flask import Flask, request, render_template, redirect, url_for, jsonify, flash, session  
import psycopg2


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



if __name__ == '__main__':
    app.run(debug=True)