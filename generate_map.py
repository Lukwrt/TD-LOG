
# -*- coding: utf-8 -*-

import matplotlib.image as mpimg
import numpy as np
import matplotlib.pyplot as plt
import pprint as pp

def get(l, k):
    """

    :param l: liste
    :param k: position
    :return: l element de l à la position k mod n, ou n est la longueur de la liste
    permet d acceder au element d'une liste en les voyant comme des boucles
    """
    n = len(l)
    return l[k % n]

def assert_closed_curve (l):
    """
    :param l: une liste de postion successives
    :return: True si l est une courbe fermee
    >>> l = [(0,0),(1,1),(2,1),(2,0),(1,0)]
    >>> assert_closed_curve(l)
    True
    """
    ans = True
    for k in range(len(l)):
        p1, p2 = get(l,k), get(l,k+1)
        ans = (abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) <= 2)
    return ans

def get_contour(map):
    """
    :param map: une matrice de booleens
    :return: une liste de contours, un contours etant une liste de pixel formant continuement un contour. \
    l'ordre est donc fondamental dans ces listes. chaque contours est repere par sa position dans la liste en sortie
    de la fonction
    """
    height, width = map.shape[0], map.shape[1]
    c_map = np.zeros((height, width)) # la matrice qui indique la presence d'un contour par un 1

    for i in range(1, height - 1):
        for j in range(1, width - 1):
            if not (map[i, j]) and (np.abs(map[i, j] ^ map[i + 1, j]) +
                                    np.abs(map[i, j] ^ map[i - 1, j]) +
                                    np.abs(map[i, j] ^ map[i, j + 1]) +
                                    np.abs(map[i, j] ^ map[i, j - 1])) >= 1:
                c_map[i, j] = 1

    def search_one():
        """
        :return: la position d'un pixel faisant partie d'un contour
        les positions des elements de contours explores deviennent des 0 dans c_map
        """
        b = True
        i, j = 0, 0
        while i < height - 1 and b:
            i += 1
            j = 0
            while j < width - 1 and b:
                b = (c_map[i, j] == 0)
                j += 1
        if (i, j) == (height - 1, width - 1):
            return False, i, j
        else:
            return True, i, j

    def search_next(i, j):
        """
        :param i: hauteur
        :param j: largeur
        :return: la position de l'element de contour contigu au pixel i,j -- si cet element n'existe pas, renvoie -1,-1
        """
        if c_map[i + 1, j] >= 1:
            return True, i + 1, j
        elif c_map[i - 1, j] >= 1:
            return True, i - 1, j
        elif c_map[i, j + 1] >= 1:
            return True, i, j + 1
        elif c_map[i, j - 1] >= 1:
            return True, i, j - 1
        elif c_map[i + 1, j + 1] >= 1:
            return True, i + 1, j + 1
        elif c_map[i + 1, j - 1] >= 1:
            return True, i + 1, j - 1
        elif c_map[i - 1, j + 1] >= 1:
            return True, i - 1, j + 1
        elif c_map[i - 1, j - 1] >= 1:
            return True, i - 1, j - 1

        else:
            return False, -1, -1

    b, i, j = search_one()
    contours = []

    while b:
        contours.append([(i, j)])
        sb = True
        while sb:
            c_map[i, j] = 0
            sb, i, j = search_next(i, j)
            if sb:
                contours[-1].append((i, j))

        b, i, j = search_one()
    ### on retire les contours qui semblent aberrant
    contours = [x for x in contours if len(x) > 2]

    return contours



def compute_tangeante(map, contours, bw=5):
    """
    :param map: map de booleen
    :param contours: liste des differents contours
    :param bw: bande passante pour le calcul de la tangeante (permet de lisser le calul)
    :return: une matrice tanj_map avec la valeur de la pente de la tangeante pour \
     chaque position de la map, on attribut 0 aux postions ne faisant pas partie d'un contour
     associe height*width comme pente de la tangeante lorsque la pente est infinie
    """
    height, width = map.shape[0], map.shape[1]
    tanj_map = np.zeros((height, width))
    for c in contours:
        for k in range(len(c)):
            if (get(c, k - bw)[0] - get(c, k + bw)[0]) == 0:
                tanj_map[c[k][0], c[k][1]] = height * width
            else:
                tanj_map[c[k][0], c[k][1]] = (get(c, k - bw)[1] - get(c, k + bw)[1]) / (
                        get(c, k - bw)[0] - get(c, k + bw)[0])
    return tanj_map

def dist(x,y,x_,y_):
    return (x-x_)**2+(y-y_)**2

