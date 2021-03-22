import math


mu = 16.234
gamma = 1.234

# students are indexed from 0-9
# students contains the true score of the students
# scores out of 10
students = [5, 8, 7, 3, 6, 9, 7, 4, 10, 6]
# h,h,h,hs,hs,hl,hl,d,d,d(random)
probe_idx = [0, 1, 2]

# students paper and their marks

grades = [[(3, 3), (4, 6), (1, 7), (2, 7)], [(5, 9), (6, 7), (2, 7), (0, 6)], [(7, 4), (8, 10), (0, 6), (1, 8)], [(4, 5), (5, 7), (1, 6), (2, 6)], [(5, 6), (6, 5), (2, 5), (0, 4)], [
    (6, 8), (7, 6), (0, 6), (1, 8)], [(7, 6), (8, 10), (1, 9), (2, 8)], [(8, 6), (9, 4), (2, 4), (0, 2)], [(9, 3), (3, 1), (0, 2), (1, 4)], [(3, 3), (4, 5), (1, 3), (2, 4)]]

graded_by = [[]]
for i in range(10):
    for idx, student in enumerate(grades):
        for elem in student:
            if elem[0] == i:
                graded_by[i].append((idx, elem[1]))
    graded_by.append([])

for cnt, i in enumerate(graded_by):
    print(cnt)
    for j in i:
        print(j[0], j[1], ' ', end='')
    print()

# for cnt, i in enumerate(grades):
#     print('grader ', cnt)
#     for j in i:
#         print(j[0], '->', j[1], 'marks', end='  |')
#     print()


bi = []

for i in grades:
    stu1, marks1 = i[2]
    stu2, marks2 = i[3]
    sum = (marks1-students[stu1])+(marks2-students[stu2])
    bi.append(sum/2)

# print('bi', bi)

ti = []

for i in grades:
    stu1, marks1 = i[2]
    stu2, marks2 = i[3]
    sum = (marks1-(students[stu1]+bi[stu1]))**2 + \
        (marks2-(students[stu2]+bi[stu2]))**2
    ti.append(1/sum)


# print('ti', ti)

# r -> score of a paper

def cal_r(graded_by):
    r = []
    for paper in range(10):
        c1 = math.sqrt(gamma)*mu
        c2 = 0
        for elem in graded_by[paper]:
            grader = elem[0]
            c2 += math.sqrt(ti[grader]) * (elem[1]-bi[grader])
        c3 = math.sqrt(gamma)
        c4 = 0
        for elem in graded_by[paper]:
            grader = elem[0]
            c4 += ti[grader]
        r_val = (c1+c2)/(c3+c4)
        r.append(r_val)
    return r


def cal_r_minus(idx, graded_by):
    r = []
    for paper in range(10):
        c1 = math.sqrt(gamma)*mu
        c2 = 0
        for elem in graded_by[paper]:
            grader = elem[0]
            if grader == idx:
                continue
            c2 += math.sqrt(ti[grader]) * (elem[1]-bi[grader])
        c3 = math.sqrt(gamma)
        c4 = 0
        for elem in graded_by[paper]:
            grader = elem[0]
            if grader == idx:
                continue
            c4 += ti[grader]
        r_val = (c1+c2)/(c3+c4)
        r.append(r_val)
    return r


r = cal_r(graded_by)


def R(graded_by, j, setting):
    r = []
    if(setting == "normal"):
        r = cal_r(graded_by)
    else:
        r = cal_r_minus(j, graded_by)
    if j not in probe_idx:
        return 0
    return -(r[j]-students[j])**2


def wj(graded_by):
    W = []
    for i in range(10):
        W.append(R(graded_by, i, "normal"))
    return W


def wji(graded_by):
    WJI = []
    for i in range(10):
        WJI.append(R(graded_by, i, "notnormal"))
    return WJI


W = wj(graded_by)
WJI = wji(graded_by)

print(W)
print(WJI)


alpha = 5


def get_bonus(W, WJI):
    bonus = []
    for i in range(10):
        for elem in grades[i]:
            s = 0
            if elem[0] not in probe_idx:
                s += alpha*(W[elem[0]]-WJI[elem[0]])
        bonus.append(s)
    return bonus


bonus = get_bonus(W, WJI)
print(bonus)
