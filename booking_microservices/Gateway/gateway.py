from flask import Flask, request
import requests

@app.route('/')
def home():
    return "hello! this is the API Gateway"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
