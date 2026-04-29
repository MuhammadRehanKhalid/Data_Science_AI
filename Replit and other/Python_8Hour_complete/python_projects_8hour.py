# name  = "Rehan"
# print("Hello " + name)

# name += "!"
# print("Hello " + name)
# decade = str(1980)
# print(type(decade))

# print("I like the music from the "+decade+"!")
# #print(f"I like the music from the {decade}!")
# # complex numbers
# com_val = 2 + 3j
# print(com_val)
# print(type(com_val))
# print(com_val.real)
# print(com_val.imag)

# import math
# print(math.pi)
# gpa = 3.87
# print(math.sqrt(16))
# print(math.ceil(gpa))
# print(math.floor(gpa))
# # casting a string to a number
# zipcode = "90210"
# print(int(zipcode))


# game
from random import random
import sys
import random
playerchoice = input("Enter .. \n 1. for Rock, \n 2. for Paper, \n 3. for Scissors: \n")
player = int(playerchoice)
if player < 1 | player > 3:
    sys.exit("You have to chose between 1 and 3")
    
computerchoice = random.choice("123")
computer = int(computerchoice)

print("Computer chose: " + computerchoice)
print("Player chose: " + playerchoice)

if player == computer:
    print("It's a tie!")
elif (player == 1 and computer == 3) or (player == 2 and computer == 1) or (player == 3 and computer == 2):
    print("Player wins!")
else:
    print("Computer wins!")