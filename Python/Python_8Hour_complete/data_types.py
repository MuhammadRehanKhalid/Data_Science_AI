# # string data types
# # literal asignment
# first =  "dave"
# last  = "Gray"
# print(type(first))
# print(type(first) == str)
# print(isinstance (first, str)
#       )
# print(
#     "a" in ("a","b","c","d","e","d")
# )

class Animal:
    pass
class Dog(Animal):
    pass
class Bird:
    pass
class sparrow(Bird):
    pass
dog  = Dog()
print(isinstance(dog, Animal))
print(isinstance(dog, Bird))