import numpy as np, json, wave
import sys
V=sys.argv[1]; info=json.load(open(f'info_{V}.json')); SR=44100; T=info['DUR']; n=int(T*SR); rng=np.random.default_rng(11)
def z(): return np.zeros(n,np.float32)
def add(buf,x,t,g=1.0):
    s=int(t*SR)
    if s>=n: return
    e=min(n,s+len(x)); buf[s:e]+=x[:e-s]*g
def ma(x,k):
    return np.convolve(x,np.ones(k)/k,'same')
def hp(x,k): return x-ma(x,k)
bpm=132; spb=60/bpm; s16=spb/4
# instruments
def kick():
    t=np.arange(int(.42*SR))/SR; f=45+110*np.exp(-t*30); ph=2*np.pi*np.cumsum(f)/SR
    return (np.sin(ph)*np.exp(-t*6.5)+0.3*np.sin(ph)*np.exp(-t*60)).astype(np.float32)
def clap():
    out=np.zeros(int(.25*SR),np.float32)
    for d in (0,.012,.024):
        nn=rng.standard_normal(int(.2*SR)); tt=np.arange(len(nn))/SR
        b=hp(ma(nn,3),40)*np.exp(-tt*(30 if d<.02 else 14)); s=int(d*SR); out[s:s+len(b)]+=b[:len(out)-s]*.5
    return out
def hat(open_=False):
    L=.22 if open_ else .05; nn=rng.standard_normal(int(L*SR)); tt=np.arange(len(nn))/SR
    return (hp(nn,4)*np.exp(-tt*(14 if open_ else 80))*.22).astype(np.float32)
def note(m): return 440*2**((m-69)/12)
def pluck(f,L=.18):
    t=np.arange(int(L*SR))/SR; x=sum(np.sign(np.sin(2*np.pi*f*k*t))/k for k in (1,))*.5+np.sin(2*np.pi*f*2*t)*.25
    return (ma(x,4)*np.exp(-t*16)).astype(np.float32)
def bassn(f,L):
    t=np.arange(int(L*SR))/SR; x=np.tanh(2.5*np.sin(2*np.pi*f*t))+.4*np.sin(2*np.pi*f/2*t)
    return (ma(x,8)*np.minimum(1,t*80)*np.exp(-t*2.2)).astype(np.float32)
def padc(ms,L):
    t=np.arange(int(L*SR))/SR; x=np.zeros(len(t))
    for m in ms:
        for dt in (-0.12,0,0.12): x+=np.sin(2*np.pi*note(m+dt)*t)+.3*np.sin(2*np.pi*note(m+dt)*2*t)
    env=np.minimum(1,t/0.4)*np.minimum(1,(L-t)/0.4); return (x*env*.018).astype(np.float32)

SS=info['SS']; VS=info['VS']; PT=info['PRICE_T']; ST=info['STRIKE_T']; BT=info['BTN_T']
CH=[(53,[53,56,60]),(49,[49,53,56]),(56,[56,60,63]),(51,[51,55,58])]
drums=z(); bass=z(); arp=z(); pad=z(); side=np.ones(n,np.float32); K=kick(); C=clap()
bar=4*spb; nb=int(T/bar)+1
def mode(t):
    if t>=T-1.4: return 'out'
    if ST-.35<=t<PT: return 'break'
    if t<SS[3]: return 'half'
    return 'full'
for b in range(nb):
    t0=b*bar; root,ch=CH[b%4]; add(pad,padc(ch,bar+.3),t0,1.2)
    for q in range(16):
        tq=t0+q*s16
        if tq>=T: break
        m=mode(tq); seq=[0,2,1,2,0,2,1,2,0,2,1,2,0,1,2,1]
        if m!='out': add(arp,pluck(note(ch[seq[q]]+12)),tq,.5 if m=='full' else .3)
        if m in('half','full') and q%4==0:
            add(drums,K,tq,.95 if m=='full' else .75); s=int(tq*SR); L=int(.18*SR); e=min(n,s+L); side[s:e]=np.minimum(side[s:e],np.linspace(.25,1,L)[:e-s])
        if m=='full':
            if q in (4,12): add(drums,C,tq,.8)
            if q%4==2: add(drums,hat(True),tq,.65)
            elif q%2==1: add(drums,hat(),tq,.8)
            if q in (14,15) and b%2==1: add(drums,hat(),tq,.9)
            if q%2==0 and q%4!=0: add(bass,bassn(note(root-24),s16*2),tq,.6)
            if q%4==0: add(bass,bassn(note(root-24),s16*1.5),tq,.4)
        if m=='half':
            if q%2==1: add(drums,hat(),tq,.5)
            if q%8==0: add(bass,bassn(note(root-24),bar/2),tq,.45)
