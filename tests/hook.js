// Injected by tests/run.py into a temporary copy of site/index.html, right after requestAnimationFrame(frame);
// It runs inside the game's own block scope, so it can see every binding. Never shipped.
// Text widths assume Press Start 2P (every character is 1em wide), so the check is right even when the font can't load.
window.__WQ=new Proxy({},{get:(_,k)=>{try{return eval(String(k))}catch(e){return undefined}},set:(_,k,v)=>{window.__wqv=v;eval(String(k)+'=window.__wqv');return true}});
window.__TXT=[];window.__REC=0;
{const t0=txt;txt=function(s,x,y,col,al,sz){if(window.__REC&&s!==''&&s!=null){const m=ctx.getTransform(),fs=sz||8;const w=String(s).length*fs,a=al||'left',x0=a==='center'?x-w/2:a==='right'?x-w:x;
  window.__TXT.push({s:String(s),x0:m.a*x0+m.e,y0:m.d*y+m.f,x1:m.a*(x0+w)+m.e,y1:m.d*(y+fs)+m.f})}return t0(s,x,y,col,al,sz)}}
window.__frameText=()=>{window.__TXT=[];window.__REC=1;draw();window.__REC=0;return window.__TXT};
window.__overlaps=(list)=>{const L=list||window.__TXT,out=[];for(let i=0;i<L.length;i++)for(let j=i+1;j<L.length;j++){const a=L[i],b=L[j];
  if(a.s===b.s&&Math.abs(a.x0-b.x0)<1&&Math.abs(a.y0-b.y0)<1)continue;const ox=Math.min(a.x1,b.x1)-Math.max(a.x0,b.x0),oy=Math.min(a.y1,b.y1)-Math.max(a.y0,b.y0);if(ox>1&&oy>1)out.push(a.s+' | '+b.s)}return out};
window.__offscreen=(list)=>{const L=list||window.__TXT;return L.filter(t=>t.x0<-1||t.x1>W+1||t.y0<-1||t.y1>H+1).map(t=>t.s)};
// Text fully covered by a later opaque-ish panel (alpha >= 0.6) is hidden, so it is dropped from the frame's list.
{const p0=px;px=function(c,col,x,y,w,h){if(window.__REC&&c===ctx&&w>0&&h>0){let a=1;const m=/rgba\([^)]*,\s*([\d.]+)\)/.exec(String(col));if(m)a=parseFloat(m[1]);
  if(a>=0.6){const t=ctx.getTransform(),X0=t.a*x+t.e,Y0=t.d*y+t.f,X1=t.a*(x+w)+t.e,Y1=t.d*(y+h)+t.f;window.__TXT=window.__TXT.filter(q=>!(q.x0>=X0-0.5&&q.x1<=X1+0.5&&q.y0>=Y0-0.5&&q.y1<=Y1+0.5))}}return p0(c,col,x,y,w,h)}}
