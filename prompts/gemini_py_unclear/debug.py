import re
p=r'(?P<N>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)|(?P<I>[A-Za-z_][A-Za-z_0-9]*)|(?P<O>[+\-*/^()[\]])|(?P<W>\s+)'
s="2 m/s"
t=[(0,float(m.group()))if m.lastgroup=='N'else(1,m.group())if m.lastgroup=='I'and re.fullmatch(r'[a-z][a-z_]*|[A-Z][A-Z_]*',m.group())else(2,m.group())if m.lastgroup=='O'else None for m in re.finditer(p,s)if m.lastgroup!='W']
print(t)
print(None in t)
print(sum(len(m.group())for m in re.finditer(p,s)))
print(len(s))
