


import random
for i in range(1000):
    a = random.randint(-1000000, 1000000)
    b = random.randint(-1000000, 1000000)
    data = "%s %s" % (a, b)
    with ('cases/1/in/'+i+".in", 'w') as f:
        f.write(data)
    