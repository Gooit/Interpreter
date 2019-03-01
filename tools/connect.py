import requests


code = """
a, b = input().split()
print(int(a)+int(b))
"""

data = {
    'code': code,
    'time_limited': 1000,
    'memory_limited': 32768,
    'problem_id': 1,
    'solution_id': 1,
}
url = "http://39.96.194.42:5000/python/"

res = requests.post(url=url, json=data)
print(res.status_code)
print(res.content)