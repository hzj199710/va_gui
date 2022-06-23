import pandas as pd

nn = 'Z:/2022/05/18/AlarmPic[2][20220518163544].jpg'

tt = nn.split('/')
nn = '\\'.join(tt)
print(nn)