const {chromium}=require('playwright');const {spawn}=require('child_process');
(async()=>{const [,,v,voFile,out,only]=process.argv;const vo=require(voFile);
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
p.on('pageerror',e=>console.error('ERR',e.message));
await p.goto('file://'+__dirname+'/motor_v4.html?v='+v+'&vo='+encodeURIComponent(JSON.stringify(vo)));await p.waitForTimeout(400);
const D=await p.evaluate(()=>window.DUR);console.log('DUR',D);
if(only){for(const t of only.split(',')){await p.evaluate(t=>setT(t),+t);await p.screenshot({path:out+'_'+t+'.jpg',type:'jpeg',quality:80});}await b.close();return;}
const ff=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-framerate','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-preset','veryfast',out]);
const N=Math.ceil(D*30);for(let i=0;i<N;i++){await p.evaluate(t=>setT(t),i/30);const buf=await p.screenshot({type:'jpeg',quality:88});ff.stdin.write(buf);}
ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();console.log('done',N);})();
