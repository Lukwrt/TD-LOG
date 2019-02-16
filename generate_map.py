import matplotlib.image as mpimg
import numpy as np
import matplotlib.pyplot as plt
import pprint as pp


def get_contour(map):
    """
    :param map: une matrice de booléens
    :return: une liste de contours, un contours étant une liste de pixel formant continuement un contour. \
    l'ordre est donc fondamental dans ces listes. chaque contours est repéré par sa position dans la liste en sortie
    de la fonction
    """
    height, width = map.shape[0], map.shape[1]
    c_map = np.zeros((height, width)) # la matrice qui indique la présence d'un contour par un 1

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
        les positions des éléments de contours explorés deviennent des 0 dans c_map
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
        :return: la position de l'élément de contour contigu au pixel i,j -- si cet élément n'existe pas, renvoie -1,-1
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

    contours = [x for x in contours if len(x) > 2]
    return contours


def get(l, k):
    """
    :param l: liste
    :param k: position
    :return: l'element de l à la position k mod n, où n est la longueur de la liste
    permet d'accéder au élément d'une liste en les voyant comme des boucles
    """
    n = len(l)
    return l[k % n]


def compute_tangeante(map, contours, bw=5):
    """
    :param map: map de booléen
    :param contours: liste des différents contours
    :param bw: bande passante pour le calcul de la tangeante (permet de lisser le calul)
    :return: une matrice tanj_map avec la valeur de la pente de la tangeante pour \
     chaque position de la map, on attribut 0 aux postions ne faisant pas partie d'un contour
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
    :param map: map booléènne
    :param contours: contours de la map
    :param b: on calcule seulement pour les pixels étant à distance au maximum b d'un contour
    :return: une matice, avec pour chaque pixel proche d'un contour, l'id de ce contour (relativement
    à l'objet contour ) et la position de l'élement de conteur dont il est le plus proche
    """
    height, width = map.shape[0], map.shape[1]
    near_contour_map = np.zeros((height, width, 2))
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
    :return: la map booléène codant à partir de l'image png, si il y a présence d'obstacle.
     aplatie la matrice obtenue pour pouvoir l'envoyer par socket
    """
    img = mpimg.imread(filename)
    height, width = img.shape[0], img.shape[1]
    new_img = img[:, :, 3] > 0.9
    return new_img.tolist(), width, height


def file_to_map(filename):
    """

    :param filename:
    :return: la map booléène codant à partir de l'image png, si il y a présence d'obstacle.
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
    :param x: latitude initiale
    :param y: longitude initiale
    :param x_: latitude finale
    :param y_: longitude finale
    :param near_border: la matrice calculée par compute_nearest_border
    :param tanj_map: la matrice calculée par compute_tangeante
    :param contours: liste des différents contours
    :return: la position où le joueur glisse s'il part de la position initiale et souhaiterais aller à la position
    finale (la vitesse incidente à l'obstacle est donc la différence entre ces deux positions)
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
    :return: map, width, height, inner_slide (la fonction de glissement associée a la map)
    """
    map, width, height = file_to_map(filename)
    contours = get_contour(map)

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
