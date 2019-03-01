import os
import random


problem_id = 1
for i in range(1000):
    a = random.randint(-1000000, 1000000)
    b = random.randint(-1000000, 1000000)
    data = "%s %s" % (a, b)
    path = 'cases/%s/in/' % problem_id
    if not os.path.exists(path):
	    os.makedirs(path) 
    with open(path + "%s.in" % i, 'w') as f:
        f.write(data)
    
