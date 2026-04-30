user_input = int(input("Enter your choice \n1. rock, \n2. paper, \n3. scissors: \n"))
# print("You chose: " + user_input)
import random
c_input = random.choice("123")
computer_choice = int(c_input)
# print("Computer chose: " + computer_choice)

if user_input == computer_choice:
    print("It's a tie!")
elif user_input == 1 and computer_choice == 3 | user_input == 2 and computer_choice == 1 | user_input == 3 and computer_choice == 2:
    print("User win!")
elif user_input == 1 and computer_choice == 2 | user_input == 2 and computer_choice == 3 | user_input == 3 and computer_choice == 1:
    print("Computer win!")
else:
    print("Invalid input! Please enter 1, 2, or 3.")
    