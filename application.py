from flask import Flask, render_template, session, request, redirect, url_for
from flask_session import Session
from tempfile import mkdtemp
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://avitalUsr:316331198@avital-shard-00-00.akkop.mongodb.net:27017,avital-shard-00-01.akkop.mongodb.net:27017,avital-shard-00-02.akkop.mongodb.net:27017/CS50TicTacToe?ssl=true&replicaSet=Avital-shard-0&authSource=admin&retryWrites=true&w=majority"
mongo = PyMongo(app)


app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.secret_key = "secret key"

# First page that user sees.
@app.route("/")
def index():
    return render_template("start.html")

# The user has decided to play the game.
@app.route("/game")
def game():
    xname = request.args.get('X')
    oname = request.args.get('O')

    if xname is None or oname is None:
        return render_template("start.html")


    if "board" not in session:
        print("Creating new game...")
        session["board"] = [[None, None, None], [None, None, None], [None, None, None]]
        session["turn"] = "X" 
        doc = { "xname": xname, "oname": oname }
        record = mongo.db.players.insert_one(doc)
        objectId = record.inserted_id
        session["objectId"] = objectId # The objectId saved in the session
        session["xname"] = xname
        session["oname"] = oname


    xname = session["xname"]
    oname = session["oname"]
    result = winner(session["board"])

    if(result[0] == True):
        if(result[1] == "X"):
            player_name = session["xname"]
        else:
            player_name = session["oname"]  

        objectId = session["objectId"]     
        mongo.db.players.update_one(
            {"_id": objectId}, # selector
            {"$set": {"winner": player_name }} # update
        )
        cursor = list(mongo.db.players.find({"winner": {"$exists": True}}))
        # Clean the cache for new game
        session.pop('board')

        return render_template("end.html", result = result[1], player_name = player_name, history = cursor)
    elif(result[0] == False):
        # Clean the cache for new game
        session.pop('board')

        return render_template("draw.html", result = "It's a draw, play again!", history = cursor)

    # if(result == None):
    else:
        return render_template("game.html", game = session["board"], turn = session["turn"], xname=xname, oname=oname)


# Where on the board I want to play the next move.
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

# The user let computer make a move.
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

    return redirect(url_for("game"))

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
