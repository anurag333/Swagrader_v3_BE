import numpy as np
import math

mat1 = [[None, 10.0, 3.0, 3.0, 2.0, None, None, None, None, None], [3.0, None, 1.0, None, None, 3.0, 7.0, None, None, None], [0.0, 7.0, None, None, None, None, None, 8.0, 0.0, None], [4.0, 7.0, None, None, 2.0, 3.0, None, None, None, None], [8.0, None, 9.0, None, None, 5.0, 5.0, None, None, None], [
    None, 8.0, 8.0, None, None, None, 5.0, 7.0, None, None], [6.0, 0.0, None, None, None, None, None, 5.0, 8.0, None], [4.0, None, 6.0, None, None, None, None, None, 4.0, 1.0], [None, 3.0, 6.0, 7.0, None, None, None, None, None, 9.0], [2.0, 2.0, None, 3.0, 5.0, None, None, None, None, None]]
mat2 = [[None, 5.0, 7.0, 5.0, 3.0, None, None, None, None, None], [2.0, None, 5.0, None, None, 3.0, 3.0, None, None, None], [5.0, 7.0, None, None, None, None, None, 3.0, 7.0, None], [6.0, 8.0, None, None, 5.0, 9.0, None, None, None, None], [2.0, None, 4.0, None, None, 3.0, 3.0, None, None, None], [
    None, 2.0, 7.0, None, None, None, 2.0, 3.0, None, None], [4.0, 5.0, None, None, None, None, None, 2.0, 5.0, None], [3.0, None, 4.0, None, None, None, None, None, 3.0, 4.0], [None, 7.0, 8.0, 6.0, None, None, None, None, None, 7.0], [6.0, 9.0, None, 8.0, 6.0, None, None, None, None, None]]

mu = 16.234
gm = 1.234
# mu = 1
# gm = 2
n_probes = 3


def get_bias(mat, probe_idx, probe_score):
    bi = []
    for i, student in enumerate(mat):
        num_probes = 0
        sum = 0.0
        for j, paper in enumerate(student):
            if j in probe_idx and mat[i][j] != None:
                sum += (mat[i][j]-probe_score[j])
                num_probes += 1
        bi.append(sum/num_probes)
    return bi


def get_reliability(mat, probe_idx, probe_score):
    ti = []
    bi = get_bias(mat, probe_idx, probe_score)
    for i, student in enumerate(mat):
        num_probes = 0
        sum = 0.0
        for j, paper in enumerate(student):
            if j in probe_idx and mat[i][j] != None:
                sum += (mat[i][j]-(probe_score[j]+bi[i]))**2
                # if sum == 0.0:
                #     print(i, j)
                #     print(mat[i][j], (probe_score[j]), bi[i])
                num_probes += 1
        if sum == 0.0:
            ti.append(0)
        else:
            ti.append((num_probes-1)/sum)
    return ti


def get_r_star_j(mu, gm, arr, bi, ti):
    c1 = math.sqrt(gm)*mu
    c3 = math.sqrt(gm)
    c2 = 0.0
    for i, val in enumerate(arr):
        if val != None:
            c2 += math.sqrt(ti[i]) * (val-bi[i])
    c4 = 0.0
    for i, val in enumerate(arr):
        if val != None:
            c4 += math.sqrt(ti[i])
    ################
    if c3+c4 == 0.0:
        return 0.0
    else:
        return (c1+c2)/(c3+c4)


def R(x, y):
    return -(x-y)**2


def trupeqa(mat, mu, gm, n_probes, probe_score, alpha):
    probe_idx = [i for i in range(n_probes)]
    mat = np.array(mat
                   )
    bi = get_bias(mat, probe_idx, probe_score)
    ti = get_reliability(mat, probe_idx, probe_score)

    print('bi => ', bi)
    print('ti => ', ti)

    r_star = []
    for i in range(len(mat[0])):
        arr = np.ravel(mat[:, i:i+1])
        r_star.append(get_r_star_j(mu, gm, arr, bi, ti))

    print('r*j => ', r_star)
    yj = []
    for i in range(len(r_star)):
        if i in probe_idx:
            yj.append(probe_score[i])
        else:
            yj.append(r_star[i])

    w_star_j = []
    for i in range(len(mat[0])):
        # arr = np.ravel(mat[:, i:i+1])
        w_star_j.append(R(r_star[i], yj[i]))

    print('w_star_j => ', w_star_j)

    w_star_j_minus_i = []

    for i in range(len(mat)):
        wji = []
        for j in range(len(mat[0])):
            arr = np.ravel(mat[:, j:j+1])
            arr[i] = None
            rs = get_r_star_j(mu, gm, arr, bi, ti)
            wji.append(R(rs, yj[j]))
        w_star_j_minus_i.append(wji)

    print('w_star_j_minus_i => ', w_star_j_minus_i)

    bonus = []

    for i in range(len(mat)):
        bon = 0.0
        for j in range(len(mat[0])):
            if j in probe_idx:
                continue
            bon += alpha * (w_star_j[j]-w_star_j_minus_i[i][j])
        bonus.append(bon)

    print('yj => ', yj)
    print('bonus => ', bonus)
    return yj, bonus


# trupeqa(mat2, mu, gm, n_probes, [3, 4, 5], 5)
