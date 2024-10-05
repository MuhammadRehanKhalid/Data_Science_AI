import turtle
t = turtle.Turtle()
t.screen.bgcolor("black")
t.pensize(2)
t.color("green")
t.left(90)
t.backward(100)
t.speed(200)
t.shape("turtle")

def tree(x):
    if x < 10:
        return
    else:
        t.forward(x)
        t.color("red")
        t.circle(2)
        t.color("brown")
        t.left(30)
        tree(3*x/4)
        t.right(60)
        tree(3*x/4)
        t.left(30)
        t.backward(x)
tree(100)
turtle.done()

