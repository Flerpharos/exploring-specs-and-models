import math as M,re;F=float
def n(u):return{k:v for k,v in u.items()if v}
def mu(u,v):r=dict(u);[r.update({k:r.get(k,0)+w})for k,w in v.items()];return n(r)
def di(u,v):r=dict(u);[r.update({k:r.get(k,0)-w})for k,w in v.items()];return n(r)
def pu(u,p):return n({k:v*p for k,v in u.items()})
def fe(v):return str(int(v))if type(v)is F and v.is_integer()else str(v)
def sr(u):
 if not u:return"1"
 p,q=sorted(k for k,v in u.items()if v>0),sorted(k for k,v in u.items()if v<0)
 return("*".join(k if u[k]==1 else f"{k}^{fe(u[k])}"for k in p)or"1")+(f"/{'*'.join(k if u[k]==-1 else f'{k}^{fe(-u[k])}'for k in q)}"if q else"")
def ck(v):
 if not M.isfinite(v):raise Exception("Error: numeric result is not finite.")
 if type(v)is complex:raise Exception("Error: numeric result is not real.")
 return v
def cr(v):
 if type(v)is complex or not M.isfinite(v):raise Exception("Error: invalid relationship.")
 return v
def sf(b,e,s):
 try:return cr(s*(b**e))
 except Exception:raise Exception("Error: invalid relationship.")
class V:
 def __init__(s,m,u):s.m=ck(m);s.u=u
class E:
 def __init__(s):s.U,s.V,s.R,s.S=set(),{},{},set()
def cv(A,B,R):
 if A==B:return 1.0
 q,v=[((sr(A),),A,1.0)],{sr(A)}
 while q:
  w=[x for x in q if x[1]==B]
  if w:return sorted(w,key=lambda x:x[0])[0][2]
  nx=[]
  for p,u,s in q:
   for t,(f,b)in R.items():
    if u.get(t,0):e=u[t];nu=mu(di(u,{t:e}),pu(b,e));nx.append((p+(sr(nu),),nu,sf(f,e,s),t,0))
    if b:
     r=[u.get(x,0)/b[x]for x in b];z=[x for x in r if x]
     if z and len(set(x>0 for x in z))==1:e=min(abs(x)for x in z)*(1 if z[0]>0 else-1);nu=mu(di(u,pu(b,e)),{t:e});nx.append((p+(sr(nu),),nu,sf(f,-e,s),t,1))
  sl={}
  for p,nu,s,t,i in nx:
   su=p[-1]
   if su not in v:
    c=(p,t,i,s)
    if su not in sl or c<sl[su][0]:sl[su]=(c,nu)
  q=[(x[0][0],x[1],x[0][3])for x in sl.values()]
  for su in sl:v.add(su)
 raise Exception(f"Error: cannot convert {sr(A)} to {sr(B)}.")
def un(A,B,R):
 try:return A.m,B.m*cv(B.u,A.u,R),A.u
 except Exception:pass
 try:return A.m*cv(A.u,B.u,R),B.m,B.u
 except Exception:pass
 raise Exception(f"Error: cannot convert {sr(B.u)} to {sr(A.u)}.")
def cl(v):
 if not M.isfinite(v):raise Exception("Error: invalid formula.")
 return v
def lx(s):
 p=r'(?P<N>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)|(?P<I>[A-Za-z_][A-Za-z_0-9]*)|(?P<O>[+\-*/^()[\]])|(?P<W>\s+)'
 t=[(0,cl(F(m.group())))if m.lastgroup=='N'else(1,m.group())if m.lastgroup=='I'and re.fullmatch(r'[a-z][a-z_]*|[A-Z][A-Z_]*',m.group())else(2,m.group())if m.lastgroup=='O'else None for m in re.finditer(p,s)if m.lastgroup!='W']
 if None in t or sum(len(m.group())for m in re.finditer(p,s))!=len(s):raise Exception("Error: invalid formula.")
 return t
