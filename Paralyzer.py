# import yagmail
# from datetime import datetime

import multiprocessing
import time
import os
from multiprocessing import Pool
import re
from Resulter import extract_results


path_work = './'                            # current dir as default
path_pv = 'proverif '                       # if no proverif in PATH, change this to proverif's path
path_lib = './lib.pvl'                      # pvl file, including lib(functions, types and events) and query(query and settings)
path_query = './query.pvl'
path_process = ["./ENC.pv", "./MAC.pv"]     # pv file
path_attacker = './attacker.pvl'            # attacker's actions, described in process macro.
path_result = "./paralyzer-result/"             # all the outputs and query's results are save in path_result


# extract queries in query.pvl
def extract(file_path, start_flag, end_flag):
    with open(file_path, "r") as file:
        file_content = file.read()

    result = []
    start_index = 0 

    while True:
        # find start_flag
        start_index = file_content.find(start_flag, start_index)
        if start_index == -1:
            break  

        # find end_flag
        end_index = file_content.find(end_flag, start_index)
        if end_index == -1:
            break  

        extracted_text = file_content[start_index + len(start_flag):end_index].strip()
        tag = re.findall(r"<(.*?)>", extracted_text)
        if len(tag) == 1:
            result.append((tag[0], extracted_text))
        else:
            result.append(('', extracted_text))

        start_index = end_index + 1

    return result


# add attackers into ENC.pv or MAC.pv
def attacker(ATK_path, process_path, base_path):
    if not os.path.exists(base_path + 'ATK/'):
        os.mkdir(base_path + 'ATK/')
    ATK = extract(ATK_path, 'let', '=')
    ATK_files_path = []
    for (t, i) in ATK:
        if '(' not in i:
            continue
        with open(process_path, 'r') as file:
            file_content = file.read()

        ATK_flag = "(* <ATTACKER> *)"
        ATK_index = 0
        ATK_index = file_content.find(ATK_flag, ATK_index)
        if ATK_index == -1:
            return []
        else:
            if i == 'CompromisedParticipantA(sk:SK_t)':
                ATKprocess = i.replace('sk:SK_t', 'PrivKA')
            elif i == 'CompromisedParticipantB(sk:SK_t)':
                ATKprocess = i.replace('sk:SK_t', 'PrivKB')
            else:
                ATKprocess = i
            new_file = file_content[:ATK_index] + ATKprocess + '|\n' + file_content[ATK_index + len(ATK_flag) + 1:]
            new_file_path = base_path + 'ATK/' + os.path.basename(process_path)[:-3] + '-' + re.sub(r"\([^()]*\)", "",
                                                                                                   ATKprocess) + '.pv'
            with open(new_file_path, 'w') as file:
                file.write(new_file)
            ATK_files_path.append(new_file_path)
    return ATK_files_path


# run a cmd to use proverif
def long_time_task(c, query_num,lock,):
    start = time.time()
    os.system(c)
    end = time.time()
    result = c.split('>')
    result_name = result[1].strip()
    task = result_name.rsplit('/', 3)
    if len(task) > 1:
        task_name = task[1] + '/' + task[2]
    with lock:
        query_num.value -= 1
        print('Task %s runs %0.2f seconds. ' % (task_name, (end - start)) + str(query_num.value) + ' left.')
    log_output = c.split('>')
    if len(log_output) > 1:
        log_name = log_output[1].strip()
        parse_log(log_name)
    return 'Task %s runs %0.2f seconds.' % (task_name, (end - start))


# writelines into result-timeout.txt after finish a query
def call_back(s):
    with open(path_work + 'result-timeout.txt', "a+") as file:
        file.writelines(s + '\n')

# make single query file
def query_file(qlist):
    query_path = path_work + 'query'
    if not os.path.exists(query_path):
        os.mkdir(query_path)
    query_file_path = []
    for index, q in enumerate(qlist):
        file_name = f"{q[0]}.pvl"
        file_path = os.path.join(query_path, file_name)

        with open(file_path, "w") as file:
            file.write('query' + q[1] + '.')

        query_file_path.append(file_path)
    return query_file_path


# make proverif cmd
def pv_cmd(query_file_path_list, process, result_dir):
    result = []
    for i in query_file_path_list:
        for j in process:
            output = result_dir + os.path.basename(j)[:-3] + "/" + os.path.basename(i)[:-4]
            if not os.path.exists(output):
                os.makedirs(output)
            result.append(path_pv  + \
                          ' -lib ' + path_lib + \
                          ' -lib ' + i + \
                          ' -lib ' + path_attacker + \
                          ' ' + j + \
                          ' > ' + output + '/output.log'
                          )
    return result


# check if a query is TRUE or FALSE or other
def parse_log(i):
    with open(i, 'r',encoding='utf-8') as f:
        content = f.read()
        index = content.find("Verification summary:")
        summary = content[index:]
        if 'true' in summary:
            res = '/TRUE.log'
        elif 'false' in summary:
            res = '/FALSE.log'
        elif 'cannot be proved' in summary:
            res = '/CANNOT.log'
        else:
            res = '/RESULT_NOT_FOUND.log'
        with open(os.path.dirname(i) + res, 'w') as res_f:
            res_f.writelines(summary)


if __name__ == '__main__':
    if not os.path.exists(path_result):
        os.mkdir(path_result)
    query_list = extract(path_query, 'query', '.')
    query_file_path_list = query_file(query_list)
    cmd = []
    for i in path_process:
        ATK = attacker(path_attacker, i, path_work)
        cmd += (pv_cmd(query_file_path_list, ATK, path_result))
    p = Pool()  # The default number of subprocess is the number of cores.
    # p = Pool(4)  
    query_num_manager = multiprocessing.Manager()
    lock = query_num_manager.Lock()
    query_num=query_num_manager.Value('i',len(cmd))
    print('Waiting for all subprocesses done...')
    results = [p.apply_async(long_time_task, (i,query_num,lock,), callback=call_back) for i in cmd]
    try:
        output = [result.get(timeout=48 * 60 * 60) for result in results] #set 2 days as the max time
    except multiprocessing.TimeoutError:
        print('time out')
    p.terminate()
    p.join()
    print('All subprocesses done.')
    extract_results(path_result)

    # use code below to send email when the program finishes.
    # yag = yagmail.SMTP(user='123@456.com', password='xxxx', host='smtp.456.com')
    # yag.send(to='456@123.com', subject='ProVerif batch verify finished!', contents='All subprocesses are done, at '+str(datetime.now()))
