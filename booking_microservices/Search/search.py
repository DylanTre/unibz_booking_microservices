from flask import Flask, request, jsonify
import requests
import sqlite3
import pika
import threading
from pika.exchange_type import ExchangeType
import json

app = Flask(__name__)

_bookingExchange = 'booking'
_apartmentExchange = 'apartment'
_rabbitmqHost = 'rabbitmq'
_dbnmae = 'search.db'

def connect_to_db():
    return sqlite3.connect(_dbnmae)


@app.route('/')
def home():
    return "hello! this is the search service"

#api: /search?from=20200101&to=20200105
@app.route('/search', methods=['GET'])
def search():
    fromDate = request.args.get('from')
    toDate = request.args.get('to')
    conn = connect_to_db()
    print ("Opened database successfully")
    cursor = conn.execute("SELECT * FROM APARTMENTS WHERE ID NOT IN (SELECT APARTMENTID FROM BOOKINGS WHERE FROMDATE <= ? AND TODATE >= ?)", (fromDate, toDate))

    apartments = []
    for row in cursor:
        apartments.append({
            'id': row[0],
            'name': row[1],
            'address': row[2],
            'noise': row[3],
            'floor': row[4]
        })

    # Close connection
    conn.close()

    return jsonify(apartments)

@app.route('/debugapartments', methods=['GET'])
def debug():
    conn = connect_to_db()
    print ("Opened database successfully")
    cursor = conn.execute("SELECT * FROM APARTMENTS")
    rows = cursor.fetchall()
    apartments = [{'id': row[0], 'name': row[1], 'address': row[2], 'noiselevel': row[3], 'floor': row[4]} for row in rows]
    conn.close()
    return jsonify(apartments)

@app.route('/debugbookings', methods=['GET'])
def debug2():
    conn = connect_to_db()
    cursor = conn.execute("SELECT * FROM BOOKINGS")
    bookings = []
    for row in cursor:
        bookings.append({
            'id': row[0],
            'apartmentid': row[1],
            'from': row[2],
            'to': row[3],
            'who': row[4]
        })

    conn.close()
    return jsonify(bookings)

def handleApartmentChange(ch, method, properties, body):
    print(f"received message: {body}")
    apartment = json.loads(body)
    conn = connect_to_db()
    if apartment['type'] == 'add':
        conn.execute("INSERT INTO APARTMENTS (ID,NAME,ADDRESS,NOISE,FLOOR) VALUES (?,?,?,?,?)",
                     (apartment['id'], apartment['name'], apartment['address'], apartment['noiselevel'], apartment['floor']))
        conn.commit()
    elif apartment['type'] == 'delete':
        conn.execute("DELETE FROM APARTMENTS WHERE ID = ?", (apartment['id'],))
        conn.commit()
    else:
        print("unknown message")
    conn.close()

def handleBookingChange(ch, method, properties, body):
    print(f"received message: {body}")
    booking = json.loads(body)
    conn = connect_to_db()

    if booking['type'] == 'add':
        conn.execute("INSERT INTO BOOKINGS (ID,APARTMENTID,FROMDATE,TODATE,WHO) VALUES (?,?,?,?,?)", (booking['id'], booking['apartmentid'], booking['from'], booking['to'], booking['who']))
        conn.commit()
    elif booking['type'] == 'cancel':
        conn.execute("DELETE FROM BOOKINGS WHERE ID = ?", (booking['id'],))
        conn.commit()
    elif booking['type'] == 'change':
        conn.execute("UPDATE BOOKINGS SET FROMDATE = ?, TODATE = ? WHERE ID = ?", (booking['from'], booking['to'], booking['id']))
        conn.commit()
    else:
        print("unknown message")
    conn.close()


def listenForApartmentChanges():
    connection = pika.BlockingConnection(pika.ConnectionParameters(_rabbitmqHost))
    channel = connection.channel()
    channel.exchange_declare(exchange=_apartmentExchange, exchange_type=ExchangeType.fanout)
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=_apartmentExchange, queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=handleApartmentChange, auto_ack=True)
    channel.start_consuming()

def listenForBookingChanges():
    connection = pika.BlockingConnection(pika.ConnectionParameters(_rabbitmqHost))
    channel = connection.channel()
    channel.exchange_declare(exchange=_bookingExchange, exchange_type=ExchangeType.fanout)
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=_bookingExchange, queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=handleBookingChange, auto_ack=True)
    channel.start_consuming()

def init():
    conn = connect_to_db()

    conn.execute("DROP TABLE IF EXISTS BOOKINGS")
    conn.execute("DROP TABLE IF EXISTS APARTMENTS")
    conn.commit()

    conn.execute('''CREATE TABLE IF NOT EXISTS APARTMENTS
                  (ID TEXT PRIMARY KEY NOT NULL,
                   NAME TEXT NOT NULL,
                   ADDRESS TEXT NOT NULL,
                   NOISE INTEGER NOT NULL,
                   FLOOR INTEGER NOT NULL)''')

    conn.execute('''CREATE TABLE IF NOT EXISTS BOOKINGS
                  (ID TEXT PRIMARY KEY NOT NULL,
                   APARTMENTID TEXT NOT NULL,
                   FROMDATE TEXT NOT NULL,
                   TODATE TEXT NOT NULL,
                   WHO TEXT NOT NULL)''')

    conn.commit()
    conn.close()

    apartmentjson = requests.get('http://apartment:5000/list').json()
    conn = connect_to_db()

    for apartment in apartmentjson:
        conn.execute("INSERT INTO APARTMENTS (ID,NAME,ADDRESS,NOISE,FLOOR) VALUES (?,?,?,?,?)",
                     (apartment['id'], apartment['name'], apartment['address'], apartment['noiselevel'], apartment['floor']))
        conn.commit()

    bookingjson = requests.get('http://booking:5000/list').json()
    for booking in bookingjson:
        conn.execute("INSERT INTO BOOKINGS (ID,APARTMENTID,FROMDATE,TODATE,WHO) VALUES (?,?,?,?,?)", (booking['id'], booking['apartmentid'], booking['from'], booking['to'], booking['who']))
        conn.commit()

    conn.close()



if __name__ == '__main__':
    init()
    t1 = threading.Thread(target=listenForApartmentChanges)
    t1.start()

    t2 = threading.Thread(target=listenForBookingChanges)
    t2.start()

    app.run(host="0.0.0.0", port=5000)

