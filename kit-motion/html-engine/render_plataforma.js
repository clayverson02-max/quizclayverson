const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.cwd()+'/plat.html');await p.waitForTimeout(800);
const FPS=30,N=Math.round((await p.evaluate(()=>window.DUR))*FPS); require('fs').mkdirSync('fr',{recursive:true});
for(let i=0;i<N;i++){await p.evaluate(t=>setT(t),i/FPS);await p.screenshot({path:`fr/${String(i).padStart(4,'0')}.jpg`,type:'jpeg',quality:93});}
await b.close();console.log('done',N);})();
