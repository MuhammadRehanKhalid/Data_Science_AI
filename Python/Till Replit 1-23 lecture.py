# -------------------First Class-print---------------#
print('Hello World')
print('Muhammad Rehan khalid')
# -----------------------------
print("""Muhammad Rehan Khalid
          is a very Nice Man.
              He is a man of his words,
              he never disobeys his father or
                  mother's decisions.
                      Someone wants to destory his
                      reputaion by backmouthing him.""")

print(' different type of the words can getout')
# -------------------2nd Class-input-------------#
input('whats your name?: ')
myname = input('What is your Name?: ')
print(myname)
print()

age = input("What is your age?: ")
print("You achieved such position in this little age.")
name = input("what is your Name?: ")
print("Thats a nice name.")
area = input("in whihc city do you live?: ")
print("This city is wellknown for its trading centers.")
print()
print("So our Name is ")
print(name)
print("and you are ")
print(age)
print("year's old")
print("You told a detailed intro about your homecity which is ")
print(area)
# -------------------3rd Class-concatenation----------------#
N = input("what is your Name?: ")
F = input("What food are you eating?: ")
C = input("How your food is coocked?: ")
print(N, "going to crush", F, "lokking declicious", C, "with susage")

N = input("what is your Name?: ")
F = input("What food are you eating?: ")
C = input("How your food is coocked?: ")
D = input("name of the DIY?: ")
FD = input("Food description?: ")
print(N, "is eating", F, C, FD, "on a ",D)
# -----------------4th Class-StoryandLettercolorchanging0----#
print("=== Your adventure Story ===")
print("""You Will be asked a bunch of Questions Then we will you Up an amazing with You as the star""")
print()
ame = input("Your name: ")
enemy = input("Your enemy name: ")
superpower = input("Your super power: ")
print()
print( "Story starts as our", name, "reaches the foreboding castle")
print("Suddenly as bolt of lightening strikes in foots od the", name)
print(name, "fought the final fierce battle with his most deadliest counter",
      enemy,"who was clearly missing that", name, "has the super powers of",
      superpower, "which means the our hero will win quite easily")
# change colors
print(name, "fought the final", "\033[34m", "fierce battle", "\033[0m", "with his most deadliest counter",
      enemy, "who was clearly missing that", name, "has the super powers of", "\033[31m",
      superpower, "\033[0m" "which means " "the our hero " "will win quite " "easily")
# ---------------5thClass-ifelse------------------#
print("It's a securoty Check, Please! Cooperate")
myname = input("what's Your Name?")
if myname == "Rehan":
    print("Welcome Boss.")
    print("It's pleasure to see you")
else:
    print("\033[31m","Please", "\033[0m", " leave the perimiter, optherwise strict action will be taken")
# ---------------6th Class-Elif-------------------#
myname = input("Your name: ")
if myname == "Rehan":
    print("Welcome Boss.")
    print("It's pleasure to see you")
elif myname == "Laraib": print(""""You are strcitly prohibited to work here. leave the
perimeter immediately.""")
else: print("\033[31m", "Please", "\033[0m", " leave the perimiter, otherwise strict action will be taken")

admin = input("Admin : ")
password = input(" Password: ")

if admin == "Rehan" and password == "12345":
    print("Greeting's Rehan!")
    print("You could have make your way without password")
    print("Have a great day.")
elif admin == "Laraib" and password == "123456":
    print(" Welcome Mam. Please Proceed to the next Check Point")
else:
    print("You are trespassing Gvot Property!")
    print("Please with immediate effect")
    print("Other wise forces are on the way.")
# ---------------7th Class-Nesting withif if ----------------#
person = input('Whta is your Favourite Personamlity: ')
if person == "allama iqbal":
    print("Hurray! Correct Answer")
elif person == "quaid-e-azam":
    print("That's right but, speciyit according to Poetry")
    poet = input("if poet, name?: ")
    if poet == 'allama iqbal':
        print('Thats Correct')
    else:
        print('Try luck next time.')
else:
    print("you are not a litterary person")
