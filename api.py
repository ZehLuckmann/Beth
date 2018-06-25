#!flask/bin/python
#Example input:
#curl -i -H "Content-Type: application/json" -X POST -d '{"message":"Oi"}' http://localhost:5000/
from flask import Flask, request, abort
from beth import Bot
import json

app = Flask(__name__)
bot = Bot()

@app.route('/', methods=['POST'])
def get_reply():
    try:
        blob = request.get_json(force=True)
    except:
        abort(400)

    task = {
        'message': blob['message'],
        'reply' : "Fatal Error: No reply!",
        'success': False
    }

    try:
        task['reply'] = bot.get_reply(task['message'])
        task['success'] = True
    except Exception as e:
        task['reply'] = "FATAL ERROR: " + str(e)
        task['success'] = False

    print(task)
    return json.dumps(task)

if __name__ == '__main__':
    app.run(debug=False)
