
import multiprocessing
import time
import os
from multiprocessing import Pool
import re

work_path = '/home/dell/proverif/DDS/'
path_pv = '~/proverif/proverif2.04/proverif'
path_lib = '/home/dell/proverif/DDS/lib.pvl'
path_process_whole = "/home/dell/proverif/DDS/whole.pv"
path_process_MAC = "/home/dell/proverif/DDS/only-MAC.pv"
path_result = "/home/dell/proverif/DDS/result-timeout-1/"
path_query = '/home/dell/proverif/DDS/query.pvl'
path_event = '/home/dell/proverif/DDS/event.pvl'
path_compromise = '/home/dell/proverif/DDS/compromise.pvl'


def extract(file_path, start_flag, end_flag):
    # 打开文件进行读取
    with open(file_path, "r") as file:
        # 读取文件内容
        file_content = file.read()

    # 初始化结果数组
    result = []

    # 处理文本内容
    # start_flag = "query"  # query的起始标记
    # end_flag = "."  # 句点的结束标记
    start_index = 0  # 当前查找的起始索引

    # 查找并提取内容
    while True:
        # 在文本中查找起始标记
        start_index = file_content.find(start_flag, start_index)
        if start_index == -1:
            break  # 未找到起始标记，结束循环

        # 在文本中查找结束标记
        end_index = file_content.find(end_flag, start_index)
        if end_index == -1:
            break  # 未找到结束标记，结束循环

        # 提取内容并添加到结果数组中
        extracted_text = file_content[start_index + len(start_flag):end_index].strip()
        tag = re.findall(r"<(.*?)>", extracted_text)
        if len(tag) == 1:
            result.append((tag[0], extracted_text))
        else:
            result.append(('', extracted_text))
        # 更新起始索引
        start_index = end_index + 1

    return result


def compromise_Scenarios(cS_path, process_path, base_path):
    cS = extract(cS_path, 'let', '=')
    cS_files_path = []
    for (t, i) in cS:
        if '(' not in i:
            continue
        with open(process_path, 'r') as file:
            file_content = file.read()

        cS_flag = "(* <compromiseScenarios> *)"
        cs_index = 0
        cs_index = file_content.find(cS_flag, cs_index)
        if cs_index == -1:
            return []
        else:
            if i == 'compromisedParticipantA(sk:SK_t)':
                cSprocess = i.replace('sk:SK_t', 'PrivKA')
            elif i == 'compromisedParticipantB(sk:SK_t)':
                cSprocess = i.replace('sk:SK_t', 'PrivKB')
            else:
                cSprocess = i
            new_file = file_content[:cs_index] + cSprocess + '|\n' + file_content[cs_index + len(cS_flag) + 1:]
            new_file_path = base_path + 'cS/' + os.path.basename(process_path)[:-3] + '-' + re.sub(r"\([^()]*\)", "",
                                                                                                   cSprocess) + '.pv'
            with open(new_file_path, 'w') as file:
                file.write(new_file)
            cS_files_path.append(new_file_path)
    return cS_files_path


query_num = multiprocessing.Value('i', 0)


def long_time_task(c, ):
    start = time.time()
    os.system(c)
    end = time.time()
    result = c.split('-html')
    if len(result) > 1:
        result_name = result[1].strip()
    task = result_name.rsplit('/', 3)
    if len(task) > 1:
        task_name = task[1] + '/' + task[2]
    with query_num.get_lock():
        query_num.value -= 1
        print('Task %s runs %0.2f seconds. ' % (task_name, (end - start)) + str(query_num.value) + ' left.')
    log_output=c.split('>')
    if len(log_output) > 1:
        log_name = log_output[1].strip()
        parse_log(log_name)
    return 'Task %s runs %0.2f seconds.' % (task_name, (end - start))


def call_back(s):
    with open('/home/dell/proverif/DDS/time-out-1.txt', "a+") as file:
        file.writelines(s + '\n')


def query_file(qlist):
    # 创建临时文件夹
    query_path = work_path + 'query'
    if not os.path.exists(query_path):
        os.mkdir(query_path)
    query_file_path = []
    # 处理文本内容
    for index, q in enumerate(qlist):
        # 构建文件路径
        file_name = f"{q[0]}.pvl"
        file_path = os.path.join(query_path, file_name)

        # 保存内容到文件
        with open(file_path, "w") as file:
            file.write('query' + q[1] + '.')

        # 打印文件路径
        query_file_path.append(file_path)
    return query_file_path


log = []


def pv_cmd(query_file_path_list, process, result_dir):
    result = []
    for i in query_file_path_list:
        for j in process:
            output = result_dir + os.path.basename(j)[:-3] + "/" + os.path.basename(i)[:-4]
            if not os.path.exists(output):
                os.makedirs(output)
            if 'Reachability' in output:
                set = ' -set reconstructTrace false '
            else:
                set = ''
            result.append(path_pv + \
                          set + \
                          ' -lib ' + path_lib + \
                          ' -lib ' + path_event + \
                          ' -lib ' + i + \
                          ' -lib ' + path_compromise + \
                          ' ' + j + \
                          ' -html ' + output + \
                          ' > ' + output + '/output.log'
                          )
            log.append(output + '/output.log')
    return result


def parse_log(i):
    with open(i, 'r') as f:
        content = f.read()
        index = content.find("Verification summary:")
        summary = content[index:]
        if 'true' in summary:
            res = '/TURE.log'
        elif 'false' in summary:
            res = '/FALSE.log'
        elif 'cannot be proved' in summary:
            res = '/CANNOT.log'
        else:
            res = '/RESULT_NOT_FOUND.log'
        with open(os.path.dirname(i)+res, 'w') as res_f:
            res_f.writelines(summary)


if __name__ == '__main__':
    query_list = extract(path_query, 'query', '.')
    query_file_path_list = query_file(query_list)
    whole_cS = compromise_Scenarios(path_compromise, path_process_whole, work_path)
    MAC_cS = compromise_Scenarios(path_compromise, path_process_MAC, work_path)
    cmd = []
    cmd += (pv_cmd(query_file_path_list, whole_cS, path_result))
    cmd += (pv_cmd(query_file_path_list, MAC_cS, path_result))
    Pool_len=80
    p = Pool(len(cmd))
    query_num.value = len(cmd)
    # for i in cmd:
    #     p.apply_async(long_time_task, args=(i,), callback=call_back)
    # results = p.map_async(long_time_task, cmd, callback=call_back)
    print('Waiting for all subprocesses done...')
    results = [p.apply_async(long_time_task, (i,), callback=call_back) for i in cmd]
    try:
        output = [result.get(timeout=48*60*60) for result in results]
    except multiprocessing.TimeoutError:
        print('time out')
        # p.terminate()
        # p.join()
    p.terminate()
    p.join()
    print('All subprocesses done.')