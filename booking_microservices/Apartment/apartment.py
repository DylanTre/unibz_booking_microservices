from flask import Flask, request, jsonify
import requests
import sqlite3
import pika
import uuid
import json
from pika.exchange_type import ExchangeType


app = Flask(__name__)

_apartmentExchange = 'apartment'
_rabbitmqHost = 'rabbitmq'
_dbnmae = 'search.db'

def connect_to_db():
    return sqlite3.connect(_dbnmae)

@app.route('/')
def home():
    return "hello! this is the apartment service"

#api: /add?name=1273a&address=RockerfellerStreet&noiselevel=10&floor=3
@app.route('/add')
def add():
    name = request.args.get('name')
    address = request.args.get('address')
    noiselevel = request.args.get('noiselevel')
    floor = request.args.get('floor')

    id = str(uuid.uuid4())

    conn = connect_to_db()
    conn.execute("INSERT INTO APARTMENTS (ID, NAME, ADDRESS, NOISE, FLOOR) VALUES (?, ?, ?, ?, ?)",
                 (str(id), name, address, noiselevel, floor))
    conn.commit()
    conn.close()

    apartment = {
        'type': 'add',
        'id': id,
        'name': name,
        'address': address,
        'noiselevel': noiselevel,
        'floor': floor
    }
    postApartmentChange(json.dumps(apartment))

    return "added: " + json.dumps(apartment)


@app.route('/remove')
def remove():
    id = request.args.get('id')
    conn = connect_to_db()
    conn.execute("DELETE FROM APARTMENTS WHERE ID = ?", (id,))
    conn.commit()
    conn.close()

    apartment = {
        'type': 'delete',
        'id': str(id)
    }

    postApartmentChange(json.dumps(apartment))
    return "deleted: " + str(id)

@app.route('/list', methods=['GET'])
def list():
    conn = connect_to_db()
    print ("Opened database successfully")
    cursor = conn.execute("SELECT * FROM APARTMENTS")
    rows = cursor.fetchall()
    apartments = [{'id': row[0], 'name': row[1], 'address': row[2], 'noiselevel': row[3], 'floor': row[4]} for row in rows]
    conn.close()
    return json.dumps(apartments)


def postApartmentChange(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(_rabbitmqHost))
    channel = connection.channel()
    channel.exchange_declare(exchange=_apartmentExchange, exchange_type=ExchangeType.fanout)
    channel.basic_publish(exchange=_apartmentExchange, routing_key='', body=message)
    print(f"sent message: {message}")
    connection.close()


def init():
    conn = connect_to_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS APARTMENTS
                  (ID TEXT PRIMARY KEY NOT NULL,
                   NAME TEXT NOT NULL,
                   ADDRESS TEXT NOT NULL,
                   NOISE INTEGER NOT NULL,
                   FLOOR INTEGER NOT NULL)''')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init()
    app.run(host="0.0.0.0", port=5000)

