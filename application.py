from flask import Flask, render_template, session, request, redirect, url_for
from flask_session import Session
from tempfile import mkdtemp
from flask_pymongo import PyMongo
import os
from bson import ObjectId
from datetime import datetime
import pymongo
import random

# Turn this file to web application
app = Flask(__name__)

# app.config["MONGO_URI"] = "mongodb://localhost:27017/newCS50"
app.config["MONGO_URI"] = "mongodb://avitalUsr:316331198@avital-shard-00-00.akkop.mongodb.net:27017,avital-shard-00-01.akkop.mongodb.net:27017,avital-shard-00-02.akkop.mongodb.net:27017/CS50TicTacToe?ssl=true&replicaSet=Avital-shard-0&authSource=admin&retryWrites=true&w=majority"

mongo = PyMongo(app)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app = Flask(__name__)
app.secret_key = "Piko Piko"


# First page that user sees.
@app.route("/")
def index():
    # Clean the cache for new game
    session.clear()
    return render_template("start.html")

# Multiplayer game:
@app.route("/createMultiplayer")
def createMultiplayer():
    xname = request.args.get('X')
    oname = request.args.get('O')
    dateFormat = '%Y-%m-%d %H:%M:%S.%f'
    currentTime = datetime.now().strftime(dateFormat)
    doc = { 
            "multiGame": True,
            "xname": xname,
            "oname": oname,
            "createdAt": currentTime,
            "XTurn": random.choice([True, False]),
            "board": [[None, None, None], [None, None, None], [None, None, None]]
        }

    record = mongo.db.players.insert_one(doc)
    objectId = record.inserted_id
    xLink = "/multiplayer?gameId=" + str(objectId) + "&player=X" 
    oLink = "/multiplayer?gameId=" + str(objectId) + "&player=O" 
    return render_template("/multiplayerLinks.html", xLink = xLink, xname = xname, oname = oname, oLink = oLink)


@app.route("/multiplayer") #/multiplayer?gameId=12bits&player=X
def multiplayer():
    gameId = request.args.get('gameId')
    player = request.args.get('player') # X or O

    document = mongo.db.players.find_one({"_id": ObjectId(gameId)})
    
    result = winner(document['board'])
    if(result[0] == True):
        if(result[1] == "X"):
            player_name = document["xname"]
        else:
            player_name = document["oname"]  
        
        dateFormat = '%Y-%m-%d %H:%M:%S.%f'
        deltaTime = str(datetime.now() - datetime.strptime(document["createdAt"], dateFormat))
        mongo.db.players.update_one({"_id": ObjectId(gameId)},{"$set": {"winner": player_name, "duration": deltaTime}})
        cursor = list(mongo.db.players.find({"winner": {"$exists": True}}).sort([("_id",pymongo.DESCENDING)]))
        return render_template("end.html", result = result[1], player_name = player_name, history = cursor)

    elif(result[0] == False):
        cursor = list(mongo.db.players.find({"winner": {"$exists": True}}))
        return render_template("draw.html", result = "It's a draw, play again!", history = cursor)

    else:
        if((document['XTurn'] == True and player == 'X') or (document['XTurn'] == False and player == 'O')):
            YouNeedToPlay = True  
        else:
            YouNeedToPlay = False

        if(document['XTurn'] == True):
            player_name = document['xname']
            player_who_need_to_play ='X'
        else:
            player_name = document['oname']
            player_who_need_to_play = 'O'

        if(player == 'X'):
            your_name = document['xname']
        else:
            your_name = document['oname']

        return render_template("multiplayer.html", gameId = gameId, player_who_need_to_play = player_who_need_to_play, board = document['board'], INeedToPlay = YouNeedToPlay, player_name = player_name, my_name = your_name)

# Where on the board I want to play the next move on multiplayer game.
@app.route("/playMultiplayer/<gameId>/<int:row>/<int:col>")
def playMultiplayer(gameId, row, col):
   
    document = mongo.db.players.find_one({"_id": ObjectId(gameId)})

    board = document['board']

    if(document['XTurn'] == True):
        player_type ='X'
    else:
        player_type = 'O'

    board[row][col] = player_type

    mongo.db.players.update_one({"_id": ObjectId(gameId)},{"$set": {"board": board, "XTurn": player_type == 'O'}})

    return redirect(url_for("multiplayer", gameId = gameId, player = player_type)) 


@app.route("/scores")
def scores():
    cursor = list(mongo.db.players.find({"winner": {"$exists": True}}).sort([("_id",pymongo.DESCENDING)]))
    return render_template("scores.html", history = cursor)

