import sys
import os.path
import logging

import turtle
import math,random

def drawSquare(x,y,l,colour):
    turtle.penup()
    turtle.goto(x,y)
    turtle.pendown()    
    if colour < 0:
        color = 'black'
    else:
        color = 'white'
    r = l / math.sqrt(2)
    turtle.begin_fill()
    turtle.color(color)
    turtle.circle(r,steps = 4)
    turtle.end_fill()
    
def drawEdge(start):
    length = 2 * abs(start) + 6
    turtle.penup()
    turtle.goto(start - 3,start - 3)
    turtle.pendown()
    turtle.pensize(3)
    for d in range(4):
        dirction = d * 90
        turtle.setheading(dirction)
        turtle.forward(length) 
    turtle.right(315)
    turtle.pensize(1)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s')
    logging.root.setLevel(level=logging.INFO)
       
    programme = os.path.basename(sys.argv[0])
    logger = logging.getLogger(programme)
    logger.info('Running %s ...' % ''.join(sys.argv))
    
    
    
    size = 18 # eval(raw_input("Please input the size of the chessboard: "))
    length = 40 #eval(raw_input('Please input the size of the blank: '))
    
    logger.info("The size of the chessboard is " + str(size) + " X " + str(size) + ", each blank is " + str(length)+ " X " + str(length))
    
    start_y =  size * length / 2 
    start_x = - start_y
    
    turtle.hideturtle()  
    turtle.speed(100)
    
    drawEdge(start_x)    
    
    for y in range(1,size + 1,1):        
        for x in range(size):
            color = random.randint(-10, 10)
            pos_x = start_x + x * length
            pos_y = start_y - y * length
            drawSquare(pos_x,pos_y,length,color)
        
        
        
    turtle.done()
            
    