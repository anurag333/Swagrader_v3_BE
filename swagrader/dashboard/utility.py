from .models import *
import random
from django.shortcuts import get_object_or_404
from django.http import Http404
from itertools import chain
from django.contrib.auth import get_user_model


def get_probes(outline_with_rubrics, assign, strategy='random'):
    subs = assign.assign_submissions.all()
    User = get_user_model()
    if strategy == 'random':
        sub_ids = set()
        for sub in subs:
            sub_ids.add(sub.sub_id)
        print(assign.assignment_peergrading_profile.all()[0].n_probes)
        print(assign.assignment_peergrading_profile.all()[0].peerdist)
        probes = []
        user_ids = set()
        for user in chain(assign.assignment_peergrading_profile.all()[0].instructor_graders.all(), assign.assignment_peergrading_profile.all()[0].ta_graders.all()):
            user_ids.add(user.email)
        for _ in range(assign.assignment_peergrading_profile.all()[0].n_probes):
            id = random.choice(tuple(sub_ids))
            # right now we are choosing random id to give probe and not removing from set
            user_id = random.choice(tuple(user_ids))
            sub = get_object_or_404(assign.assign_submissions.all(), sub_id=id)
            grader = get_object_or_404(User, email=user_id)
            print(sub)
            print(grader)
            try:
                probe = ProbeSubmission.objects.create(
                    parent_sub=sub, probe_grader=grader)
            except:
                print(
                    '########################### probeSubmission object already exists#################################################')
                raise Http404
            sub_ids.remove(id)
            probes.append({'probe_id': probe.probe_id})
            for q in outline_with_rubrics:
                cur_ques = Question.objects.get(ques_id=q['qid'])
                ques_sub = sub.submissions.all().get(question=cur_ques)
                ques = ProbeSubmissionQuestion.objects.create(
                    parent_probe_sub=probe, parent_ques=ques_sub)
                ques_com = ProbeSubmissionQuestionComment.objects.create(
                    parent_ques=ques)

                for sq in q['sub_questions']:
                    sub_ques = SubQuestion.objects.get(sques_id=sq['sqid'])
                    sub_ques = ProbeSubmissionSubquestion.objects.create(
                        parent_probe_ques=ques, parent_sub_ques=sub_ques)
                    sub_ques_com = ProbeSubmissionSubquestionComment.objects.create(
                        parent_subques=sub_ques)

        return probes


def get_outline_with_rubrics(assign):
    outline_with_rubrics = []
    assign_questions = assign.questions.all()

    for q in assign_questions:
        ques = {
            "qid": q.ques_id,
            "max_marks": q.max_marks,
            "min_marks": q.min_marks,
            "rubrics": [],
            "sub_questions": [],
        }
        sub_questions = q.sub_questions.all()
        g_rubrics = q.g_rubrics.all()

        for gr in g_rubrics:
            g_rub = {
                "rubric_id": gr.rubric_id,
                "marks": gr.marks,
                "description": gr.description,
            }
            ques["rubrics"].append(g_rub)

        for sq in sub_questions:
            sub_ques = {
                "sqid": sq.sques_id,
                "max_marks": sq.max_marks,
                "min_marks": sq.min_marks,
                "sub_rubrics": []
            }
            g_subrubrics = sq.g_subrubrics.all()
            for gsr in g_subrubrics:
                gs_rub = {
                    "sub_rubric_id": gsr.sub_rubric_id,
                    "marks": gsr.marks,
                    "description": gsr.description,
                }
                sub_ques["sub_rubrics"].append(gs_rub)

            ques["sub_questions"].append(sub_ques)

        outline_with_rubrics.append(ques)

    return outline_with_rubrics


