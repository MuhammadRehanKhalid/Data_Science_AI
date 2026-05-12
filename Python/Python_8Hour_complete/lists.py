users = ['rehan', 'mohammad', 'sara', 'ali']
data = ['manager', 'developer', 'designer', 'tester']

# employer
employer = []

print("rehan" in employer)

print(users[-1])

print(users.index("sara"))

print(users[:2])
print(len(users))
users.append("Iqra")
users += ["bedar",'mussab']
print(users)
users.extend(['hassan', 'hussain'])
print(users)
users.insert(2, "hassan")
print(users)
users[2:2] = ["mujii", "khuji"]
print(users)
users.remove("hassan")
print(users)
users.pop()
print(users)
del users[1]
print(users)

data.clear()
print(data)

users.sort()
print(users)