# code errors
tvShow = input("What is your favourite tv show? ")
if tvShow == "peppa pig":
    print("Ugh, why?")
    faveCharacter = input("Who is your favourite character? ")
    if faveCharacter == "daddy pig":
        print("Right answer")
    else:
        print("Nah, Daddy Pig's the greatest")
elif tvShow == "paw patrol":
    print("Aww, sad times")
else:
    print("Yeah, that's cool and all…")
# --------------8th Class----Project------------#


# --------------9th Class----Numbers------------#
myscore = int(input('What  is your Number?: '))
if myscore > 1000:
    print('Winner')
else:
    print("try again!")
score = int(input("What was your score on the test?"))
if score >= 80:
    print("Not too shabby")
elif score > 70:
    print("Acceptable.")
else:
    print("Dude, you need to study more!")

# era generator
gen = int(input("What's your birth year? : "))
if 1883 <= gen <= 1900:
    print('Lost Generation')
elif 1901 <= gen <= 1927:
    print('Greatest Generation')
elif 1928 <= gen <= 1945:
    print('Silent Generation')
elif 1946 <= gen <= 1964:
    print('Baby Boomers')
elif 1965 <= gen <= 1980:
    print('Generation X')
elif 1981 <= gen <= 1996:
    print('Millennials')
elif 1997 <= gen <= 2012:
    print('Generation Z')
elif 2013 <= gen <= 2023:
    print('Generation Alpha')
else:
    print("Record Not Foun.")

# --------------10th Class-----Bitofmath----------------#
adding = 9 + 3
print(adding)
module = 9 % 3
print(module)
power = 3 ** 3
print(power)
divisor = 27 // 9
print(divisor)

fair = float(input('From Gutwala to Lahore:'))
numberofpeople = int(input('Number of People Travelling?: '))

each = fair / numberofpeople
print("You will all pay", each, 'each person')
each = round(each, 3)

spent = float(input("Bill of your's at Dr. Saucy: "))
print('Thank YOu Sir for Eating at Dr. Saucy')
tip = float(input("Would you like to tip for service?: "))
tip = spent / tip / 10
answer = round(tip, 2)
print(answer, "$")
# -------------11th Class-----Days in a Year------------#
days = int(input("Days in a year?: "))
days_in_year = 365
days_in_leapyear = 366
hours_in_a_day = 24
minutes_in_hour = 60
seconds_in_minutes = 60
if days <= 365:
    seconds = days_in_year*hours_in_a_day*minutes_in_hour*seconds_in_minutes
    print("Seconds in a Simple Year are", seconds)
else:
    seconds = days_in_leapyear*hours_in_a_day*minutes_in_hour*seconds_in_minutes
    print("Seconds in a leap year are", seconds)
# -------------- 11th Class-- Year Code Generation--------#
print("100 Days of Code QUIZ")
print()
print("How many can you answer correctly?")
ans1 = input("What language are we writing in?")
if ans1 == "python":
    print("Correct")
else:
    print("Nope🙈")
ans2 = int(input("Which lesson number is this?"))
if ans2>12:
    print("We're not quite that far yet")
else:
    print("We've gone well past that!")
# ---------------------12th Class ------------------#
print("100 Days of Code QUIZ")
print()
print("How many can you answer correctly?")
ans1 = input("What language are we writing in?")
if ans1 == "python":
    print("Correct")
else:
    print("Nope🙈")
ans2 = int(input("Which lesson number is this?"))
if ans2>12:
    print("We're not quite that far yet")
elif ans2 == 12:
    print("That's right!")
else:
    print("We've gone well past that!")
# ---------------------- 13th Class ---------------------#
print("""Helo Class
  Welcome to the  Mark Sheet.
  'Now you are going to get your result.'
  Are you excited!!😎😎🤩🤩""")
print()
s1 = "chemistry"
s2 = "biology"
s3 = "physics"
s4 = "english"

