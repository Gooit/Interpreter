import os
import shlex
import subprocess
import sys
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
        self.compile_command = conf.get('compile_command') or ""
        self.work_dir = conf.get('work_dir') or "work_dir/"
        self.work_filename = conf.get("work_filename") or ""
        self.user_out_path = "user_out/main.out"
        self.cases_root_path = conf.get("cases_root_path") or "cases/"


    def _initial(self, *args, **kwargs):
        return kwargs

    def _load_local_conf(self):
        return {}

    def _write_code(self, code):
        work_filename = self.work_dir + self.work_filename
        with open(work_filename, 'wt') as f:
            f.write(code)


    def _compile(self):
        p = subprocess.Popen(self.compile_command, shell=True, cwd=self.work_dir, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = p.communicate()  
        if p.returncode == 0: 
            return True

        # dblock.acquire()
        # update_compile_info(solution_id, err + out) # ±àÒëÊ§°Ü,¸üÐÂÌâÄ¿µÄ±àÒë´íÎóÐÅÏ¢
        # dblock.release()
        return False

    def __call__(self, *args, **kwargs):
        self.low_level()
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

    def low_level(self):
        try:
            os.setuid(int(os.popen("id -u %s" % "nobody").read()))
        except:
            pass

    def _single_run_rule(self, input_file_index, path,
                         solution_id, problem_id, time_limited, mem_limited):
        return True, ""

    def _run(self, *args, **kwargs):
        problem_id = kwargs['problem_id']
        in_cases_path = os.path.join(self.cases_root_path, str(problem_id), 'in')
        in_cases_num = len(os.listdir(in_cases_path))
        out_cases_path = os.path.join(self.cases_root_path, str(problem_id), 'out')
        out_cases_num = len(os.listdir(out_cases_path))
        if in_cases_num != out_cases_num:
            print('warning', 'cases error')
        status, msg, data = False, '', None
        start_time = time.time()
        for index in range(in_cases_num):
            status = self._single_run_rule(input_file_index=index, path=in_cases_path, **kwargs)
            if status['result']:
                return status, msg
            status, msg = self._judge(index, **kwargs)
            if not status:
                return status, msg, None
        return status, msg, data

    def _check_dangerous_code(self, code):
        return True

    def _judge(self, output_file_index, problem_id, **kwargs):

        out_cases_path = os.path.join(self.cases_root_path, str(problem_id), output_file_index)
        with open(out_cases_path, 'r') as f:
            out_case = f.read().replace('\r','').rstrip()  # É¾³ý\r,É¾³ýÐÐÄ©µÄ¿Õ¸ñºÍ»»ÐÐ
        with open(self.user_out_path, 'r') as f:
            user_out = f.read().replace('\r', "").strip()
        if out_case == user_out:  # ÍêÈ«ÏàÍ¬:AC
            return "Accepted"
        if out_case.split() == user_out.split():  # ³ýÈ¥¿Õ¸ñ,tab,»»ÐÐÏàÍ¬:PE
            return "Presentation Error"
        if out_case in user_out:  # Êä³ö¶àÁË
            return "Output limit"
        return "Wrong Answer"  # ÆäËûWA


class CPlusPlusInterpreter(Interpreter):
    def check_dangerous_code(solution_id, code):
        if code.find('system') >= 0:
            return False
        return True


class PythonInterpreter(Interpreter):
    def __init__(self):
        super().__init__()
        self.user_out_path = "user_out/python.out"
        self.compile_command = "python3 -m py_compile main.py"

    def _initial(self, *args, **kwargs):
        kwargs['time_limited'] *= 2
        kwargs['memory_limited'] *= 2

    def check_dangerous_code(self, code):
        support_modules = [
            're',  # ÕýÔò±í´ïÊ½
            'sys',  # sys.stdin
            'string',  # ×Ö·û´®´¦Àí
            'scanf',  # ¸ñÊ½»¯ÊäÈë
            'math',  # ÊýÑ§¿â
            'cmath',  # ¸´ÊýÊýÑ§¿â
            'decimal',  # ÊýÑ§¿â£¬¸¡µãÊý
            'numbers',  # ³éÏó»ùÀà
            'fractions',  # ÓÐÀíÊý
            'random',  # Ëæ»úÊý
            'itertools',  # µü´úº¯Êý
            'functools',
            # Higher order functions and operations on callable objects
            'operator',  # º¯Êý²Ù×÷
            'readline',  # ¶ÁÎÄ¼þ
            'json',  # ½âÎöjson
            'array',  # Êý×é
            'sets',  # ¼¯ºÏ
            'queue',  # ¶ÓÁÐ
            'types',  # ÅÐ¶ÏÀàÐÍ
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
        command = "python3 %s" % os.path.join(self.work_dir, '__pycache__/main.cpython-37.pyc')
        main_exe = shlex.split(command)
        input_file_path = os.path.join(path, "%s.in" % input_file_index)
        try:
            input_file = open(input_file_path, 'r')
            temp_output_file = open('', 'w')
            cfg = {
                'args': main_exe,
                'fd_in': input_file.fileno(),
                'fd_out': temp_output_file.fileno(),
                'timelimit': time_limited,  # in MS
                'memorylimit': mem_limited,  # in KB
            }
            self.low_level()
            result = lorun.run(cfg)
        except:
            return False, "System Error", None
        finally:
            input_file.close()
            temp_output_file.close()
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
