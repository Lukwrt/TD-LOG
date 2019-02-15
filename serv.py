from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO, send, emit

import random
import numpy as np
import time as time
from math import *
from generate_map import *

map, map_width, map_height, inner_slide = load_map("./static/map_alpha.png")
app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)

server_clock = time.clock()
last_update = server_clock
last_broadcast = time.clock()
last_bonus_respawn = server_clock

class bonus :
    def __init__(self):
        self.nb_bonus = 5
        self.bonus_list = ["heal", "boost"]
        self.bonus = {}
        for _ in range(self.nb_bonus):
            self.spawn_bonus()


    def spawn_bonus(self):
        id = generate_valid_id(self.bonus)
        x, y = random.randint(0, map_height - 1), random.randint(0, map_width - 1)
        while map[x, y]:
            x, y = random.randint(0, map_height - 1), random.randint(0, map_width - 1)
        type = self.bonus_list[random.randint(0, len(self.bonus_list) - 1)]
        self.bonus[id] = {'type': type, "x": y, "y": x}


class game(bonus):
    def __init__(self) :
        # Game objects
        self.players = {}
        self.bullets = {}
        self.teams = {"red": {"color": '#ff0000', "players_number": 0, 'spawn': [0, 0], 'score': 0},
                      "blue": {"color": '#0000ff', "players_number": 0, 'spawn': [map_height - 1, map_width - 1], 'score': 0}
                     }
        bonus.__init__(self)

        # Game Parameters :
        self.player_speed = 2
        self.bullet_speed = 6
        self.bigballRadius = 15
        self.smallballRadius = 3
        self.dead_radius = 6
        self.proc_distance = 20
        self.respawn_time = 5
        self.refreshing_time = 1 / 120


    def handle_shot(self,id, vx, vy):
        assert type(id)==int, "wrong id"
        bullet_id = generate_valid_id(self.bullets)
        self.bullets[bullet_id] = {"x": self.players[id]["x"], "y": self.players[id]["y"],
                          "vx": vx, "vy": vy,
                          "team": self.players[id]["team"],
                          "player_id": id}

    def test_handle_shot(self,id, vx, vy):
        assert type(id)==int, "wrong id"
        bullet_id = generate_valid_id(self.bullets)
        self.bullets[bullet_id] = {"x": self.players[id]["x"], "y": self.players[id]["y"],
                          "vx": vx, "vy": vy,
                          "team": self.players[id]["team"],
                          "player_id": id}
        return bullet_id

    def handle_new_connect(self):
        id = generate_valid_id(self.players)
        team_ = self.select_team()
        self.teams[team_]["players_number"] += 1
        print("Un joueur connecte, id : " + str(id), "team : " + team_)

        self.players[id] = {"x": self.teams[team_]["spawn"][1], "y": self.teams[team_]["spawn"][0],
                   "vx": 0, "vy": 0, "r": self.bigballRadius, "team": team_,
                   "pseudo": session['pseudo'], "score": 0,
                   "speed": self.player_speed}
        emit('authentification', {"id": id,
                              "map_width": map_width, "map_height": map_height})

    def test_create_id(self):
        id = generate_valid_id(self.players)
        team_ = self.select_team()
        self.teams[team_]["players_number"] += 1
        self.players[id] = {"x": self.teams[team_]["spawn"][1], "y": self.teams[team_]["spawn"][0],
                   "vx": 0, "vy": 0, "r": self.bigballRadius, "team": team_,
                   "pseudo": "None", "score": 0,
                   "speed": self.player_speed}
        return id

    def __getattr__(self,name):
        if name == 'bullets':
            return self.bullets
        if name == 'players':
            return self.players
        if name == 'teams':
            return self.teams
        if name == 'bonus':
            return self.bonus
        if name == 'refreshing_time':
            return self.refreshing_time



    def players_update(self):
        global server_clock, last_update, last_bonus_respawn
        server_clock = time.clock()
        bullets_to_pop = []
        players_to_pop = []
        bonus_to_pop = []

        if server_clock - last_bonus_respawn > self.respawn_time:
            self.spawn_bonus()
            last_bonus_respawn = server_clock
        for id in self.players:
            self.update_pos(id)
            for id_bonus in self.bonus:
                self.pick_bonus(id,id_bonus,bonus_to_pop)
        for id_bul in self.bullets:
            self.update_bullet(id_bul,bullets_to_pop)
            for id_play in self.players:
                self.collision(id_bul,id_play,bullets_to_pop)
                if self.players[id_play]["r"] < self.dead_radius:
                    self.death(id_play,id_bul,players_to_pop)

        for id in bullets_to_pop:
            self.bullets.pop(id, None)
        for id_bonus in bonus_to_pop:
            self.bonus.pop(id_bonus)

        for id in players_to_pop:
            self.teams[self.players[id]["team"]]["players_number"] -= 1
            self.players.pop(id, None)
            socketio.emit('dead', id, broadcast=True)
        last_update = server_clock


    def select_team(self):
        min_p, t_ = 1000, ''
        for t in self.teams:
            if self.teams[t]["players_number"] < min_p:
                t_ = t
                min_p = min(min_p, self.teams[t]["players_number"])
        return t_


    def update_pos(self,id):
        assert self.players[id]["r"] >= self.dead_radius,"player should be dead"
        assert (0 <= self.players[id]["x"] <= map_width) and (
                    0 <= self.players[id]["y"] <= map_height), "player out of map"
        assert map[int(self.players[id]["y"])][int(self.players[id]["x"])] == False, "player in obstacle"
        new_x = self.players[id]["x"] + self.players[id]["vx"] * (server_clock - last_update) * self.players[id]["speed"]
        new_y = self.players[id]["y"] + self.players[id]["vy"] * (server_clock - last_update) * self.players[id]["speed"]
        if (0 < new_y < map_height) and (0 < new_x < map_width):
            if map[int(new_y)][int(new_x)] == True:
                new_y, new_x = inner_slide(self.players[id]["y"], self.players[id]["x"], new_y, new_x)
        else:
            new_x = max(min(new_x, map_width-1), 0)
            new_y = max(min(new_y, map_height-1), 0)
        self.players[id]["x"] = new_x
        self.players[id]["y"] = new_y

    def pick_bonus(self,id,id_bonus,topop):
        assert id_bonus in self.bonus, "bonus does not exist"
        if (self.bonus[id_bonus]["x"] - self.players[id]["x"]) ** 2 + \
                (self.bonus[id_bonus]["y"] - self.players[id]["y"]) ** 2 <= \
                self.proc_distance ** 2:
            if self.bonus[id_bonus]["type"] == "heal":
                self.players[id]["r"] += 6
            if self.bonus[id_bonus]["type"] == "boost":
                self.players[id]["speed"] += 1
            topop.append(id_bonus)

    def update_bullet(self,id,topop):
        assert (0 <= self.bullets[id]["x"] <= map_width) and (0 <= self.bullets[id]["y"] <= map_height), "bullet out of map"
        assert map[int(self.bullets[id]["y"])][int(self.bullets[id]["x"])] == False, "bullet in obstacle"
        new_x = self.bullets[id]["x"] + self.bullets[id]["vx"] * (server_clock - last_update) * self.bullet_speed
        new_y = self.bullets[id]["y"] + self.bullets[id]["vy"] * (server_clock - last_update) * self.bullet_speed
        if (0 < new_y < map_height) and (0 < new_x < map_width) \
         and (map[int(new_y)][int(new_x)] == False):
            self.bullets[id]["x"] = new_x
            self.bullets[id]["y"] = new_y
        else:
            topop.append(id)

    def collision(self,id,idp,topop):
        assert (0 <= self.bullets[id]["x"] <= map_width) and (0 <= self.bullets[id]["y"] <= map_height), "bullet out of map"
        assert map[int(self.bullets[id]["y"])][int(self.bullets[id]["x"])] == False, "bullet in obstacle"
        if (self.players[idp]["team"] != self.bullets[id]["team"] and
                (self.players[idp]["x"] - self.bullets[id]["x"]) ** 2 +
                (self.players[idp]["y"] - self.bullets[id]["y"]) ** 2 <=
                (self.players[idp]["r"] + self.smallballRadius) ** 2):
            self.players[idp]["r"] -= 4
            topop.append(id)

    def death(self,idp,id,topop):
        '''
        >>> g = game()
        >>> idp = g.test_create_id()
        >>> id = g.test_handle_shot(idp,2,2)
        >>> old_score = g.teams[g.players[g.bullets[id]["player_id"]]["team"]]["score"]
        >>> g.death(432929229,id,[4562626])
        >>> g.teams[g.players[g.bullets[id]["player_id"]]["team"]]["score"] == old_score + 1
        True
        '''
        assert idp not in topop, "player already dead"
        topop.append(idp)
        self.teams[self.players[self.bullets[id]["player_id"]]["team"]]["score"] += 1
        self.players[self.bullets[id]["player_id"]]["score"] += 1
        socketio.emit('score_update',
                    {'score_red': self.teams['red']['score'],
                    'score_blue': self.teams['blue']['score']},
                    broadcast=True)

    def handle_movement(self, id, vx, vy):
        '''
        >>> g = game()
        >>> id_ = g.test_create_id()
        >>> g.handle_movement(id_,2,3)
        >>> g.players[id_]['vx'] == 2 and g.players[id_]['vy'] == 3
        True
        '''
        self.players[id]['vx'] = vx
        self.players[id]['vy'] = vy

