from flask import Flask, render_template, session, redirect, url_for
from flask_session import Session
from tempfile import mkdtemp

app = Flask(__name__)

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# First page that user sees.
@app.route("/")
def index():
    return render_template("start.html")

# The user has decided to play the game.
@app.route("/game")
def game():
    if "board" not in session:
        session["board"] = [[None, None, None], [None, None, None], [None, None, None]]
        session["turn"] = "X" 
    result = winner(session["board"])
    if(result[0] == True):
        return render_template("end.html", result = result[1])
    elif(result[0] == False):
        return render_template("draw.html", result = "It's a draw, play again!")
    # if(result == None):
    else:
        return render_template("game.html", game = session["board"], turn = session["turn"])


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
    return redirect(url_for("game")) 

# The user let computer make a move.
@app.route("/ComputerMove")
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


    


