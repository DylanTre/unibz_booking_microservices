from flask import Flask, jsonify, request
import threading
import pika
import requests
import sqlite3
import uuid
from pika.exchange_type import ExchangeType
import json

app = Flask(__name__)

debug = False

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
    conn = sqlite3.connect('test.db')
    print ("Opened database successfully")

    id = uuid.uuid4()

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
    if not debug:
        postBookingChange(jsonify(booking))
    else:
        return jsonify(booking)


#api: /cancel?id=123
@app.route('/cancel')
def cancel():
    id = request.args.get('id')
    print(id)
    conn = sqlite3.connect('test.db')
    conn.execute("DELETE FROM BOOKINGS WHERE ID = ?", (id,))
    conn.commit()
    conn.close()
    # entry to json
    booking = {
        'type': 'cancel',
        'id': id
    }
    if not debug:
        postBookingChange(jsonify(booking))
    else:
        return jsonify(booking)


#api: /change?id=d6727483-16fc-4fe4-bc7f-20dfb8d6a502&from=20240101&to=20240102
@app.route('/change')
def change():
    id = request.args.get('id')
    fromDate = request.args.get('from')
    toDate = request.args.get('to')
    conn = sqlite3.connect('test.db')
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
    if not debug:
        postBookingChange(jsonify(booking))
    else:
        return jsonify(booking)



@app.route('/list')
def list():
    # Connect to database
    conn = sqlite3.connect('test.db')
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

    return jsonify(bookings)


def postBookingChange(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.exchange_declare(exchange='booking', exchange_type=ExchangeType.fanout)
    channel.basic_publish(exchange='booking', routing_key='', body=message)
    print(f"sent message: {message}")
    connection.close()


def handleApartmentChange(ch, method, properties, body):
    # body is a json string
    print(f"received message: {body}")
    apartment = json.loads(body)
    if apartment['type'] == 'add':
        conn = sqlite3.connect('test.db')
        conn.execute("INSERT INTO APARTMENTS (ID) VALUES (?)", (apartment['id'],))
        conn.commit()
        conn.close()
    elif apartment['type'] == 'delete':
        conn = sqlite3.connect('test.db')
        conn.execute("DELETE FROM APARTMENTS WHERE ID = ?", (apartment['id'],))
        conn.commit()
        conn.close()
    else:
        print("unknown message")

def postBookingChange(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.exchange_declare(exchange='booking', exchange_type=ExchangeType.fanout)
    channel.basic_publish(exchange='booking', routing_key='', body=message)
    connection.close()

def listenForApartmentChanges():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.exchange_declare(exchange='apartment', exchange_type=ExchangeType.fanout)
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='apartment', queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=handleApartmentChange, auto_ack=True)
    channel.start_consuming()

def init():
    # Connect to database
    conn = sqlite3.connect('test.db')

    # Create table if not exists for apartments
    conn.execute('''CREATE TABLE IF NOT EXISTS APARTMENTS
                      (ID TEXT PRIMARY KEY NOT NULL)''')

    # Create table if not exists for bookings
    conn.execute('''CREATE TABLE IF NOT EXISTS BOOKINGS
                      (ID TEXT PRIMARY KEY NOT NULL,
                       APARTMENTID TEXT NOT NULL,
                       FROMDATE TEXT NOT NULL,
                       TODATE TEXT NOT NULL,
                       WHO TEXT NOT NULL)''')
    if not debug:
        apartmentjson = requests.get("http://apartment:5000/list").json()
        for apartment in apartmentjson:
            conn.execute("INSERT INTO APARTMENTS (ID) VALUES (?)", (apartment['id'],))


    # Commit changes
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init()
    if not debug:
        t = threading.Thread(target=listenForApartmentChanges)
        t.start()
        app.run(host="0.0.0.0", port=5000)
    else:
       app.run(host="0.0.0.0", port=5007)
