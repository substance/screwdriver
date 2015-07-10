import inspect

level = 0

def indent():
  global level
  level = level+1

def dedent():
  global level
  level = level-1

def log(msg):
  global level
  print('{i} {m}'.format( i='..'*level, m=msg ))