def sanitization_check(assign, test_questions):
    assign_questions = assign.questions.all()
    questions = []
    error_flag = False
    errors = []

    for q in assign_questions:
        ques = {
            "qid": q.qid,
            "max_marks": q.max_marks,
            "min_marks": q.min_marks,
            "sub_questions": []
        }
        sub_questions = q.sub_questions.all()
        for sq in sub_questions:
            sub_ques = {
                "sqid": sq.sques_id,
                "max_marks": sq.max_marks,
                "min_marks": sq.min_marks,
            }
            ques["sub_questions"].append(sub_ques)
        questions.append(ques)

    # [VAL_CHECK_0] All keys must be there
    for tq in test_questions:
        tqid = tq.get('qid', None)
        tminm = tq.get('min_marks', None)
        tmaxm = tq.get('max_marks', None)
        trub = tq.get('rubrics', -1)
        tcom = tq.get('comment', -1)
        tsubq = tq.get('sub_questions', -1)
        if not (tqid and tminm and tmaxm) or tsubq == -1 or trub == -1 or tcom == -1:
            error_flag = True
            error = "Key error in question payload"
            errors.append(error)

    if error_flag:
        return errors

    # [VAL_CHECK_1] All test questions should be in questions and marks should add up properly
    for test_question in test_questions:
        found = False
        test_ques_marks = 0
        test_ques_rubric_marks = 0
        for ques in questions:
            if ques['qid'] == test_question['qid'] and \
                    ques['max_marks'] == test_question['max_marks'] and \
                    ques['min_marks'] == test_question['min_marks']:

                if ques['sub_questions']:
                    sq_max_marks = 0
                    sq_min_marks = 0
                else:
                    sq_max_marks = ques['max_marks']
                    sq_min_marks = ques['min_marks']

                for test_sq in test_question['sub_questions']:
                    sq_found = False
                    sq_max_marks += test_sq['max_marks']
                    sq_min_marks += test_sq['min_marks']

                    for sub_ques in ques['sub_questions']:
                        if sub_ques['sqid'] == test_sq['sqid'] and \
                                sub_ques['min_marks'] == test_sq['min_marks'] and \
                                sub_ques['max_marks'] == test_sq['max_marks']:
                            sq_found = True
                            break

                if sq_max_marks == ques['max_marks'] and sq_min_marks == ques['min_marks']:
                    found = True

                tq_marks = 0
                if test_question['comment']['marks']:
                    tq_marks += test_question['comment']['marks']
                for rb in test_question['rubrics']:
                    if rb['selected']:
                        tq_marks += rb['marks']

                for tsq in test_question['sub_questions']:
                    tsq_marks = 0
                    if tsq['comment']['marks']:
                        tsq_marks += tsq['comment']['marks']
                    for srb in tsq['sub_rubrics']:
                        if srb['selected']:
                            tsq_marks += srb['marks']

                    if not (tsq['min_marks'] <= tsq_marks <= tsq['max_marks']):
                        error_flag = True

                    tq_marks += tsq_marks

                if not (ques['min_marks'] <= tq_marks <= ques['max_marks']):
                    error_flag = True
                break

        if not found or not sq_found:
            error_flag = True
            error = test_question['qid'] + \
                " - Payload question Either not found, or some sub-question not found, or marks error"
            errors.append(error)

    # [VAL_CHECK_2] All questions should be in test questions
    for ques in questions:
        found = False
        for test_question in test_questions:
            if ques['qid'] == test_question['qid'] and \
                    ques['max_marks'] == test_question['max_marks'] and \
                    ques['min_marks'] == test_question['min_marks']:
                found = True

                for sub_ques in ques['sub_questions']:
                    sq_found = False
                    for test_sq in test_question['sub_questions']:
                        if sub_ques['sqid'] == test_sq['sqid'] and \
                                sub_ques['min_marks'] == test_sq['min_marks'] and \
                                sub_ques['max_marks'] == test_sq['max_marks']:
                            sq_found = True
                            break
                break

        if not found or not sq_found:
            error_flag = True
            error = ques['qid'] + \
                " - Database question either not found, or some sub-question not found, or marks error"
            errors.append(error)

    if not error_flag:
        return "ok"

    else:
        return errors


def match_making(P_papers, NP_papers, P_students, NP_students, peerdist):
    p_len = len(P_papers)
    np_len = len(NP_papers)

    match = []

    for i in range(np_len):
        for j in range((peerdist+1)//2):
            cur = (i + j + 1) % np_len
            match.append((NP_students[i], NP_papers[cur]))

    counter = int(0)
    for i in range(p_len):
        for j in range((peerdist+1)//2):
            cur = (counter) % np_len
            match.append((P_students[i], NP_papers[cur]))
            counter += 1

    for i in range(p_len):
        for j in range((peerdist)//2):  # no +1 because k/2 paper
            cur = (i + j + 1) % p_len
            match.append((P_students[i], P_papers[cur]))
    counter = 0
    for i in range(np_len):
        for j in range((peerdist)//2):
            cur = (counter) % p_len
            match.append((NP_students[i], P_papers[cur]))
            counter += 1

    return match
