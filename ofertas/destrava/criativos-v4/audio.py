import json,sys,numpy as np,subprocess,wave
v=sys.argv[1]; vo=json.load(open(f'vo_{v}.json')); SR=44100
NL=[x['dur']+(1.5 if i==len(vo)-1 else .7) for i,x in enumerate(vo)]; NS=np.concatenate([[0],np.cumsum(NL)[:-1]]); DUR=NS[-1]+NL[-1]
VS=[s+(.25 if i==0 else .32) for i,s in enumerate(NS)]
N=int(DUR*SR)+SR; t=np.arange(N)/SR; rng=np.random.default_rng(3)
beat=60/112; mus=np.zeros(N)
def add(buf,x,at):
  a=int(at*SR); b=min(N,a+len(x)); buf[a:b]+=x[:b-a]
kt=np.arange(int(.35*SR))/SR; kick=np.sin(2*np.pi*(50+90*np.exp(-kt*30))*kt)*np.exp(-kt*9)
ht=np.arange(int(.05*SR))/SR; hat=rng.standard_normal(len(ht))*np.exp(-ht*90)*.25
st=np.arange(int(.2*SR))/SR; snare=(rng.standard_normal(len(st))*.5+np.sin(2*np.pi*190*st)*.4)*np.exp(-st*22)
chords=[[220,277.2,329.6],[196,246.9,293.7],[174.6,220,261.6],[196,246.9,293.7]]
nb=int(DUR/beat)+2
for i in range(nb):
  at=i*beat; add(mus,kick*.9 if i%2==0 else kick*.5,at)
  if i%4 in(1,3): add(mus,snare*.45,at)
  add(mus,hat,at+beat/2)
  if i%4==0:
    ch=chords[(i//4)%4]; L=int(beat*4*SR); pt=np.arange(L)/SR
    pad=sum(np.sin(2*np.pi*f*pt)+.3*np.sin(2*np.pi*2*f*pt) for f in ch)/6*np.minimum(1,pt/.3)*np.exp(-pt*.35)
    add(mus,pad*.35,at)
    bt=np.arange(int(beat*SR))/SR; add(mus,np.sin(2*np.pi*ch[0]/2*bt)*np.exp(-bt*3)*.5,at)
mus/=np.abs(mus).max()
voice=np.zeros(N); sfx=np.zeros(N)
for i,x in enumerate(vo):
  with wave.open(f'/tmp/w/tts/{x["id"]}.wav') as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768; a=a.reshape(-1,w.getnchannels()).mean(1)
  add(voice,a,VS[i])
  if i>0:
    wt=np.arange(int(.45*SR))/SR; n=rng.standard_normal(len(wt)); env=np.sin(np.pi*wt/.45)**2
    wh=np.convolve(n,np.ones(30)/30,'same')*env*.5; add(sfx,wh,NS[i]-.25)
env=np.convolve((np.abs(voice)>.02).astype(float),np.ones(int(.25*SR))/int(.25*SR),'same')
duck=1-.6*np.minimum(1,env*3)
mix=voice*1.0+mus*.22*duck+sfx*.35
mix=mix[:int(DUR*SR)]; fade=int(.6*SR); mix[-fade:]*=np.linspace(1,0,fade)
mix=np.clip(mix/np.abs(mix).max()*.9,-1,1)
with wave.open(f'{v}_mix.wav','w') as w: w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((mix*32767).astype(np.int16).tobytes())