name = input("What is your name?: ")
if name == "Mubeen" or name == "hassan" or name == "Bedar" or name == "Mussab":
    print("🤩Welcome to the Marks Sheet🤩", name)
    print("It looks like you are enrolled in batch number 231.")
    sub_name = input("Which subject are you looking for?: ")
    if sub_name == s1 or sub_name == s2 or sub_name == s3 or sub_name == s4:
        print("Next.")
    else:
        print("Try Something else.")
    print("Grade Calculator")
    total_marks = int(input("Maximum Marks for the Subject: "))
    obtained_marks = int(input("marks You obtained: "))
    grade = round(float(obtained_marks / total_marks) * 100, 2)
    print(grade, "%")
    if 90 <= grade <= 99.9:
        print("A+")
    elif 80 <= grade <= 89.9:
        print("A-")
    elif 70 <= grade <= 79.9:
        print("B")
    elif 60 <= grade <= 69.9:
        print("C")
    elif 50 <= grade <= 59.9:
        print("D")
    elif 40 <= grade <= 49.9:
        print("U")
    elif grade < 40:
        print("Fail")
    else:
        print("No Result.")
else:
    print("Wrong credentials added.")
print('You got ', grade, ' % out of 100 %.')
if grade >= 90.99:
    print("That's a fabulous score")
elif grade <=60.99:
    print("You need to study hard")
else:
    print("That's not a bad score, You can improve much after exams.")
# ------------------------------------#

# -----------------Start of --------------------#

#------------------ Class 14-rock paper scissor-----------#
from getpass import getpass as input

print("E P I C    🪨  📄 ✂️    B A T T L E ")
print()
print("Select your move (R, P or S)")
print()

Player_1 = input("Player 1 > ")
print()
Player_2 = input("Player 2 > ")
print()

if Player_1=="R":
  if Player_2=="R":
    print("You both picked Rock, draw!")
  elif Player_2=="S":
    print("Player1 smashed Player2's Scissors into dust with their Rock!")
  elif Player_2=="P":
    print("Player1's Rock is smothered by Player2's Paper!")
  else:
    print("Invalid Move Player 2!")
elif Player_1=="P":
  if Player_2=="R":
    print("Player2's Rock is smothered by Player1's Paper!")
  elif Player_2=="S":
    print("Player1's Paper is cut into tiny pieces by Player2's Scissors!")
  elif Player_2=="P":
    print("Two bits of paper flap at each other. Dissapointing. Draw.")
  else:
    print("Invalid Move Player 2!")
elif Player_1=="S":
  if Player_2=="R":
    print("Player 2's Rock makes metal-dust out of Player1's Scissors")
  elif Player_2=="S":
    print("Ka-Shing! Scissors bounce off each other like a dodgy sword fight! Draw.")
  elif Player_2=="P":
    print("Player1's Scissors make confetti out of Player2's paper!")
  else:
    print("Invalid Move Player 2!")
else:
  print("Invalid Move Player 1!")

# -----------------------------Class 15--- Loop------#
counter = 1
while counter < 12:
    print(counter)
    counter += 1
st_p = ""
while st_p != "yes":
    print("😒")
    st_p = input("exit?: ")

#------------- Class-15----loop Game----------------#
exit = ""
while exit != "yes":
    print("Animal Game")
    print()
    print("""You can choose animal
    Of your choice and we will
    tell you its voice""")
    print("""Animal List:
              1) Cat
              2) Dog
              3) Lion
              4) Duck
              5) Frog
              6) Deer""")
    animal_name = input("Animal Name: ")
    if animal_name == "Cat" or animal_name == "cat":
        print("Cats are known For their meows, purrs, hisses, and growls")
        print("🐈 Meeeooowww meeeoowww !!!!")
    elif animal_name == "Dog" or animal_name == "dog":
        print("Dogs are known For their bark, growl, and woofs")
        print("🐕 Woof Woof !!!!")
    elif animal_name == "Lion" or animal_name == "lion":
        print("Lions are known For their roar, roar, and roar")
        print("🦁 Roar !!!")
    elif animal_name == "Duck" or animal_name == "duck":
        print("Ducks are known For their quack, quack, and quack")
        print("🦆 Quack Quack !!!!")
    elif animal_name == "Frog" or animal_name == "frog":
        print("Frog are known For their Corak")
        print("🐸 Corakkkk Croakkkkkkk !!!")
    elif animal_name == "Deer" or animal_name == "deer":
        print("Deer are known For their Bray, Hee-Haw")
        print("🦌 Brayyyyyyyy !!!!")
    else:
        print("Please choose a animal")
    exit = input('Exit?: ')
