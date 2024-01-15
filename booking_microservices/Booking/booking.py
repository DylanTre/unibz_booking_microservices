from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/')
def home():
    return "hello! this is the Booking service"

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
    conn.execute("INSERT INTO BOOKINGS (ID, APARTMENTID, FROMDATE, TODATE, WHO) \
        VALUES ("+ id +", "+ apartmentid +", "+ fromDate +", "+ toDate +","+ who +" )");

    conn.commit()
    print ("Records created successfully")
    conn.close()


@app.route('/cancel')
def cancel():
    id = request.args.get('id')

    # Connect to database
    conn = sqlite3.connect('test.db')

    # Execute query
    conn.execute("DELETE FROM BOOKINGS WHERE ID = ?", (id))

    # Close connection
    conn.close()


@app.route('/change')
def change():
    id = request.args.get('id')
    fromDate = request.args.get('from')
    toDate = request.args.get('to')

    # Connect to database
    conn = sqlite3.connect('test.db')

    # Execute query
    conn.execute("UPDATE BOOKINGS SET FROMDATE = ?, TODATE = ? WHERE ID = ?", (fromDate, toDate, id))

    # Close connection
    conn.close()



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


if __name__ == '__main__':
    app.run()
