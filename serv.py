
# -*- coding: utf-8 -*-

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

test = int(input("effectuer les tests ? (oui : 1/ non :0) :"))

class bonus :
    def __init__(self):
        self.nb_bonus = 5
        self.bonus_list = ["heal", "boost"]
        self.bonus = {}
        for _ in range(self.nb_bonus):
            self.spawn_bonus()


    def spawn_bonus(self):
        """
        fait spawner un bonus de type aleatoire dans une location aleatoire
        """
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
        self.player_speed = 2 # vitesse de base des joueurs
        self.bullet_speed = 6 # vitesse des projectiles
        self.bigballRadius = 15 # rayon (vie) de base des joueurs
        self.smallballRadius = 3 # rayon des projectiles
        self.dead_radius = 6 # rayon en deca duquel le joueur meurt
        self.proc_distance = 20 # distance de declenchement des bonus
        self.respawn_time = 5 # temps de respawn des bonus (en secondes)
        self.refreshing_time = 1 / 120 # temps de raffraichissement du serveur


    def handle_shot(self,id, vx, vy):
        """
        gere le tire du joueur identifie par id, dont le curseur est positionne en (vx,vy)
        """
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
        """
        gere la connection d'un nouveau joueur au serveur :
        creer un nouvel id, affile le joueur a une equipe et renvoie au joueur les info relatives au terrain
        """
        id = generate_valid_id(self.players)
        team_ = self.select_team()
        self.teams[team_]["players_number"] += 1
        print("Un joueur connecte, id : " + str(id), "team : " + team_)
        self.create_player(id,team_)
        emit('authentification', {"id": id,
                              "map_width": map_width, "map_height": map_height})

    def create_player(self,id,team_):
        '''Si on effectue des tests, on a besoin que le pseudo ne dépende pas du cookie
        '''
        if test==0:
            self.players[id] = {"x": self.teams[team_]["spawn"][1], "y": self.teams[team_]["spawn"][0],
                        "vx": 0, "vy": 0, "r": self.bigballRadius, "team": team_,
                        "pseudo": session['pseudo'], "score": 0,
                        "speed": self.player_speed}
        if test==1:
            self.players[id] = {"x": self.teams[team_]["spawn"][1], "y": self.teams[team_]["spawn"][0],
                        "vx": 0, "vy": 0, "r": self.bigballRadius, "team": team_,
                        "pseudo": "test_pseudo", "score": 0,
                        "speed": self.player_speed}

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
        if name == "bigballRadius":
            return self.bigballRadius



    def players_update(self):
        """
        calcule la frame suivante du jeu, le delta de temps est calcule avec le temps actuel
        et le temps auquel a eu lieu la derniere udpate
        """
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
            if test==0:
                socketio.emit('dead', id, broadcast=True)
        last_update = server_clock


    def select_team(self):
        """
        selectionne la team dans lequel sera affilie le prochain joueur
        la regle est que c'est la team qui a le moins de joueur actif qui est prioritaire
        """
        min_p, t_ = 1000, ''
        for t in self.teams:
            if self.teams[t]["players_number"] < min_p:
                t_ = t
                min_p = min(min_p, self.teams[t]["players_number"])
        return t_


    def update_pos(self,id):
        """
        fait evoluer la position du joueur identifie par id

        >>> g = game()
        >>> id = g.test_create_id()
        >>> g.players[id]["r"] >= g.dead_radius
        True
        >>> 0 <= g.players[id]["x"] <= map_width
        True
        >>> 0 <= g.players[id]["y"] <= map_height
        True
        >>> map[int(g.players[id]["y"])][int(g.players[id]["x"])] == False
        True
        >>> g.update_pos(id)
        >>> new_x = g.players[id]["x"] + g.players[id]["vx"] * (server_clock - last_update) * g.players[id]["speed"]
        >>> new_y = g.players[id]["y"] + g.players[id]["vy"] * (server_clock - last_update) * g.players[id]["speed"]
        >>> new_x == max(min(new_x, map_width-1), 0)
        True
        """

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
        '''
        >>> g = game()
        >>> id_ = g.test_create_id()
        >>> oldradius = g.players[id_]["r"]
        >>> idbonus = generate_valid_id(g.bonus)
        >>> g.bonus[idbonus]={'type': "heal", "x": 0, "y": 0}
        >>> g.pick_bonus(id_,idbonus,[])
        >>> g.bigballRadius == 15
        True
        '''

        """
        si le joueur reference par id est a proximite du bonus reference par id_bonus,
        le bonus est declenche sur le joeur.
        si le bonus est declenche, le bonus est retire du jeu, d'ou la presence de topop,
        qui est la liste des id des bonus a supprimer a la frame suivante
         (topop est donc passe dynamiquement en argument)
        """
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
        '''
        fait evoluer la position de la balle identifie par id
        si la balle rencontre un element (joueur, obstacle) elle disparait et est ajoute a topop


        >>> g = game()
        >>> idp = g.test_create_id()
        >>> id = g.test_handle_shot(idp,25,25)
        >>> g.update_bullet(id,[-1])
        >>> 0 <= g.bullets[id]["x"] <= map_width
        True
        >>> 0 <= g.bullets[id]["y"] <= map_height
        True
        >>> new_x = g.bullets[id]["x"] + g.bullets[id]["vx"] * (server_clock - last_update) * g.bullet_speed
        >>> new_y = g.bullets[id]["y"] + g.bullets[id]["vy"] * (server_clock - last_update) * g.bullet_speed
        >>> g.bullets[id]["x"] == new_x
        True
        >>> g.bullets[id]["y"] == new_y
        True
        '''
        new_x = self.bullets[id]["x"] + self.bullets[id]["vx"] * (server_clock - last_update) * self.bullet_speed
        new_y = self.bullets[id]["y"] + self.bullets[id]["vy"] * (server_clock - last_update) * self.bullet_speed
        if (0 < new_y < map_height) and (0 < new_x < map_width) \
         and (map[int(new_y)][int(new_x)] == False):
            self.bullets[id]["x"] = new_x
            self.bullets[id]["y"] = new_y
        else:
            topop.append(id)

    def collision(self,id,idp,topop):
        '''
        verifie si une collision a lieu entre la balle (id) et le joueur (idp)
        si oui, applique les consequences.
        :param id: id de la balle
        :param idp: id du joueur
        :param topop: liste de balle a supprimer
        :return:
        >>> g = game()
        >>> idp = g.test_create_id()
        >>> id = g.test_handle_shot(idp,2,2)
        >>> g.collision(id,idp,[-1])
        >>> 0 <= g.bullets[id]["x"] <= map_width
        True
        >>> 0 <= g.bullets[id]["y"] <= map_height
        True
        '''
        if (self.players[idp]["team"] != self.bullets[id]["team"] and
                (self.players[idp]["x"] - self.bullets[id]["x"]) ** 2 +
                (self.players[idp]["y"] - self.bullets[id]["y"]) ** 2 <=
                (self.players[idp]["r"] + self.smallballRadius) ** 2):
            self.players[idp]["r"] -= 4
            topop.append(id)

    def death(self,idp,id,topop):
        '''
        gere la mort du joueur (idp) par la balle (id),
        modifie les scores en consequences

        :param idp: id joueur
        :param id: id balle
        :param topop: liste de joueur qui sont deja mort a cette frame

        >>> g = game()
        >>> idp = g.test_create_id()
        >>> id = g.test_handle_shot(idp,2,2)
        >>> old_score = g.teams[g.players[g.bullets[id]["player_id"]]["team"]]["score"]
        >>> g.death(432929229,id,[4562626])
        >>> g.teams[g.players[g.bullets[id]["player_id"]]["team"]]["score"] == old_score + 1
        True
        '''
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

