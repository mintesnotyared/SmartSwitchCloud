from flask import Flask

app = Flask(name)

@app.route('/')
def home():
    return "Smart Switch Cloud is Live!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
