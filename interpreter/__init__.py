import os
import shlex
import subprocess
import threading
import time


class Singleton(type):
    def __new__(cls, name, bases, attrs):
        cls.__instance = None
        return super(Singleton, cls).__new__(cls, name, bases, attrs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super(Singleton, self).__call__(*args, **kwargs)
        return self.__instance





class Interpreter(object):

    __metaclass__ = Singleton

    compile_lock = threading.Lock()
    def __init__(self):
        conf = self._load_local_conf()
        self.compile_command = conf['compile_command'] or ""
        self.temp_answer_path = conf['temp_answer_path'] or "temp_answer/"
        self.temp_answer_filename = conf["temp_answer_filename"] or ""
        self.cases_root_path = conf["cases_root_path"] or "cases/"


    def _initial(self, *args, **kwargs):
        return kwargs

    def _load_local_conf(self):
        return {}

    def _write_code(self, code):
        temp_answer_filename = self.temp_answer_path + self.temp_answer_filename
        with open(temp_answer_filename, 'wt') as f:
            f.write(code)


    def _compile(self):
        p = subprocess.Popen(self.compile_command, shell=True, cwd=dir_work, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = p.communicate()  # ��ȡ���������Ϣ
        if p.returncode == 0:  # ����ֵΪ0,����ɹ�
            return True

        # dblock.acquire()
        # update_compile_info(solution_id, err + out)  # ����ʧ��,������Ŀ�ı��������Ϣ
        # dblock.release()
        return False

    def __call__(self, *args, **kwargs):
        kwargs = self._initial(**kwargs)
        code = kwargs.pop('code')
        result = {}
        with self.compile_lock:
            self._write_code(code)
            self._compile()
        status = self._check_dangerous_code(code)
        if not status:
            result['status'] = status
            result['msg'] = "Runtime Error"
            result['data'] = None
            return result
        status, value, data = self._run(**kwargs)
        result['status'] = status
        result['msg'] = value
        result['data'] = data
        return result

    def _single_run_rule(self, input_file_index, path,
                         solution_id, problem_id, time_limited, mem_limited):
        return True, "", ""

    def _run(self, *args, **kwargs):
        problem_id = kwargs['problem_id']
        in_cases_path = os.path.join(self.cases_root_path, str(problem_id), 'in')
        in_cases_num = len(os.listdir(in_cases_path))
        out_cases_path = os.path.join(self.cases_root_path, str(problem_id), 'out')
        out_cases_num = len(os.listdir(out_cases_path))
        if in_cases_num != out_cases_num:
            print('warning', '���������һ��')
        status, msg, data = False, '', None
        start_time = time.time()
        for index in range(in_cases_num):
            status, msg, user_answer = self._single_run_rule(input_file_index=index, path=in_cases_path, **kwargs)
            if not status:
                return status, msg, data
            status, msg = self._judge(user_answer, index, **kwargs)
            if not status:
                return status, msg, None
        return status, msg, data

    def _check_dangerous_code(self, code):
        return True

    def _judge(self, user_asnwer, output_file_index, problem_id, **kwargs):

        path = os.path.join(self.cases_root_path, str(problem_id), output_file_index)
        with(path, 'w') as f:
            out_case = f.read().replace(
                '\r',
                '').rstrip(
            )  # ɾ��\r,ɾ����ĩ�Ŀո�ͻ���
        if out_case == user_asnwer:  # ��ȫ��ͬ:AC
            return "Accepted"
        if out_case.split() == user_asnwer.split():  # ��ȥ�ո�,tab,������ͬ:PE
            return "Presentation Error"
        if out_case in user_asnwer:  # �������
            return "Output limit"
        return "Wrong Answer"  # ����WA


class CPlusPlusInterpreter(Interpreter):
    def check_dangerous_code(solution_id, code):
        if code.find('system') >= 0:
            return False
        return True


class PythonInterpreter(Interpreter):
    def _initial(self, *args, **kwargs):
        kwargs['time_limited'] *= 2
        kwargs['memory_limited'] *= 2

    def check_dangerous_code(self, code):
        support_modules = [
            're',  # ������ʽ
            'sys',  # sys.stdin
            'string',  # �ַ�������
            'scanf',  # ��ʽ������
            'math',  # ��ѧ��
            'cmath',  # ������ѧ��
            'decimal',  # ��ѧ�⣬������
            'numbers',  # �������
            'fractions',  # ������
            'random',  # �����
            'itertools',  # ��������
            'functools',
            # Higher order functions and operations on callable objects
            'operator',  # ��������
            'readline',  # ���ļ�
            'json',  # ����json
            'array',  # ����
            'sets',  # ����
            'queue',  # ����
            'types',  # �ж�����
        ]
        for line in code:
            if line.find('import') >= 0:
                words = line.split()
                tag = 0
                for w in words:
                    if w in support_modules:
                        tag = 1
                        break
                if tag == 0:
                    return False
        return True

    def _single_run_rule(self, input_file_index, path, solution_id,
                         problem_id, time_limited, mem_limited):
        command = "python3 %s" % os.path.join("temp_answer", '__pycache__/main.cpython-33.pyc')
        main_exe = shlex.split(command)
        try:
            input_file_obj = open()
            output_file_obj = open()
            cfg = {
                'args': main_exe,
                'fd_in': input_file_obj.fileno(),
                'fd_out': output_file_obj.fileno(),
                'timelimit': time_limited,  # in MS
                'memorylimit': mem_limited,  # in KB
            }
            result = lorun.run(cfg)
        except:
            return False, "System Error", None
        finally:
            input_file_obj.close()
            output_file_obj.close()
        return True, result


class JavaInterpreter(Interpreter):
    pass


class GoInterpreter(Interpreter):
    def check_dangerous_code(self, code):
        danger_package = [
            'os', 'path', 'net', 'sql', 'syslog', 'http', 'mail', 'rpc', 'smtp', 'exec', 'user',
        ]
        for item in danger_package:
            if code.find('"%s"' % item) >= 0:
                return False
        return True
