from flask import Flask, request
import requests


app = Flask(__name__)

# This service is a gateway for all the other services
@app.route('/')
def home():
    return "hello! this is the API Gateway"
@app.route('/apartment/add')
def addapartment():
    name = request.args.get('name')
    address = request.args.get('address')
    noiselevel = request.args.get('noiselevel')
    floor = request.args.get('floor')

    # Call apartment service
    response = requests.get('http://apartment:5000/add?name='+name+'&address='+address+'&noiselevel='+noiselevel+'&floor='+floor)
    return response.text

@app.route('/apartment/remove')
def removeapartment():
    id = request.args.get('id')

    # Call apartment service
    response = requests.get('http://apartment:5000/remove?id='+id)
    return response.text

@app.route('/apartment/list')
def listapartment():
    # Call apartment service
    response = requests.get('http://apartment:5000/list')
    return response.text

@app.route('/booking/add')
def addbooking():
    apartmentid = request.args.get('apartment')
    fromDate = request.args.get('from')
    toDate = request.args.get('to')
    who = request.args.get('who')

    # Call booking service
    response = requests.get('http://booking:5000/add?apartment='+apartmentid+'&from='+fromDate+'&to='+toDate+'&who='+who)
    return response.text

@app.route('/booking/cancel')
def cancelbooking():
    id = request.args.get('id')

    # Call booking service
    response = requests.get('http://booking:5000/cancel?id='+id)
    return response.text

@app.route('/booking/change')
def changebooking():
    id = request.args.get('id')
    fromDate = request.args.get('from')
    toDate = request.args.get('to')

    # Call booking service
    response = requests.get('http://booking:5000/change?id='+id+'&from='+fromDate+'&to='+toDate)
    return response.text

@app.route('/booking/list')
def listbooking():
    # Call booking service
    response = requests.get('http://booking:5000/list')
    return response.text

@app.route('/search/search')
def search():
    fromDate = request.args.get('from')
    toDate = request.args.get('to')

    # Call search service
    response = requests.get('http://search:5000/search?from='+fromDate+'&to='+toDate)
    return response.text


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
