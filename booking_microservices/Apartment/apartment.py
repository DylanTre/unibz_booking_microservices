from flask import Flask, request, jsonify
import requests
import sqlite3
import pika
import uuid
import json

app = Flask(__name__)


@app.route('/')
def home():
    return "hello! this is the apartment service"


#api: /add?name=(string)&address=(string)&noiselevel=(number)&floor=(number)
@app.route('/add')
def add():
    name = request.args.get('name')
    address = request.args.get('address')
    noiselevel = request.args.get('noiselevel')
    floor = request.args.get('floor')

    #generate UUID
    id = uuid.uuid4()

    #add to database
    conn = sqlite3.connect('test.db')
    print ("Opened database successfully")

    conn.execute("INSERT INTO APARTMENTS (ID,NAME,ADDRESS,NOISE,FLOOR) \
        VALUES ("+ id +", "+ name +", "+ address +", "+ noiselevel +","+ floor +" )");

    conn.commit()
    print ("Records created successfully")
    conn.close()

    postApartmentChange("add:"+id)


@app.route('/remove')
def remove():
    id = request.args.get('id')

    # Remove from database
    conn = sqlite3.connect('test.db')
    print ("Opened database successfully")

    conn.execute("DELETE FROM APARTMENTS WHERE ID = ?", (id,))

    conn.commit()
    print ("Record deleted successfully")
    conn.close()

    postApartmentChange("delete:"+id)


@app.route('/list', methods=['GET'])
def list():
    # Connect to database
    conn = sqlite3.connect('test.db')
    print ("Opened database successfully")
    # Execute query
    cursor = conn.execute("SELECT * FROM APARTMENTS")
    # Fetch all rows
    rows = cursor.fetchall()
    # Convert rows to list of dictionaries for JSON serialization
    apartments = [{'id': row[0], 'name': row[1], 'address': row[2], 'noiselevel': row[3], 'floor': row[4]} for row in rows]
    # Close connection
    conn.close()
    # Return JSON response
    return jsonify(apartments)


def postApartmentChange(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.exchange_declare(exchange='apartment', exchange_type=ExchangeType.fanout)
    channel.basic_publish(exchange='apartment', routing_key='', body=message)
    print(f"sent message: {message}")
    connection.close()


def init():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS APARTMENTS
                  (ID TEXT PRIMARY KEY NOT NULL,
                   NAME TEXT NOT NULL,
                   ADDRESS TEXT NOT NULL,
                   NOISE INTEGER NOT NULL,
                   FLOOR INTEGER NOT NULL)''')

    cursor.commit()
    cursor.close()



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    init()
    app.run(host="0.0.0.0", port=5000)