def compute_nearest_border(map, contours, b=3):
    """
    :param map: map booleènne
    :param contours: contours de la map
    :param b: on calcule seulement pour les pixels etant à distance au maximum b d'un contour
    :return: une matice, avec pour chaque pixel proche d'un contour, l'id de ce contour (relativement
    à l'objet contour ) et la position de l'element de conteur dont il est le plus proche. affecte la valeur -1,-1
    si le coutour le plus proche de la position en question est plus loin que la distance b+1

    >>> int_map = np.array([[0,0,0,0],[0,1,1,0],[0,1,0,0],[0,0,0,0]]).astype(int)
    >>> bool_map = (-1*map+1).astype(bool)
    >>> contours = get_contour(bool_map)
    >>> NNmap = compute_nearest_border(int_map,contours,b=2)
    >>> pp.pprint(bool_map)
    array([[ True,  True,  True,  True],
       [ True, False, False,  True],
       [ True, False,  True,  True],
       [ True,  True,  True,  True]])
    >>> pp.pprint(contours)
    [[(1, 2), (1, 1), (2, 1)]]
    >>> pp.pprint(NNmap[:,:,1])
    array([[ 1,  1,  0,  0],
       [ 1,  1,  0,  0],
       [ 2,  2,  2,  0],
       [ 2,  2,  2, -1]])
=======
    à l'objet contour ) et la position de l'element de conteur dont il est le plus proche
>>>>>>> 51ebf68cba94b65083c4895d3670076f8d17caf9
    """
    height, width = map.shape[0], map.shape[1]
    near_contour_map = -1*np.ones((height, width, 2))
    near_contour_map = near_contour_map.astype(int)
    dist_to_c = np.zeros((height, width))+height*width
    for i in range(len(contours)):
        for k in range(len(contours[i])):
            x,y = contours[i][k][0], contours[i][k][1]
            for j in range(-b+1,b):
                for m in range(-b+1,b):
                    d = dist(x,y,x+j,y+m)
                    if d <= dist_to_c[x+j,y+m]:
                        near_contour_map[x+j,y+m] = np.array([i, k])
                        dist_to_c[x+j,y+m] = d

    return near_contour_map



def get_map(filename):
    """
    :param filename:
    :return: la map booleène codant à partir de l'image png, si il y a presence d'obstacle.
     aplatie la matrice obtenue pour pouvoir l'envoyer par socket
    """
    img = mpimg.imread(filename)
    height, width = img.shape[0], img.shape[1]
    new_img = img[:, :, 3] > 0.9
    return new_img.tolist(), width, height


def file_to_map(filename):
    """

    :param filename:
    :return: la map booleène codant à partir de l'image png, si il y a presence d'obstacle.
    """
    img = mpimg.imread(filename)
    height, width = img.shape[0], img.shape[1]
    new_img = img[:, :, 3] > 0.9
    return new_img, width, height


def print_map(img):
    """
    affiche avec imshow l'image
    :param img:
    :return:
    """
    plt.imshow(img)
    plt.savefig('contour_map')
    plt.show()

def slide(x, y, x_, y_, near_border, tanj_map, contours):
    """
    cette fonction est cense être appele si et seulement si x,y est proche d'une obstacle et
     si x_,y_ se trouve dans un obstacle
    :param x: latitude initiale
    :param y: longitude initiale
    :param x_: latitude finale
    :param y_: longitude finale
    :param near_border: la matrice calculee par compute_nearest_border
    :param tanj_map: la matrice calculee par compute_tangeante
    :param contours: liste des differents contours
<<<<<<< HEAD
    :return: la position ou le joueur glisse s'il part de la position initiale et souhaiterais aller à la position
=======
    :return: la position où le joueur glisse s'il part de la position initiale et souhaiterais aller à la position
>>>>>>> 51ebf68cba94b65083c4895d3670076f8d17caf9
    finale (la vitesse incidente à l'obstacle est donc la difference entre ces deux positions)
    """
    vx, vy = x_ - x, y_ - y
    print(int(x),int(y))
    i, k = near_border[int(x), int(y)]

    print(contours[i][k])
    t = tanj_map[contours[i][k][0], contours[i][k][1]]
    p = int((vx + vy * t) / np.sqrt(1 + t ** 2))
    n_x, n_y = get(contours[i], k + p)
    if (n_x - x) * vx + (n_y - y) * vy <= 0:
        n_x, n_y = get(contours[i], k - p)

    return n_x, n_y

def load_map (filename, bw = 4, b = 5):
    """
    :param filename:
    :param bw: bande passante
    :param b: distance limite de calcul
    :return: map, width, height, inner_slide (la fonction de glissement associee a la map)
    """
    map, width, height = file_to_map(filename)
    contours = get_contour(map)

    ### ce test verifie si tout le contours sont fermées
    for c in contours:
        assert assert_closed_curve(c), "contour non fermé"
    ###-------------------------------------------------

    int_map = map.astype(int)
    tanj_map = compute_tangeante(int_map, contours, bw = bw)
    near_border = compute_nearest_border(int_map, contours, b = b)
    def inner_slide (x, y, x_, y_):

        vx, vy = x_ - x, y_ - y
        i, k = near_border[int(x), int(y)]
        t = tanj_map[contours[i][k][0], contours[i][k][1]]
        p = int((vx + vy * t) / np.sqrt(1 + t ** 2))
        n_x, n_y = get(contours[i], k + p)
        if (n_x - x) * vx + (n_y - y) * vy <= 0:
            n_x, n_y = get(contours[i], k - p)

        return n_x, n_y
    return map, width, height, inner_slide

if __name__ == "__main__":
    """
    fait un affichage des contours obtenus
    """
    new_img, width, height = file_to_map("./static/map_alpha.png")

    contours = get_contour(new_img)
    c_map = np.zeros((height, width))
    new_img = new_img.astype(int)

    tanj_map = compute_tangeante(new_img, contours, bw=2)
    near_contour_map = compute_nearest_border(new_img, contours, b=3)

    lw = 6
    for c in contours:
        for k in range(len(c)):
            new_img[c[k][0]:c[k][0] + lw, c[k][1]:c[k][1] + lw] = 10*(k+2)/len(c)

    print_map(new_img)
