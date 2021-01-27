from .models import *
import random

def get_probes(subs, strategy='random'):
    if strategy == 'random':
        sub_ids = set()
        for sub in subs:
            sub_ids.add(sub.sub_id)
        probes = []
        for _ in range(assign.assignment_peergrading_profile.n_probes):
            id = random.choice(tuple(sub_ids))
            sub = subs.objects.get(sub_id=id)
            probe = ProbeSubmission.objects.create(parent_sub=sub)
            sub_ids.remove(id)
            probes.append({'probe_id': probe.probe_id})
        
        return probes

def get_outline_with_rubrics(probe, assign):
    outline_with_rubrics = []
    assign_questions = assign.questions.all()

    for q in assign_questions:
        ques = {
            "qid": q.qid,
            "max_marks": q.max_marks,
            "min_marks": q.min_marks,
            "rubrics": [],
            "sub_questions": [],
        }
        sub_questions = q.sub_questions.all()
        g_rubrics = q.g_rubrics.all()

        for gr in g_rubrics:
            g_rub = {
                "marks": gr.marks,
                "description": gr.description,
                "selected": gr.probe_rubric.selected,
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
                    "marks": gsr.marks,
                    "description": gsr.description,
                    "selected": gsr.probe_subrubric.selected
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
    
    if error_flag: return errors
    
    # [VAL_CHECK_1] All test questions should be in questions and marks should add up properly
    for test_question in test_questions:
        found = False
        test_ques_marks = 0
        test_ques_rubric_marks = 0
        for ques in questions:
            if  ques['qid'] == test_question['qid'] and \
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
                        if  sub_ques['sqid'] == test_sq['sqid'] and \
                            sub_ques['min_marks'] == test_sq['min_marks'] and \
                            sub_ques['max_marks'] == test_sq['max_marks']:
                            sq_found = True
                            break 

                if sq_max_marks == ques['max_marks'] and sq_min_marks == ques['min_marks']:
                    found = True
                
                tq_marks = 0
                if test_question['comment']['marks']: tq_marks += test_question['comment']['marks']
                for rb in test_question['rubrics']:
                    if rb['selected']:
                        tq_marks += rb['marks']
                
                for tsq in test_question['sub_questions']:
                    tsq_marks = 0
                    if tsq['comment']['marks']: tsq_marks += tsq['comment']['marks']
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
            error = test_question['qid'] + " - Payload question Either not found, or some sub-question not found, or marks error"
            errors.append(error)
    
    # [VAL_CHECK_2] All questions should be in test questions
    for ques in questions:
        found = False
        for test_question in test_questionss:
            if  ques['qid'] == test_question['qid'] and \
                ques['max_marks'] == test_question['max_marks'] and \
                ques['min_marks'] == test_question['min_marks']:
                found = True 
                
                for sub_ques in ques['sub_questions']:       
                    sq_found = False     
                    for test_sq in test_question['sub_questions']:
                        if  sub_ques['sqid'] == test_sq['sqid'] and \
                            sub_ques['min_marks'] == test_sq['min_marks'] and \
                            sub_ques['max_marks'] == test_sq['max_marks']:
                            sq_found = True
                            break 
                break

        if not found or not sq_found:
            error_flag = True 
            error = ques['qid'] + " - Database question either not found, or some sub-question not found, or marks error"
            errors.append(error)
      
    if not error_flag:
        return "ok"

    else: return errors



