from flask import Flask, jsonify, request
import threading
import pika
import requests
import sqlite3
import uuid
from pika.exchange_type import ExchangeType
import json

app = Flask(__name__)

_bookingExchange = 'booking'
_apartmentExchange = 'apartment'
_rabbitmqHost = 'rabbitmq'
_dbnmae = 'test.db'

def connect_to_db():
    return sqlite3.connect(_dbnmae)

@app.route('/')
def home():
    return "hello! this is the Booking service"

#api: /add?apartment=123&from=20200101&to=20200102&who=JohnShmit
@app.route('/add')
def add():
    apartmentid = request.args.get('apartment')
    fromDate = request.args.get('from')
    toDate = request.args.get('to')
    who = request.args.get('who')

    # Connect to database
    conn = connect_to_db()
    print ("Opened database successfully")

    id = str(uuid.uuid4())

    # Execute query
    conn.execute("INSERT INTO BOOKINGS (ID, APARTMENTID, FROMDATE, TODATE, WHO) VALUES (?, ?, ?, ?, ?)",
                 (str(id), apartmentid, fromDate, toDate, who))
    conn.commit()
    print ("Records created successfully")
    conn.close()

    # entry to json
    booking = {
        'type': 'add',
        'id': id,
        'apartmentid': apartmentid,
        'from': fromDate,
        'to': toDate,
        'who': who
    }

    postBookingChange(json.dumps(booking))
    return json.dumps(booking)


#api: /cancel?id=123
@app.route('/cancel')
def cancel():
    id = request.args.get('id')
    print(id)
    conn = connect_to_db()
    conn.execute("DELETE FROM BOOKINGS WHERE ID = ?", (id,))
    conn.commit()
    conn.close()
    # entry to json
    booking = {
        'type': 'cancel',
        'id': id
    }

    postBookingChange(json.dumps(booking))
    return json.dumps(booking)


#api: /change?id=d6727483-16fc-4fe4-bc7f-20dfb8d6a502&from=20240101&to=20240102
@app.route('/change')
def change():
    id = request.args.get('id')
    fromDate = request.args.get('from')
    toDate = request.args.get('to')
    conn = connect_to_db()
    conn.execute("UPDATE BOOKINGS SET FROMDATE = ?, TODATE = ? WHERE ID = ?", (fromDate, toDate, id))
    conn.commit()
    conn.close()

    # entry to json
    booking = {
        'type': 'change',
        'id': id,
        'from': fromDate,
        'to': toDate
    }
    postBookingChange(json.dumps(booking))
    return json.dumps(booking)



@app.route('/list')
def list():
    # Connect to database
    conn = connect_to_db()
    print ("Opened database successfully")

    # Execute query
    cursor = conn.execute("SELECT * FROM BOOKINGS")

    # Create list of bookings
    bookings = []
    for row in cursor:
        bookings.append({
            'id': row[0],
            'apartmentid': row[1],
            'from': row[2],
            'to': row[3],
            'who': row[4]
        })

    # Close connection
    conn.close()

    return json.dumps(bookings)


def handleApartmentChange(ch, method, properties, body):
    conn = connect_to_db()
    apartment = json.loads(body)
    if apartment['type'] == 'add':
        conn.execute("INSERT INTO APARTMENTS (ID) VALUES (?)", (apartment['id'],))
        conn.commit()
    elif apartment['type'] == 'delete':
        conn.execute("DELETE FROM APARTMENTS WHERE ID = ?", (apartment['id'],))
        conn.commit()
    else:
        print("unknown message")
    conn.close()

def postBookingChange(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(_rabbitmqHost))
    channel = connection.channel()
    channel.exchange_declare(exchange=_bookingExchange, exchange_type=ExchangeType.fanout)
    channel.basic_publish(exchange=_bookingExchange, routing_key='', body=message)
    connection.close()

def listenForApartmentChanges():
    connection = pika.BlockingConnection(pika.ConnectionParameters(_rabbitmqHost))
    channel = connection.channel()
    channel.exchange_declare(exchange=_apartmentExchange, exchange_type=ExchangeType.fanout)
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=_apartmentExchange, queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=handleApartmentChange, auto_ack=True)
    channel.start_consuming()

def init():
    conn = connect_to_db()

    conn.execute("DROP TABLE IF EXISTS APARTMENTS")
    conn.commit()

    conn.execute('''CREATE TABLE IF NOT EXISTS APARTMENTS
                      (ID TEXT PRIMARY KEY NOT NULL)''')

    conn.execute('''CREATE TABLE IF NOT EXISTS BOOKINGS
                      (ID TEXT PRIMARY KEY NOT NULL,
                       APARTMENTID TEXT NOT NULL,
                       FROMDATE TEXT NOT NULL,
                       TODATE TEXT NOT NULL,
                       WHO TEXT NOT NULL)''')

    apartmentjson = requests.get("http://apartment:5000/list").json()
    for apartment in apartmentjson:
        conn.execute("INSERT INTO APARTMENTS (ID) VALUES (?)", (apartment['id'],))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init()
    t = threading.Thread(target=listenForApartmentChanges)
    t.start()
    app.run(host="0.0.0.0", port=5000)