## Short useful functions

#generate id
def generate_valid_id(dict):
    id = int(time.clock() * 10 ** 5)
    while str(id) in dict:
        id = int(time.clock() * 10 ** 5)
    return id



# returning a random color
def getRandomColor():
    letters = '0123456789ABCDEF'
    color = '#'
    for i in range(6):
        color += letters[int(np.floor(random.random() * 16))]
    return color


##Socketio functions


# defining the /game page by the file client.html
@app.route('/game')
def index():
    return render_template('client.html')


# definign the login page by the file login.html
@app.route('/login', methods=['GET', 'POST'])
def login():
    # session is a cookie saving the pseudo of the player
    # if pseudo is known, the player is redirected to the game
    if 'pseudo' in session:
        return redirect('/game')

    # the pseudo is not known
    else:
        # the formulary of login page has been sent
        if request.method == 'POST':
            # the player want to save his session for a month
            if (str(request.form['result']) == 'Oui'):
                session['pseudo'] = str(request.form['ps'])
                session.permanent = True
            # the player doesn't want to save his session
            else:
                print("test")
                session['pseudo'] = str(request.form['ps'])
            # redirecting the player to the game
            return redirect('/game')

        # the formulary has not been sent, we return the login page
        else:
            return render_template('login.html')

@app.route('/end_game', methods=['GET', 'POST'])
def players_dead():
    # if the player click on the button then he his redirected to the game
    if request.method == 'POST':
        return redirect('/game')
    # the player has not clicked
    else:
        return render_template('end_game.html')


@socketio.on('new_connection')
def handle_new_connection():
    game_session.handle_new_connect()

@socketio.on('client_shoot')
def handle_shoot(id, vx, vy):
    game_session.handle_shot(id, vx, vy)

@socketio.on('client_speed_update')
def handle_move(id, vx, vy):
    game_session.handle_movement(id, vx, vy)

@socketio.on('logout')
def handle_logout():
    return redirect('/end_game')

@socketio.on('request_frame')
def handle_request_frame():
    global last_broadcast
    if time.clock() - last_broadcast > game_session.refreshing_time:
        game_session.players_update()
        socketio.emit('update', {"players": game_session.players, "bullets": game_session.bullets, "bonus": game_session.bonus}, broadcast=True)
        last_broadcast = time.clock()


if __name__ == '__main__':
    #print("map size : ", map_width, map_height, " : ", map_width * map_height)
    #game_session = game()
    import doctest
    doctest.testmod()
    #socketio.run(app, host='127.0.0.1', port = 5000)
