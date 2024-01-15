from flask import Flask, request, jsonify
import requests
import sqlite3

@app.route('/')
def home():
    return "hello! this is the search service"

@api.route('/search', methods=['GET'])
def search():
    fromDate = request.args.get('from')
    toDate = request.args.get('to')

    # Connect to database
    conn = sqlite3.connect('test.db')
    print ("Opened database successfully")

    # Execute query get all apartments available in the given time range
    cursor = conn.execute("SELECT * FROM APARTMENTS WHERE ID NOT IN (SELECT APARTMENTID FROM BOOKINGS WHERE FROMDATE <= ? AND TODATE >= ?)", (fromDate, toDate))

    # Create list of apartments
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


if __name__ == '__main__':
    app.run()