# ---------------------------Class-16---True Loop----------#
while True:
    print("This Program will be running, until you press Ctrl+ F4")
    goagain = input("Do you want to go again? ")
    if goagain == "No" or goagain == "no":
        break
print("I was having fun! ")

while True:
    print ("This Program Will be running if not stopped")
    goagain_2 = input("Do you want to Stop This?")
    if goagain_2 != "no" or goagain_2 != "No":
        break
print(" I was having a Good Day!")
Error
counter = 0
while True:
  answer = int(input("Enter a number: "))
  print("Adding it up!")
  counter += answer
  print("Current total is", counter)
  addAnother = input("Add another? ")
  if addAnother == "no":
    break
print("Bye!")
Error
counter = 45
while True:
    answer = int(input("Enter a number: "))
    print("Adding it up!")
    counter += answer
    print("Current total is", counter)
    addAnother = input("Add another? ")
    if addAnother == "no" or addAnother == "No":
        break
print("Bye!")
while True:
    color = input("Enter a color: ")
    if color == "red" or color == "Red":
        break
    else:
        print("Cool color!")
print("I don't like red")

challange
print("Welcome to Name the Song Lyric")
print()
print("Figure out the missing word as quickly as you can!")
print()

counter = 1
while True:
    lyrics = input("Bashre Insaan ke banaye kallay ______ ")
    if lyrics == "qanoon" or lyrics == "Qanoon":
        print("Thanks for playing!")
    else:
        print("Nope! Try again!")
        counter += 1
    if lyrics == "qanoon" or lyrics == "Qanoon":
        break
print("You got the correct lyrics in", counter, "attempt(s).")


print("let's see if you can pace up with my song loving instintcs")
print("Fill In the blanks.")

counter = 1
while True:
    f_1 = input("Never going to ______ you up: ")
    if f_1 == "miss" or f_1 == "Miss":
        print("You got it!")
    else:
        print("Nope! Try again!😔😔")
        counter += 1
    if f_1 == "miss" or f_1 == "Miss":
        break
print("Thanks for playing!🤩🤩🤩🤩❤️❤️")
print("You got the correct lyrics in", counter, "attempt(s).")
# ---------------------------Class-17---Loop- Exit , Continue, Break---------#
from getpass import getpass as input

print("Welcome To the Most amazing and ")
print("Epic 🪨   📄 ✂️ Battle")
print()
print("""Please Choose Your Move Wisely.
      Chose R for Rock,
      P for Paper
      and S for Scissors"""
      "")
p1_score = 0
p2_score = 0
while True:
  player_1 = input("Player 1 Move: ")
  player_2 = input("Player 2 Move: ")

  if (player_1 == "R"):
    if (player_2 == "P"):
      print("Player_1 Rock was Smoothered by the Player_2 Paper.")
      p2_score += 1
    elif (player_2 == "S"):
      print("Player_1 Rock destoryed the Player_2 scissor.")
      p1_score += 1
    elif (player_2 == "R"):
      print("Both Players Choose the Rock, it's a Draw.")
    else:
      print("It's an invalid Move Player_2")
  elif (player_1 == "P"):
    if (player_2 == "P"):
      print("Both Players Choose the Paper, it's a Draw.")
    elif (player_2 == "S"):
      print("Player_1 Paper was destoryed by the Player_2 scissor.")
      p2_score += 1
    elif (player_2 == "R"):
        print("Player_2 Rock was Smoothered by the Player_1 Paper.")
        p1_score += 1
    else:
        print("It's an invalid Move Player_2")
  elif (player_1 == "S"):
    if (player_2 == "P"):
      print("Player_2 Paper was destoryed by the Player_1 scissor.")
      p1_score += 1
    elif (player_2 == "S"):
      print("Both Players Choose the Scissor, it's a Draw.")
    elif (player_2 == "R"):
      print("Player_2 Rock destoryed by the Player_1 scissor.")
      p2_score += 1
  print("player_1 scored ", p1_score)
  print("player_2 scored ", p2_score)
  if (p1_score == 3):
    print("The game is over, you've won Player_1. Hurray 🤩🤩")
    exit()
  elif (p2_score == 3):
    print("The game is over, you've won Player_2. Hurray 🤩🤩")
    exit()
  else:
    continue

