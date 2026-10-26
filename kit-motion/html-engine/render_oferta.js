const {chromium}=require('playwright');(async()=>{const v=process.argv[2];const vo=JSON.parse(require('fs').readFileSync(`vo/${v}.json`,'utf8'));
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.cwd()+'/oferta.html?v='+v+'&vo='+encodeURIComponent(JSON.stringify(vo.map(o=>({text:o.text,dur:o.dur})))));await p.waitForTimeout(800);
const info=await p.evaluate(()=>({DUR:window.DUR,SS:window.SS,VS:window.VS,PRICE_T:window.PRICE_T,STRIKE_T:window.STRIKE_T,BTN_T:window.BTN_T}));
require('fs').writeFileSync(`info_${v}.json`,JSON.stringify(info));
const N=Math.round(info.DUR*30); require('fs').mkdirSync('fr_'+v,{recursive:true});
for(let i=0;i<N;i++){await p.evaluate(t=>setT(t),i/30);await p.screenshot({path:`fr_${v}/${String(i).padStart(4,'0')}.jpg`,type:'jpeg',quality:92});}
require('fs').writeFileSync(`done_${v}`,String(N));await b.close();})();