### Short useful functions

#generate id

def generate_valid_id(dict):
    """
    :param dict: un dictionnaire dont les cles sont des entiers
    :return: une id qui n'est pas une cle deja reference dans le dictionnaire
    """
    id = int(time.clock() * 10 ** 5)
    while str(id) in dict:
        id = int(time.clock() * 10 ** 5)
    assert type(id)==int,"wrong id"
    assert id>=0, "negative id"
    return id


# returning a random color
def getRandomColor():
    letters = '0123456789ABCDEF'
    color = '#'
    for i in range(6):
        color += letters[int(np.floor(random.random() * 16))]
    return color

### Socketio functions

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

##Testing


import doctest
import unittest
from hypothesis import given
import hypothesis.strategies as strats
import time
import random
class Test_game(unittest.TestCase):
    def _test_id(self,id,string,x):
        dictio={id:{string:x}}
        try:
            generate_valid_id(dictio)
            return 1
        except AssertionError:
            return 0
    @given(id=strats.integers(),string=strats.text(),x=strats.floats())
    def test_id(self,id,string,x):
        self.assertEqual(self._test_id(id,string,x), 1)
    def _test_owl_game(self,G,id,vx,vy):
        r=random.randint(1,2)
        try:
            if r==1:
                G.handle_movement(id, vx, vy)
            if r==2:
                G.handle_shot(id, vx, vy)
        except AssertionError:
            return 0
        return 1
    @given(N1=strats.integers(),N2=strats.integers(),vx=strats.floats(),vy=strats.floats())
    def test_owl_game(self,N1,N2,vx,vy):
        G=game()
        N1 = N1%10+1
        for i in range(N1):
            id = generate_valid_id(G.players)
            team_ = G.select_team()
            G.create_player(id,team_)
        N2=N2%100
        for i in range(N2):
            id = random.choice(list(G.players.keys()))
            self.assertEqual(self._test_owl_game(G,id,vx,vy),1)
            

## running game


if __name__ == '__main__':

    if test == 1:
        doctest.testmod()
        unittest.main()
    elif test ==0:
        print("map size : ", map_width, map_height, " : ", map_width * map_height)
        game_session = game()
        socketio.run(app, host='127.0.0.1', port = 5000)
