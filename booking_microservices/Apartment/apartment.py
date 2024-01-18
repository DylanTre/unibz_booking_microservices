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


#api: /add?name=onewtwosevethree&address=RockerfellerStreet&noiselevel=10&floor=2
@app.route('/add')
def add():
    name = request.args.get('name')
    address = request.args.get('address')
    noiselevel = request.args.get('noiselevel')
    floor = request.args.get('floor')

    #generate UUID for the given parameters
    id = uuid.uuid4()

    #add to database
    conn = sqlite3.connect('test.db')
    print ("Opened database successfully")

    conn.execute("INSERT INTO APARTMENTS (ID, NAME, ADDRESS, NOISE, FLOOR) VALUES (?, ?, ?, ?, ?)",
                 (str(id), name, address, noiselevel, floor))

    conn.commit()
    print ("Records created successfully")
    conn.close()

    postApartmentChange("add:"+str(id))


@app.route('/remove')
def remove():
    id = request.args.get('id')

    conn = sqlite3.connect('test.db')
    print ("Opened database successfully")
    conn.execute("DELETE FROM APARTMENTS WHERE ID = ?", (id,))
    conn.commit()
    print ("Record deleted successfully")
    conn.close()

    postApartmentChange("delete:"+str(id))


@app.route('/list', methods=['GET'])
def list():
    conn = sqlite3.connect('test.db')
    print ("Opened database successfully")
    cursor = conn.execute("SELECT * FROM APARTMENTS")
    rows = cursor.fetchall()
    apartments = [{'id': row[0], 'name': row[1], 'address': row[2], 'noiselevel': row[3], 'floor': row[4]} for row in rows]
    conn.close()
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
    conn.execute('''CREATE TABLE IF NOT EXISTS APARTMENTS
                  (ID TEXT PRIMARY KEY NOT NULL,
                   NAME TEXT NOT NULL,
                   ADDRESS TEXT NOT NULL,
                   NOISE INTEGER NOT NULL,
                   FLOOR INTEGER NOT NULL)''')

    conn.commit()



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    init()
    app.run(host="0.0.0.0", port=5000)