# ----------------------------Class 18---Functions------------------- #
counter = 0
while True:
    name = input("What is your name?: ")
    if name == "Rehan" or name == "rehan":
        print("Great!")
        break
    else:
        print("Sorry, ", name, "is not a valid name.")
        counter += 1
        continue
print("You Completed it in ", counter, " rounds.")
#------------------Class-19--for loop---------------------- #
for counter in range(10):
    print(counter)

for i in range(10):
    print(i)
total = 0
for number in range(100):
    total += number
    print(total)

for days in range(7):
    print("Day",days+1)
total = 10
for counter in range(100):
    total += counter
    print(total)


L = 1000
A = 0.05
for x in range(10):
  L += (L*A)
  print("Year", x+1, "is", round(L,3),"total.")

# ------------------Class-20-For Loop----Range----#
for i in range(1,11):
    print(i)
for i in range(1,20,2):
    print(i)

start = int(input("Write the start value: "))
end = int(input("Write the input value: "))
incre = int(input("Write the increament value: "))
for x in range(start,end,incre):
    print(x)

# -------------Class-21-For loop Project Gae ---------#
exit = ""
while exit != "no":
    print("Welcome to Table Game")
    print()
    print(
        "Please Choose a Multiple of a number, and I will give you 10 multiples of that number."
    )
    print()
    multiple = int(input("Please enter a number: "))
    print()
    counter = 0
    for z in range(1, 11):
        answer = multiple * z
        print(multiple, "x", z)
        y_answer = int(input("Please enter the answer: "))
        if y_answer == answer:
            print("Hurray you nailed it!")
            counter += 1
        else:
            print("Sorry, your answer is incorrect. Correct answer is", answer)
    if counter == 10:
        print("You won! you gussed the all 10, 🤩❤️😎")
        print("Congratulations, You are a genious")
    else:
        print("You guessed", counter, "correct answers out of 10, �����️���")
    exit = input("Do you want to play again?: ")

# -----------------Class-22------------------------#
import random as rd

my_number = rd.randint(1, 50)
print(my_number)

for i in range(10):
    myNumber = rd.randint(1, 100)
    print(myNumber)

import random as rd

print("Welcome to Number Guess Game")
print()
print("Choose a number between 1 and 100")
print()
# for i in range(1):
myNumber = rd.randint(1, 100)
# print(myNumber)
num_1 = myNumber
counter = 0
while True:
    guess_1 = int(input("Guess the number: "))
    if guess_1 == num_1:
        print("Thats the  right number")
        print("You won!")
        break
    if guess_1 < 0:
        print("Now you tried to play us oversmart")
        print("You lost! Game Over.")
        exit()
    elif guess_1 > num_1:
        print("Number is very high!")
        counter += 1
    elif guess_1 < num_1:
        print("Number is very low!")
        counter += 1
    else:
        print("Enter the Coorect number")
print("You gueesed the correct number after ", counter, "wrong attempts")

# -----------------Class-23-----def- function- subroutine------------------#
def rehan():
    import random as rd

    dice = rd.randint(1, 6)
    print("Dice Rolled: ", dice)


for i in range(0, 6):
    rehan()


def print_favoritecolor():
    print("My favorite color is red.")


print_favoritecolor()
from getpass import getpass as input

print("Welcome to Replit.")
print()
print("Replit Login  System")
print()

cont = 0


def login(cont=0):
    while True:
        user_name = input("Enter your username: ")
        password = input("Enter your password: ")
        if user_name == "rehan" and password == "fukoff":
            print("Welcome to Replit!")
            break
        else:
            print("Invalid username or password.")
            cont += 1
            continue
    if cont == 3:
        print("Sorry, you are out of attempts. Please try again.")
        exit()

login()

#rd.randint(input("Enter the start value: "), input("Enter the end value:"))