# Single player game:
@app.route("/game")
def game():
    xname = request.args.get('X')
    oname = request.args.get('O')

    if "board" not in session:

        # Database Saving:
        dateFormat = '%Y-%m-%d %H:%M:%S.%f'
        currentTime = datetime.now().strftime(dateFormat)
        doc = { 
            "xname": xname,
            "oname": oname,
            "createdAt": currentTime,
            "multiGame": False
            }

        record = mongo.db.players.insert_one(doc)
        objectId = record.inserted_id

        # Session Saving:
        session["board"] = [[None, None, None], [None, None, None], [None, None, None]]
        session["turn"] = "X" 
        session["xname"] = xname
        session["oname"] = oname
        session["gameId"] = str(objectId) 
        session["createdAt"] = currentTime

    xname = session["xname"]
    oname = session["oname"]
    result = winner(session["board"])

    if(result[0] == True):
        if(result[1] == "X"):
            player_name = session["xname"]
        else:
            player_name = session["oname"]  


        dateFormat = '%Y-%m-%d %H:%M:%S.%f'
        deltaTime = str(datetime.now() - datetime.strptime(session["createdAt"], dateFormat))

        gameId = session["gameId"]  
        objectId = ObjectId(gameId)   
        mongo.db.players.update_one({"_id": objectId},{"$set": {"winner": player_name, "duration": deltaTime}})
        cursor = list(mongo.db.players.find({"winner": {"$exists": True}}).sort([("_id",pymongo.DESCENDING)]))

        return render_template("end.html", result = result[1], player_name = player_name, history = cursor)
    elif(result[0] == False):
        
        cursor = list(mongo.db.players.find({"winner": {"$exists": True}}))

        return render_template("draw.html", result = "It's a draw, play again!", history = cursor)

    # if(result == None):
    else:
        if session["oname"] == "computer":
            if session["turn"] == "X":
                player = session["xname"]
            else: 
                player = session["oname"]
            return render_template("computer.html", game = session["board"], turn = session["turn"], xname=xname, oname=oname, player = player)
        else:
            return render_template("game.html", game = session["board"], turn = session["turn"], xname=xname, oname=oname)


# Where on the board I want to play the next move on single player game.
@app.route("/play/<int:row>/<int:col>")
def play(row, col):

    # Shows who playing now
    session["board"][row][col] = session["turn"]
    if session["turn"] == "X":
        session["turn"] = "O"
    else:
        session["turn"] = "X"
    #  redirect to a game function.
    return redirect(url_for("game", X = session["xname"], O = session["oname"])) 

# The user let computer makes a move.
@app.route("/computerMove")
def move():
    result = minmax(session["board"], session["turn"])
    if (result[1] != None):
        return redirect(url_for('play', row = result[1][0], col = result[1][1]))

    
# Reset game.
@app.route("/reset")
def init():
    session["board"] = [[None, None, None], [None, None, None], [None, None, None]]
    session["turn"] = "X"

    return redirect(url_for("game", X = session["xname"], O = session["oname"])) 

# A function that checks who the winner is.
def winner(board):

    #Checking the rows and columns.
    for i in range(3):
        if(board[i][0] == board[i][1] == board[i][2] != None):
            return [True, board[i][1]]
        if(board[0][i] == board[1][i] == board[2][i] != None):
            return [True, board[1][i]]
        
    #Checking the diagonals.
    j = 0
    if (board[j][j] == board[j+1][j+1] == board[j+2][j+2] != None):
        return [True, board[j][j]]
    if(board[j+2][j] == board[j+1][j+1] == board[j][j+2] != None):
        return [True, board[j][j+2]]

    # The game is not over yet
    for k in range(3):
        for l in range(3):
            if(board[k][l] == None):
                return[None, board[k][l]]
    # Draw
    return [False, board[0][0]]

# Function that makes the best move on the board,
#  if the user let computer makes a move.
def minmax(board, turn):

    # If the game is over.
    result = winner(board)
    if(result[0] == True):
        if(result[1] == "X"):
            return (1, None)
        else:
            return(-1, None)
        # Draw
    elif(result[0] == False):
        return (0, None)
    else: 
        # Available moves for the game.
        moves = []
        for i in range(3):
            for j in range(3):
                if(board[i][j] == None):
                    moves.append((i,j))
        # X want to maximize the score.
        if turn == "X":
            value = -100
            for i,j in moves:
                board[i][j] = "X"
                ans = minmax(board, "O")[0]
                if(value < ans):
                    value = ans
                    step = (i,j)
                board[i][j] = None
        else:
            # O want to minimize the score.
            value = 100
            for i,j in moves:
                board[i][j] = "O"
                ans = minmax(board, "X")[0]
                if(value > ans):
                    value = ans
                    step = (i,j)
                board[i][j] = None
        return (value, step)

if __name__ == '__main__':
    app.run(debug=True)

        # Mongo Documents Example:
        # {
        #     _id: ObjectId("12Digits"), -> Game Id
        #     xname: String,
        #     oname: String,
        #     winner: xname, # Field exists only if there a winner
        #     createdAt: Time # When the game started
        #     duration: Time # How much time did the game was

        #     Only for multGame:
        #     XTurn: Boolean # True/False 
        # }