music=drums+bass*side+arp*(.6+.4*side)+pad
fx=z()
def riser(L=1.2):
    t=np.arange(int(L*SR))/SR; nn=rng.standard_normal(len(t)); y=np.zeros(len(t))
    seg=len(t)//12
    for i in range(12):
        k=max(2,int(20-i*1.6)); y[i*seg:(i+1)*seg]=hp(nn,k)[i*seg:(i+1)*seg]
    return (y*(t/L)**2*.35).astype(np.float32)
def boom():
    t=np.arange(int(1.2*SR))/SR; f=38+60*np.exp(-t*8); x=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*3.2)
    nn=rng.standard_normal(len(t))*np.exp(-t*25)*.3; return (x*.9+ma(nn,6)).astype(np.float32)
def whoosh(L=.5,up=True):
    t=np.arange(int(L*SR))/SR; nn=rng.standard_normal(len(t)); env=np.sin(np.pi*t/L)**2
    lo=ma(nn,10); hi=hp(nn,6); mixk=t/L if up else 1-t/L
    return ((lo*(1-mixk)+hi*mixk)*env*.6).astype(np.float32)
def click(f=2200):
    t=np.arange(int(.05*SR))/SR; return (np.sin(2*np.pi*f*t)*np.exp(-t*120)*.5+hp(rng.standard_normal(len(t)),3)*np.exp(-t*300)*.3).astype(np.float32)
def ding():
    t=np.arange(int(1.0*SR))/SR; return ((np.sin(2*np.pi*1318*t)+.5*np.sin(2*np.pi*1976*t))*np.exp(-t*5)*.25).astype(np.float32)
def pop2(f=700):
    t=np.arange(int(.12*SR))/SR; return (np.sin(2*np.pi*(f+900*np.exp(-t*40))*t)*np.exp(-t*35)*.4).astype(np.float32)

for i,b in enumerate(SS[1:-1],1):
    add(fx,whoosh(.45,i%2==0),b-.22,1.0); add(fx,boom(),b,.55 if i not in (3,) else 1.0)
    if i<=3: add(fx,riser(.9),b-.9,.6)
add(fx,riser(1.8),PT-1.8,1.1); add(fx,boom(),PT+.3,1.2); add(fx,ding(),PT+.32,1.0)
add(fx,whoosh(.3,True),ST,.7); add(fx,click(900),ST+.05,1.0)
a5=SS[5]; L5=SS[6]-SS[5]; step=(L5-1.2)/4
for k in range(4): add(fx,whoosh(.35,True),a5+.6+k*step,.7); add(fx,pop2(500+k*90),a5+.6+k*step+.45,1.0)
add(fx,ding(),SS[7]+.4,.7); add(fx,pop2(900),BT+.1,1.3); add(fx,boom(),BT,.6)
add(fx,riser(1.5),SS[8]-1.5,.7); add(fx,boom(),T-1.5,.9)
add(fx,boom(),SS[0]+.3,.6)
vo=json.load(open(f'vo/{V}.json')); voice=z()
for i,v in enumerate(vo):
    a=np.load(f'vo/{V}{i}.npy').astype(np.float32)
    if v['sr']!=SR: a=np.interp(np.linspace(0,len(a)-1,int(len(a)*SR/v['sr'])),np.arange(len(a)),a).astype(np.float32)
    a=a/np.max(np.abs(a))*.9; a=np.tanh(a*1.8)/np.tanh(1.8); a=a+hp(a,6)*.3
    add(voice,a,VS[i],1.0)
venv=ma(np.abs(voice),int(.15*SR)); venv=np.clip(venv/(venv.max()+1e-9)*4,0,1); duck=1-.5*ma(venv,int(.2*SR))
mus=music/np.max(np.abs(music))*.6
mix=mus*duck+fx*.75+voice
env=np.ones(n); fo=int(1.4*SR); env[-fo:]=np.linspace(1,0,fo)**1.3
mix=mix*env; mix=np.tanh(mix*1.25)/np.tanh(1.25); mix=mix/np.max(np.abs(mix))*.95
st=(np.stack([mix,mix],1)*32767).astype(np.int16)
w=wave.open(f'audio_{V}.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close(); print('ok',V)
