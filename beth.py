#encoding: utf-8
import os
import time
from datetime import datetime
import os.path
import sqlite3
import operator
from textblob.classifiers import NaiveBayesClassifier
from textblob import TextBlob
from random import shuffle

class Processing(object):
    def __init__(self, token):
        self.token = token
        if not os.path.isfile(self.token + '.db'):
            self.create_database()

    def create_database(self):
        conn = sqlite3.connect(self.token + '.db')
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE action (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, input TEXT NOT NULL, output TEXT NOT NULL);")
        cursor.execute("CREATE TABLE history (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, date_time DATETIME NOT NULL,  message TEXT NOT NULL, reply TEXT NOT NULL);")
        conn.close()

    def load_actions(self):
        conn = sqlite3.connect(self.token + '.db')
        cursor = conn.cursor()
        cursor.execute("SELECT input, output FROM action;")

        actions = []
        for row in cursor.fetchall():
            actions.append([row[0], row[1]])
        conn.close()
        return actions

    def load_history(self):
        conn = sqlite3.connect(self.token + '.db')
        cursor = conn.cursor()
        cursor.execute("SELECT message, reply, date_time FROM history;")

        history = []
        for row in cursor.fetchall():
            history.append({"message" : row[0], "reply" : row[1], "date_time": row[2]})
        conn.close()
        return history

    def new_action(self, input, output):
        conn = sqlite3.connect(self.token + '.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO history (input, output) VALUES ('{0}', '{1}', '{2}')".format(date_time, message, reply))
        conn.commit()
        conn.close()

    def new_history(self, date_time, message, reply):
        conn = sqlite3.connect(self.token + '.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO history (date_time, message, reply) VALUES ('{0}', '{1}', '{2}')".format(date_time, message, reply))
        conn.commit()
        conn.close()

class Talk(object):

    def __init__(self):
        self.__cl = None
        self.__accuracy = 0

    def train(self, train_set):
        self.__cl = NaiveBayesClassifier(train_set)

    def test(self, test_set):
        self.__accuracy = self.__cl.accuracy(test_set)

    def reply(self, message):
        blob = TextBlob(message,classifier=self.__cl)
        reply = blob.classify()
        return reply

class Config(object):
    show_similarity = True

class Bot(object):
    history=[]
    name = "beth"
    processing = Processing(name)
    history = processing.load_history()
    config = Config()
    talk = Talk()
    
    def __init__(self):
        self.start_learn();

    def start_learn(self):
        dataset = self.processing.load_actions()
        shuffle(dataset)
        split_mark = int((len(dataset) * 30)/100)
        train_set = dataset[:split_mark]
        test_set = dataset[split_mark:]
        self.talk.train(train_set)
        self.talk.train(test_set)

    def get_reply(self, message):

        action = self.get_action(message)

        if 'C_GETLASTMESSAGE' in action:
            last = self.get_last_message()
            reply_message = action.replace('C_GETLASTMESSAGE', "Voce falou: \"{0}\" eu respondi \"{1}\" as {2}".format(last['message'], last['reply'], last['date_time']))
        elif 'C_CONFIG_SHOWSIMILARITY_TRUE' in action:
            self.config.show_similarity=True
            reply_message = action.replace('C_CONFIG_SHOWSIMILARITY_TRUE', "Configuracao alterada: Exibir os valores de similariedade dos resultados")
        elif 'C_CONFIG_SHOWSIMILARITY_FALSE' in action:
            self.config.show_similarity=False
            reply_message = action.replace('C_CONFIG_SHOWSIMILARITY_FALSE', "Configuracao alterada: Nao exibir os valores de similariedade dos resultados")
        else:
            reply_message = action

        self.set_history(message, reply_message)
        return reply_message


    def get_action(self, message):
        return self.talk.reply(message)

    def set_history(self, message, reply):
        self.history.append({"message" : message, "reply" : reply, "date_time" : datetime.now()})
        self.processing.new_history(datetime.now(), message, reply)

    def get_last_message(self):
        if len(self.history) > 1:
            return self.history[-1]
        else:
            return "Nao foi possivel consultar o historico"

def main():
    # Instance Bot
    sc = SlackClient(BOT_TOKEN)
    # Connect to slack
    if not sc.rtm_connect():
        raise Exception("Nao foi possivel conectar ao slack")

    bot = Bot()
    # Boot Loop
    loop = 0
    while True:
        loop += 1
        # Examine latest events
        for slack_event in sc.rtm_read():
            print("Novo Evento: ", slack_event.get('type'))
            # Ignora os eventos que não são mensagens
            if not slack_event.get('type') == "message":
                continue

            message = slack_event.get("text")
            user = slack_event.get("user")
            channel = slack_event.get("channel")

            if not message or not user:
                continue

            sc.api_call("chat.postMessage", channel=channel, text=bot.get_reply(message))

        # Sleep for half a second
        time.sleep(0.5)


if __name__ == '__main__':
    main()
