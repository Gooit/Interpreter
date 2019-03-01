import os
import shlex
import subprocess
import sys
import threading
import time
import lorun


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
        self.status_type = self._load_status_type()


    def _initial(self, *args, **kwargs):
        return kwargs

    def _load_local_conf(self):
        return {}

    @staticmethod
    def _load_status_type():
        return {
            0: 'Accepted',
            1: 'Wrong Answer',
            2: 'Time Limit Exceeded',
            3: 'Memory Limit Exceeded',
            4: 'Presentation Error',
            5: 'Runtime Error',
            6: 'Output limit',
            7: 'System Error'
        }

    def _write_code(self, code):
        work_filename = os.path.join(self.work_dir, self.work_filename)
        with open(work_filename, 'wt') as f:
            f.write(code)


    def _compile(self):
        p = subprocess.Popen(self.compile_command, shell=True, cwd=self.work_dir, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = p.communicate()  
        if p.returncode == 0: 
            return True

        # dblock.acquire()
        # update_compile_info(solution_id, err + out)
        # dblock.release()
        return False

    def __call__(self, *args, **kwargs):
        # import ipdb;ipdb.set_trace()
        self.low_level()
        kwargs = self._initial(**kwargs)
        code = kwargs.pop('code')
        result = {}
        status = self._check_dangerous_code(code)
        if not status:
            result['status'] = status
            result['result'] = "Runtime Error"
            return result
        with self.compile_lock:
            self._write_code(code)
            self._compile()
        return self._run(**kwargs)

    def low_level(self):
        try:
            os.setuid(int(os.popen("id -u %s" % "nobody").read()))
        except:
            pass

    def _single_run_rule(self, input_file_index, path,
                         solution_id, problem_id, time_limited, memory_limited):
        return True, ""

    def _run(self, *args, **kwargs):
        problem_id = kwargs['problem_id']
        in_cases_path = os.path.join(self.cases_root_path, str(problem_id), 'in')
        in_cases_num = len(os.listdir(in_cases_path))
        out_cases_path = os.path.join(self.cases_root_path, str(problem_id), 'out')
        out_cases_num = len(os.listdir(out_cases_path))
        if in_cases_num != out_cases_num:
            print('warning', 'cases error')
        max_cost_time = 0
        max_cost_memory = 0
        for index in range(100):
            result = self._single_run_rule(input_file_index=index, path=in_cases_path, **kwargs)
            if result['result'] != 0:
                return {
                    'status': False,
                    'result': self.status_type.get(result['result'], "System Error")
                }
            status, status_type = self._judge(index, **kwargs)
            if not status:
                return {
                    'status': False,
                    'result': self.status_type.get(status_type, "System Error")
                }
            if max_cost_time < result["timeused"]:
                max_cost_time = result['timeused']
            if max_cost_memory < result['memoryused']:
                max_cost_memory = result['memoryused']
        return {
            'status': True,
            'result': 'Accepted',
            'time_limited': max_cost_time,
            'memory_limited': max_cost_memory
        }

    def _check_dangerous_code(self, code):
        return True

    def _judge(self, output_file_index, problem_id, **kwargs):
        out_cases_path = os.path.join(self.cases_root_path, str(problem_id), 'out/%s.out' % output_file_index)
        try:
            print(out_cases_path)
            with open(out_cases_path, 'r') as f:
                out_case = f.read().replace('\r', '').rstrip()
        except:
            return True, 0
        with open(self.user_out_path, 'r') as f:
            user_out = f.read().replace('\r', "").strip()
        if out_case == user_out:
            return True, 0
        if out_case.split() == user_out.split():
            return False, 4
        if out_case in user_out:
            return False, 6
        return False, 1


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
        self.work_filename = "main.py"

    def _initial(self, *args, **kwargs):
        kwargs['time_limited'] *= 2
        kwargs['memory_limited'] *= 2
        return kwargs

    def check_dangerous_code(self, code):
        support_modules = [
            're',
            'sys',  # sys.stdin
            'string',
            'scanf',
            'math',
            'cmath',
            'decimal',
            'numbers',
            'fractions',
            'random',
            'itertools',
            'functools',
            # Higher order functions and operations on callable objects
            'operator',
            'readline',
            'json',
            'array',
            'sets',
            'queue',
            'types',
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
                         problem_id, time_limited, memory_limited):
        command = "python3 %s" % os.path.join(self.work_dir, '__pycache__/main.cpython-37.pyc')
        main_exe = shlex.split(command)
        input_file_path = os.path.join(path, "%s.in" % input_file_index)
        input_file = open(input_file_path, 'r')
        temp_output_file = open(self.user_out_path, 'w')
        try:
            cfg = {
                'args': main_exe,
                'fd_in': input_file.fileno(),
                'fd_out': temp_output_file.fileno(),
                'timelimit': time_limited,  # in MS
                'memorylimit': memory_limited,  # in KB
            }
            self.low_level()
            result = lorun.run(cfg)
        except Exception as e:
            print(e)
            return {'result': -1}
        finally:
            input_file.close()
            temp_output_file.close()
        return result


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
