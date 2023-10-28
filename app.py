from flask import Flask, request, render_template, redirect, url_for, jsonify, flash, session  
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def create():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)