class P:
 def __init__(s,t,e,c):s.t,s.p,s.E,s.c=t,0,e,c;s.m="Error: invalid formula."
 def e(s,m=None):print(f"ERROR AT: {s.x()} in c={s.c} m={m}");raise Exception(m or s.m)
 def x(s):return s.t[s.p]if s.p<len(s.t)else(3,'')
 def a(s,y):
  if s.x()[1]==y:s.p+=1;return 1
 def ps(s):
  v=s.E1()
  if s.p<len(s.t):s.e()
  return v
 def E1(s):
  v=s.E2()
  while s.x()[1]in('+','-'):
   o=s.x()[1];s.p+=1
   if s.c:s.e()
   am,bm,u=un(v,s.E2(),s.E.R);v=V(am+bm if o=='+'else am-bm,u)
  return v
 def E2(s):
  v=s.E3()
  while s.x()[1]in('*','/'):
   o=s.x()[1];s.p+=1;v2=s.E3()
   if o=='*':v=V(v.m*v2.m,mu(v.u,v2.u))
   else:
    if not v2.m:s.e("Error: division by zero.")
    v=V(v.m/v2.m,di(v.u,v2.u))
  return v
 def E3(s):
  v=s.E4()
  if s.a('^'):
   v2=s.E3()
   if v2.u:s.e("Error: exponent must be scalar.")
   try:r=v.m**v2.m
   except Exception:s.e("Error: numeric result is not real.")
   if type(r)is complex:s.e("Error: numeric result is not real.")
   v=V(r,pu(v.u,v2.m))
  return v
 def E4(s):
  if s.a('+'):return s.E4()
  if s.a('-'):v=s.E4();return V(-v.m,v.u)
  if s.a('['):
   if s.c:s.e();
   v=s.E4()
   if v.u:s.e("Error: log argument must be scalar.")
   if v.m<=0:s.e("Error: log argument must be positive.")
   return V(M.log(v.m),{})
  if s.a(']'):
   if s.c:s.e();
   v=s.E4()
   if v.u:s.e("Error: exp argument must be scalar.")
   return V(M.exp(v.m),{})
  if s.a('('):
   v=s.E1()
   if not s.a(')'):s.e()
   return v
  t,vl=s.x()
  if t==0:
   s.p+=1;u={}
   if(s.x()[0]==1 and s.x()[1].islower())or s.x()[1]=='(':u=s.US()
   return V(vl,u)
  if t==1:
   s.p+=1
   if vl.islower():
    if s.c==0 and vl not in s.E.U:s.e(f"Error: unknown unit {vl}.")
    if s.c==1 and vl not in s.E.S:s.e(f"Error: unknown unit {vl}.")
    return V(1.0,{vl:1.0})
   if s.c==0:
    if vl not in s.E.V:s.e(f"Error: unknown variable {vl}.")
    return V(s.E.V[vl].m,s.E.V[vl].u)
   s.e(f"Error: unknown unit {vl}.")
  s.e()
 def US(s):
  u=s.UF()
  while s.x()[1]in('*','/'):o=s.x()[1];s.p+=1;u=(mu if o=='*'else di)(u,s.UF())
  return u
 def UF(s):
  t,vl=s.x()
  if t==1 and vl.islower():s.p+=1;u={vl:1.0}
  elif s.a('('):
   u=s.US()
   if not s.a(')'):s.e()
  else:s.e()
  if s.a('^'):
   sg=1
   if s.a('+'):pass
   elif s.a('-'):sg=-1
   t2,xp=s.x()
   if t2==0 and type(xp)is F and xp.is_integer():s.p+=1;u=pu(u,sg*int(xp))
   else:s.e()
  return u
 def OU(s):
  u=s.OU_()
  if s.p<len(s.t):s.e()
  return u
 def OU_(s):
  u=s.OP()
  while s.x()[1]in('*','/'):o=s.x()[1];s.p+=1;u=(mu if o=='*'else di)(u,s.OP())
  return u
 def OP(s):
  t,vl=s.x()
  if t==1 and vl.islower():
   s.p+=1
   if vl not in s.E.U:s.e(f"Error: unknown unit {vl}.")
   u={vl:1.0}
  elif t==0 and vl==1.0:s.p+=1;u={}
  elif s.a('('):
   u=s.OU_()
   if not s.a(')'):s.e()
  else:s.e()
  if s.a('^'):
   sg=1
   if s.a('+'):pass
   elif s.a('-'):sg=-1
   t2,xp=s.x()
   if t2==0 and type(xp)is F and xp.is_integer():s.p+=1;u=pu(u,sg*int(xp))
   else:s.e()
  return u
class C:
 def __init__(s):s.E=E()
 def r(s,l):
  o=[]
  for y in l:
   if not y.strip():continue
   try:
    if y.startswith("unit:"):
     u=y[5:].strip()
     if not u or not re.fullmatch(r'[a-z][a-z_]*',u):raise Exception("Error: invalid unit name.")
     s.E.U.add(u)
    elif y.startswith("set:"):
     p=y[4:].split(":",1)
     if len(p)!=2:raise Exception("Error: invalid command syntax.")
     v,f=p[0].strip(),p[1].strip()
     if not v or not re.fullmatch(r'[A-Z][A-Z_]*',v):raise Exception("Error: invalid variable name.")
     if not f:raise Exception("Error: invalid formula.")
     s.E.V[v]=P(lx(f),s.E,0).ps()
    elif y.startswith("relate:"):
     p=y[7:].split(":",2)
     if len(p)!=3:raise Exception("Error: invalid command syntax.")
     t,l_,f=p[0].strip(),p[1].strip(),p[2].strip()
     if not t or not re.fullmatch(r'[a-z][a-z_]*',t):raise Exception("Error: invalid unit name.")
     sz=[x.strip()for x in l_.split(',')]
     if not l_ or any(not x for x in sz)or len(set(sz))!=len(sz):raise Exception("Error: invalid unit list.")
     for x in sz:
      if not re.fullmatch(r'[a-z][a-z_]*',x)or x not in s.E.U:raise Exception("Error: invalid unit list.")
     if t in sz:raise Exception("Error: invalid relationship.")
     if not f:raise Exception("Error: invalid formula.")
     s.E.S=set(sz);vl=P(lx(f),s.E,1).ps()
     if not vl.m:raise Exception("Error: invalid relationship.")
     if any(k not in s.E.S for k in vl.u):raise Exception("Error: invalid relationship.")
     s.E.U.add(t);s.E.R[t]=(vl.m,vl.u)
    elif y.startswith("evaluate:"):
     p=y[9:].rsplit(":",1)
     if len(p)==1:
      f=p[0].strip()
      if not f:raise Exception("Error: invalid formula.")
      vl=P(lx(f),s.E,0).ps();o.append(f"{fe(vl.m)} {sr(vl.u)}")
     else:
      f,of=p[0].strip(),p[1].strip()
      if not f:raise Exception("Error: invalid formula.")
      if not of:raise Exception("Error: invalid output unit.")
      try:t_o=lx(of)
      except Exception:raise Exception("Error: invalid output unit.")
      po=P(t_o,s.E,2);po.m="Error: invalid output unit.";ou=po.OU()
      vl=P(lx(f),s.E,0).ps();sc=cv(vl.u,ou,s.E.R);o.append(f"{fe(ck(vl.m*sc))} {sr(ou)}")
    else:raise Exception("Error: unknown command.")
   except Exception as e:
    import traceback; traceback.print_exc()
    o.append(str(e))
  return o
def run(cmds):return C().r(cmds)

if __name__ == "__main__":
    print(run(["unit:m", "evaluate:2 m/s"]))
    print(run(["unit:m", "unit:s", "evaluate:2 m/s"]))
    print(run(["unit:cm", "unit:m", "relate:cm:m:0.01 m", "evaluate:1 m:cm"]))
    print(run(["unit:cm", "unit:m", "relate:cm:m:0.01 m", "evaluate:100 cm:m"]))
    print(run(["unit:kg", "unit:m", "unit:s", "unit:n", "relate:n:kg,m,s:kg*m/s^2", "evaluate:1 n:kg*m/s^2"]))
