#!/usr/bin/env python3
"""Wren Quest test suite.

    python3 tests/run.py              # every suite
    python3 tests/run.py layout golf  # just these

Suites: world, golf, flows, layout, stress. Needs Python 3 and Playwright
(pip install playwright && playwright install chromium). Set CHROME to use an
installed Chrome instead (e.g. CHROME=/usr/bin/google-chrome), and WQ_GAME
to test another copy of the game file.

The runner copies site/index.html to a temp folder, injects tests/hook.js right
after the top-level `requestAnimationFrame(frame);` line so tests can reach the game's internals,
and drives it headless. Nothing here is served or shipped.
"""
import asyncio, os, sys, tempfile, time, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME = pathlib.Path(os.environ['WQ_GAME']) if os.environ.get('WQ_GAME') else ROOT / 'site' / 'index.html'
HOOK = ROOT / 'tests' / 'hook.js'
ANCHOR = '\nrequestAnimationFrame(frame);\n'

def build_copy():
    src = GAME.read_text()
    if src.count(ANCHOR) != 1:
        sys.exit('tests: expected exactly one top-level requestAnimationFrame(frame); line in site/index.html')
    out = src.replace(ANCHOR, ANCHOR + HOOK.read_text() + '\n', 1)
    d = tempfile.mkdtemp(prefix='wq-test-')
    p = pathlib.Path(d) / 'index.html'
    p.write_text(out)
    return p.as_uri()

# ---------------------------------------------------------------- JS helpers
PRE = """const Q=window.__WQ,T=n=>{for(let i=0;i<n;i++)Q.tick()},K=Q.K,
press=k=>{K[k]=1;T(1);K[k]=0;T(1)},
adv=()=>{for(let i=0;i<120&&['dialog','hold','fade'].includes(Q.G.mode);i++){K.KeyJ=1;T(1);K.KeyJ=0;T(20)}},
fresh=()=>{Q.S=Q.newState();Q.G.bf={};Q.S.items.sword=1;Q.S.items.disc_putt=1;Q.S.maxHp=20;Q.S.hp=20;Q.G.mode='play';Q.G.dlg=null;Q.G.duel=null;Q.G.golf=null;Q.G.lastDuelT=1e12;Q.G.duelPending=0},  // lastDuelT in the future: no random duels in tests
waitDun=()=>{for(let i=0;i<400&&Q.G.room.kind!=='dun';i++){if(['dialog','hold'].includes(Q.G.mode))adv();T(1)}for(let i=0;i<80&&Q.G.mode!=='play';i++){adv();T(1)}},
go=(x,y)=>{const rm=Q.genScreen(x,y);Q.setRoom(rm);Q.G.duelPending=0;Q.G.mode='play';Q.G.dlg=null;Q.G.ents=[];Q.G.npcs=[];Q.G.picks=[];Q.G.banner=null;Q.G.floats=[];return rm};"""

WORLD = PRE + r"""
const bad=[],WALK=Q.WALK;
// overworld: every exit reaches every other (jumps over up to 3 water/lava/hurdle tiles; rune pillars count as open)
for(let y=0;y<Q.WH;y++)for(let x=0;x<Q.WW;x++){const t=Q.genScreen(x,y).t.slice();for(let i=0;i<176;i++)if(t[i]===Q.RP)t[i]=0;
  const ok=v=>WALK.has(v)||v===4||v===5,J=new Set([Q.WA,Q.LV,Q.HU]);let s0=-1;for(let i=0;i<176&&s0<0;i++){const c=i%16,w=i>>4;if((c===0||c===15||w===0||w===10)&&ok(t[i]))s0=i}if(s0<0)continue;
  const seen=new Set([s0]),q=[s0];while(q.length){const i=q.pop(),c=i%16,w=i>>4;for(const [dx,dy] of [[0,1],[1,0],[0,-1],[-1,0]])for(let k=1;k<=4;k++){const nc=c+dx*k,nw=w+dy*k;if(nc<0||nc>15||nw<0||nw>10)break;const j=nw*16+nc;if(ok(t[j])){if(!seen.has(j)){seen.add(j);q.push(j)}break}if(!J.has(t[j]))break}}
  for(let i=0;i<176;i++){const c=i%16,w=i>>4;if((c===0||c===15||w===0||w===10)&&ok(t[i])&&!seen.has(i)){bad.push('overworld exit cut off at '+x+','+y);break}}}
// dungeons: holes, throne, side dungeons
Q.S=Q.newState();const dl=[];for(let n=1;n<=27;n++)dl.push(Q.HD0+n);dl.push(Q.NDUN);
for(const d of dl){Q.S.dun[d]={unl:[],keys:[],item:0,boss:0,hc:0,vis:[]};const g=Q.genDungeon(d);if(!g.boss)bad.push('no boss in dungeon '+d);if(g.list.length<8)bad.push('dungeon '+d+' has '+g.list.length+' rooms')}
for(const k in Q.CAVES){const cv=Q.CAVES[k];if(cv&&cv.sid!==undefined){try{const g=Q.genSide(20+cv.sid);if(!g||!g.list||!g.list.length)bad.push('side dungeon '+cv.sid)}catch(e){bad.push('side dungeon '+cv.sid+' threw '+e.message)}}}
// caverns: every screen joined up
Q.CAVS.forEach((C,i)=>{const first=[...C.cells.keys()][0],seen=new Set([first]),q=[first];while(q.length){const k=q.pop(),[x,y]=k.split(',').map(Number);for(const [dx,dy] of [[0,1],[1,0],[0,-1],[-1,0]]){const k2=(x+dx)+','+(y+dy);if(!C.cells.has(k2)||seen.has(k2))continue;if(C.open.has(k+'|'+k2)||C.open.has(k2+'|'+k)){seen.add(k2);q.push(k2)}}}if(seen.size!==C.cells.size)bad.push('cavern '+i+': '+(C.cells.size-seen.size)+' screens unreachable')});
return {checks:Q.WW*Q.WH+dl.length+Q.CAVS.length,bad};"""

GOLF = PRE + r"""
const bad=[],out=[];
const aimFor=(lie,mk,cv)=>{const Tg=Math.hypot(mk.x-lie.x,mk.y-lie.y),base=Math.atan2(mk.y-lie.y,mk.x-lie.x);let a=base,D=Tg;for(let i=0;i<5;i++){const e=Q.golfPath(lie.x,lie.y,a,D,cv),ch=Math.hypot(e.x-lie.x,e.y-lie.y)||1;a-=Math.atan2(e.y-lie.y,e.x-lie.x)-base;D*=Tg/ch}return{a,D}};
const fly=(c,lie,a,D,cv,gd)=>{const wk=gd.wind;const v0=Math.sqrt(2*0.05*Math.max(1,D));let x=lie.x,y=lie.y,v=v0,t=0;const Tt=v0/0.05,zm=Math.min(18,6+12*D/Q.GOLF_MAX);let hit=0;
  while(v>0){const sp=v/v0;a+=cv*0.022*(0.25+(1-sp)*1.2);x+=Math.cos(a)*v+c.wind.x*wk;y+=Math.sin(a)*v+c.wind.y*wk;v-=0.05;t++;const z=zm*Math.sin(Math.PI*Math.min(1,t/Tt));
    if(Math.hypot(x-c.bk.x,y-c.bk.y)<7&&z<10){if(sp<0.85)return{in:1};if(!hit){hit=1;v*=0.3;a+=Math.PI}}
    for(const tr of c.trees)if(z<13&&Math.hypot(x-tr.x,y-tr.y)<tr.r+2){const sx=x-Math.cos(a)*4,sy=y-Math.sin(a)*4;if(c.water.some(w=>sx>=w.x&&sx<=w.x+w.w&&sy>=w.y&&sy<=w.y+w.h))return{ob:1};return{x:sx,y:sy}}if(x<4||x>252||y<4||y>c.L-4)return{ob:1}}
  if(c.water.some(w=>x>=w.x&&x<=w.x+w.w&&y>=w.y&&y<=w.y+w.h))return{ob:1};return{x,y}};
// the bot only carries the discs a player has by that hole (putter, plus each keeper's drop up to it)
const bagFor=n=>['disc_putt'].concat(Object.entries(Q.TUNE.golf.discAt).filter(([k])=>+k<=n).map(([,d])=>d)).map(k=>Q.TUNE.golf.discs[k]);
const choose=(c,lie,bag)=>{let best=null,bd=1e9;const dB=Math.hypot(c.bk.x-lie.x,c.bk.y-lie.y);
  for(const gd of bag)for(let r=Math.min(gd.max,dB+10);r>=20;r-=Math.max(10,r*0.12))for(let da=-0.9;da<=0.9;da+=0.08){const ang=Math.atan2(c.bk.y-lie.y,c.bk.x-lie.x)+da,mk={x:lie.x+Math.cos(ang)*r,y:lie.y+Math.sin(ang)*r};
    for(const sh of [-0.75,0,0.75]){const cv=sh*gd.cv+(gd.turn||0),s=aimFor(lie,mk,cv),res=fly(c,lie,s.a,s.D,cv,gd);if(res.ob)continue;const d=res.in?-1:Math.hypot(c.bk.x-res.x,c.bk.y-res.y);if(d<bd){bd=d;best=res}}}return best};
for(const h of Q.HOLES){if(h.par<3||h.par>4)bad.push('hole '+h.n+' is par '+h.par);const c=Q.golfCourse(h);let lie={x:c.tee.x,y:c.tee.y},st=0,done=0;
  while(st<h.par&&!done){if(Math.hypot(c.bk.x-lie.x,c.bk.y-lie.y)<=Q.PUTT_FT){st++;done=1;break}const r=choose(c,lie,bagFor(h.n));st++;if(!r){break}if(r.in){done=1;break}lie={x:r.x,y:r.y}}
  out.push(h.n+':'+(done?st:'X')+'/'+h.par);if(!done||st>h.par)bad.push('hole '+h.n+' not makeable in par by perfect play')}
return {checks:Q.HOLES.length,bad,info:out.join(' ')};"""

FLOWS = PRE + r"""
const bad=[],ck=(c,m)=>{if(!c)bad.push(m)};let n=0;const step=(c,m)=>{n++;ck(c,m)};
// new game says the intro

// all pars 3 or 4
step(Q.HOLES.every(h=>h.par===3||h.par===4),'pars are 3 or 4');
// hole loop: sink basket -> dungeon -> boss -> golf -> over par replays -> par gives crown + stairs -> exit to basket screen
fresh();const h=Q.HOLES[0],[hx,hy]=h.key.split(',').map(Number);go(hx,hy);Q.P.x=112;Q.P.y=120;Q.onEnter();Q.G.mode='play';Q.G.dlg=null;Q.G.banner=null;
step(!!Q.G.basket,'hole 1 basket exists');if(Q.G.basket){Q.G.strokes=2;Q.basketMade();waitDun()}
step(Q.G.room.kind==='dun'&&Q.G.dn===Q.HD0+1,'sinking hole 1 enters its dungeon');
const b=Q.G.dg.boss;b.t=Q.dunTiles(b);Q.setRoom(b);Q.P.x=112;Q.P.y=124;Q.onEnter();Q.G.mode='play';T(200);const boss=Q.G.ents.find(e=>e.boss);step(!!boss,'boss spawns');
if(boss){boss.inv=0;Q.hitEnemy(boss,99999,boss.x,boss.y);T(140);adv()}step(Q.G.mode==='golf'&&!Q.G.golf.admin,'boss death starts the golf challenge');step(Q.S.items.disc_mid===1,'hole 1 keeper drops the Midrange');
let g=Q.G.golf;if(g){g.strokes=g.c.par;g.ph='land';g.lt=1;T(3);step(g.ph==='retry'&&!Q.G.ents.some(e=>e.boss&&!e.dead),'over par replays with no boss');T(60);press('KeyJ');step(g.ph==='aim'&&g.tries===2&&g.strokes===0,'replay restarts the hole');
  // three fails cost one heart container
  const mh=Q.S.maxHp;for(let k=0;k<2;k++){g.strokes=g.c.par;g.ph='land';g.lt=1;T(3);T(60);press('KeyJ')}step(Q.S.maxHp===mh-2,'third failed try costs a heart container');
  for(let k=0;k<3;k++){g.strokes=g.c.par;g.ph='land';g.lt=1;T(3);T(60);press('KeyJ')}step(Q.S.maxHp===mh-2,'a hole never takes a second heart container');
  // putting mini-game: lock inside the chains
  g.lie={x:g.c.bk.x,y:g.c.bk.y+20};g.strokes=0;g.ph='land';g.lt=1;T(3);step(g.ph==='putt','within 30 ft starts the putting mini-game');
  const p=g.pt;T(12);p.x=p.ox;press('KeyJ');T(7);p.y=p.oy;press('KeyJ');T(45);step(g.made===1&&g.ph==='done','putt inside the chains is made');
  T(270);adv();T(5)}
step(Q.S.shards.includes(Q.HD0+1)&&[...Q.G.room.t].includes(Q.ST),'par gives the crown piece and opens the stairs');
Q.exitDungeon();T(60);adv();step(Q.G.room.kind==='over'&&Q.G.room.key===h.key,'stairs return to the basket screen');
// disc bag: Q/E picks a disc, range follows the disc, the shortest disc that reaches is picked at each lie, pro shop sells no discs
fresh();go(18,23);Q.S.items.disc_mid=1;Q.S.items.disc_drive=1;Q.S.items.disc_glow=1;Q.startGolf(5);T(3);{const g=Q.G.golf;g.ph='aim';g.t=200;
 step(g.bag.length===4,'the bag holds every disc owned');const d0=Q.golfDist();step(Q.gDisc().max>=d0-Q.PUTT_FT*0.5||Q.gDisc().max===280,'the tee picks a disc that reaches');
 const before=g.di;press('KeyE');step(g.di===(before+1)%4,'E picks the next disc');press('KeyQ');step(g.di===before,'Q picks the previous disc');
 g.di=0;g.mk={x:g.lie.x,y:g.lie.y-200};g.pv=null;press('KeyQ');press('KeyE');g.di=0;press('ArrowUp');step(Math.hypot(g.mk.x-g.lie.x,g.mk.y-g.lie.y)<=120.5,'the putter cannot mark past 120 ft');
 g.lie={x:g.c.bk.x,y:g.c.bk.y+100};Q.golfHome();step(Q.gDisc().nm==='PUTTER','close in, the putter is picked')}
Q.G.golf=null;Q.G.mode='play';step(!Q.shopStock({type:'proshop'},0).some(o=>/^disc_/.test(o.item)),'the pro shop sells no discs');
{const p3=Q.HOLES.filter(h=>h.par===3),early=p3.find(h=>h.n<=2),late=p3.find(h=>h.n>=3);step(Q.golfCourse(early).L===341&&Q.golfCourse(late).L>Q.golfCourse(early).L,'par 3s are 341 ft with the Midrange and grow once the Driver is in reach')}
// walk away: B at the retry screen goes back to the surface; the boss room resumes the challenge with no refight
fresh();{const h2=Q.HOLES[1],[x2,y2]=h2.key.split(',').map(Number);go(x2,y2);Q.P.x=112;Q.P.y=120;Q.onEnter();Q.G.mode='play';Q.G.dlg=null;Q.G.banner=null;
 if(Q.G.basket){Q.G.strokes=2;Q.basketMade();waitDun()}const d=Q.G.dn,bb=Q.G.dg.boss;bb.t=Q.dunTiles(bb);Q.setRoom(bb);Q.P.x=112;Q.P.y=124;Q.onEnter();Q.G.mode='play';T(200);
 const bs=Q.G.ents.find(e=>e.boss);if(bs){bs.inv=0;Q.hitEnemy(bs,99999,bs.x,bs.y);T(140);adv()}step(Q.G.mode==='golf','hole 2 challenge starts');
 const g2=Q.G.golf;g2.strokes=g2.c.par;g2.ph='land';g2.lt=1;T(3);T(60);press('KeyL');T(2);step(Q.G.mode==='dialog'&&!Q.G.golf,'B on the retry screen walks away');adv();T(80);adv();
 step(Q.G.room.kind==='over'&&Q.G.room.key===h2.key,'walking away returns to the basket screen');step(!Q.S.shards.includes(Q.HD0+2),'walking away gives no crown piece');
 Q.enterDungeon(d);T(60);adv();Q.G.mode='play';const b3=Q.G.dg.boss;b3.t=Q.dunTiles(b3);Q.setRoom(b3);Q.P.x=112;Q.P.y=124;Q.onEnter();Q.G.mode='play';T(60);
 step(!Q.G.ents.some(e=>e.boss),'coming back: the keeper stays down');adv();step(Q.G.mode==='golf'&&Q.G.golf.h.n===2,'coming back resumes the hole challenge');
 Q.G.golf.ph='intro';Q.G.golf.t=30;press('KeyL');T(2);step(!Q.G.golf,'B at the tee walks away too');adv();T(80);adv()}
// story: opening plays on a new game, beats at 1/9/18/27 pieces, throne talk, ending then the win screen
Q.newGame();step(Q.G.mode==='scene'&&Q.G.scene.name==='opening','new game opens with the story');for(let i=0;i<20&&Q.G.mode==='scene';i++){K.Enter=1;T(1);K.Enter=0;T(30)}step(Q.G.mode==='dialog','skipping the opening leads to the first line');
// one-minute opening: putter in hand, first sink on hole 1 opens a practice hole (no heart cost), then the groundskeeper
Q.newGame();Q.G.scene=null;Q.G.mode='play';Q.G.dlg=null;step(Q.S.items.disc_putt===1&&Q.S.sel==='disc_putt'&&!Q.S.items.sword,'a new game starts with the putter in hand');
Q.P.x=112;Q.P.y=120;Q.onEnter();Q.G.mode='play';Q.G.dlg=null;Q.G.banner=null;step(!!Q.G.basket,'the first basket is on the start screen');
if(Q.G.basket){Q.G.strokes=1;Q.basketMade();for(let i=0;i<200&&Q.G.mode!=='golf';i++)T(1)}step(Q.G.mode==='golf'&&Q.G.golf.tut&&Q.G.room.kind==='over','sinking it opens the practice hole, not the dungeon');
{const g=Q.G.golf,mh=Q.S.maxHp;for(let k=0;k<3;k++){g.strokes=3;Q.golfAfter();step(g.ph==='retry','practice over par replays');Q.golfReset()}step(Q.S.maxHp===mh,'missing practice three times costs no heart');
 g.made=1;g.strokes=2;g.ph='done';g.t=120;K.KeyJ=1;T(1);K.KeyJ=0;T(2);step(Q.G.mode==='dialog'&&Q.S.beats.includes('practice'),'finishing practice calls Wren to the groundskeeper')}
Q.G.mode='play';Q.G.dlg=null;Q.setRoom(Q.genScreen(18,23));Q.P.x=112;Q.P.y=120;Q.onEnter();Q.G.mode='play';Q.G.dlg=null;Q.G.banner=null;if(Q.G.basket){Q.G.strokes=1;Q.basketMade();T(200)}step(Q.G.mode!=='golf'&&Q.G.room.kind==='over','no sword yet: a second sink does not drop into the dungeon');
Q.newGame();Q.G.scene=null;Q.G.mode='play';Q.G.dlg=null;Q.startGolf(0,1);T(3);Q.G.golf.ph='retry';Q.G.golf.t=60;K.KeyL=1;T(1);K.KeyL=0;T(2);step(Q.G.mode!=='golf'&&Q.S.beats.includes('practice'),'B skips the practice hole');
fresh();go(18,23);for(const [n,b] of [[1,'first'],[9,'nine'],[18,'eighteen'],[27,'all']]){Q.S.shards=[];for(let i=1;i<=n;i++)Q.S.shards.push(Q.HD0+i);Q.storyBeat();T(2);step(Q.G.mode==='scene'&&Q.G.scene.name===b,'story beat at '+n+' pieces');for(let i=0;i<20&&Q.G.mode==='scene';i++){K.Enter=1;T(1);K.Enter=0;T(30)}adv();Q.G.mode='play'}
Q.storyBeat();T(2);step(Q.G.mode==='play','each beat plays once');
fresh();Q.S.shards=[];Q.enterDungeon(Q.NDUN);T(60);Q.G.mode='play';const tb=Q.G.dg.boss;tb.t=Q.dunTiles(tb);Q.setRoom(tb);Q.P.x=112;Q.P.y=124;Q.onEnter();Q.G.mode='play';T(3);step(Q.G.mode==='scene'&&Q.G.scene.name==='throne','the King speaks before the final fight');
fresh();go(18,23);Q.winGame();step(Q.G.mode==='scene'&&Q.G.scene.name==='ending','winning plays the ending');for(let i=0;i<20&&Q.G.mode==='scene';i++){K.Enter=1;T(1);K.Enter=0;T(30)}step(Q.G.mode==='win','the ending leads to the win screen');
fresh();go(18,23);Q.S.shards=[];for(let i=1;i<=18;i++)Q.S.shards.push(Q.HD0+i);step(Q.sceneEra()===2,'the land darkens after 18 pieces');
// admin menu is hidden without the flag
fresh();go(18,23);Q.openAdmin();step(Q.G.mode!=='admin','admin menu needs ?admin');
// map marker throw: near a basket with no foes close, the disc button opens the marker; a perfect throw sinks it
{const mtAt=(n)=>{fresh();const h=Q.HOLES[n-1],[x,y]=h.key.split(',').map(Number);go(x,y);Q.P.x=112;Q.P.y=120;Q.onEnter();Q.G.mode='play';Q.G.dlg=null;Q.G.banner=null;Q.G.ents=[];Q.G.npcs=[];const b=Q.G.basket;
   for(const [ox,oy] of [[0,70],[0,-70],[70,0],[-70,0],[50,50],[-50,50],[0,40],[40,0]]){const px=b.cx+ox-8,py=b.cy+oy-10;if(!Q.freeP(px,py))continue;let ok=true;for(let k=1;k<20;k++){const tl=Q.tileAt(b.cx+ox*(1-k/20),b.cy+oy*(1-k/20));if(tl===null||Q.blocksShot(tl))ok=false}if(ok){Q.P.x=px;Q.P.y=py;return b}}return null};
 const b=mtAt(4);step(!!b,'found a clear lie near a map basket');if(b){Q.S.sel='disc_putt';Q.P.icd=0;press('KeyK');step(Q.G.mode==='mthrow','the disc button near a basket opens the marker');
  press('KeyK');step(Q.G.mode==='play','pressing it again backs out with no throw');step(!Q.G.strokes,'backing out costs no stroke');
  Q.P.icd=0;press('KeyK');const m=Q.G.mt;m.mk={x:b.cx,y:b.cy};m.pv=null;press('KeyL');step(m.shape===2,'B changes the shape');m.shape=1;
  press('KeyJ');step(m.ph==='power','A starts the power bar');m.pw=1;m.pd=0;press('KeyJ');step(m.ph==='rel','A locks power');m.rel=0;m.rd=0;Q.mtThrow();step(Q.G.discOut&&Q.G.strokes===1,'the throw counts a stroke');
  for(let i=0;i<200&&!Q.G.basket.made;i++)T(1);step(Q.G.basket.made===1,'a perfect marker throw sinks the basket')}
 const b2=mtAt(5);if(b2){Q.S.sel='disc_putt';Q.P.icd=0;press('KeyK');const m=Q.G.mt;m.mk={x:b2.cx,y:b2.cy};m.pv=null;m.pw=0.5;m.rel=0;Q.mtThrow();for(let i=0;i<200&&Q.G.shots.length;i++)T(1);
  step(!Q.G.basket.made&&Q.G.picks.some(p=>p.kind==='discdrop'),'a short marker throw lands where Wren can pick it up')}
 const b3=mtAt(6);if(b3){Q.S.sel='disc_putt';{const fe=Q.makeEnemy(Object.keys(Q.EN)[0],Q.P.x+20,Q.P.y,1);fe.spawn=0;Q.G.ents.push(fe)}Q.P.icd=0;press('KeyK');step(Q.G.mode==='play'&&Q.G.shots.some(s=>s.kind==='disc'&&!s.pts),'with a foe close by, the disc is a quick throw');Q.G.ents=[];Q.G.shots=[];Q.G.discOut=0}
 fresh();go(18,23);Q.P.x=112;Q.P.y=120;Q.onEnter();Q.G.mode='play';Q.G.dlg=null;Q.G.ents=[];Q.G.npcs=[];Q.P.x=16;Q.P.y=140;Q.S.sel='disc_putt';Q.P.icd=0;if(Math.hypot(Q.G.basket.cx-24,Q.G.basket.cy-150)>Q.TUNE.golf.mapRange){press('KeyK');step(Q.G.mode==='play','far from the basket, the disc is a quick throw')}}
// disc gates on moat islands: Ember burns thorns, Crystal wakes the eye; nothing else opens them, jumps can't clear them, they stay open
{const gs={ember:[],crystal:[]};for(let y=0;y<Q.WH;y++)for(let x=0;x<Q.WW;x++){const rm=Q.genScreen(x,y);if(rm.jf&&rm.jf.gate)gs[rm.jf.gate].push([x,y])}
 step(gs.ember.length>=3&&gs.crystal.length>=3,'the world has a few disc gates (ember '+gs.ember.length+', crystal '+gs.crystal.length+')');
 if(gs.ember.length){fresh();const [x,y]=gs.ember[0];const rm=go(x,y);const th=[...rm.t].indexOf(Q.TH);step(th>=0,'an ember gate has thorns');
  Q.gateHit({x:0,y:0,dk:'disc_mid'},Q.TH);step([...Q.G.room.t].includes(Q.TH),'a plain disc does not burn thorns');
  Q.P.z=8;step(!Q.freeP((th%16)*16,(th>>4)*16-6),'a jump cannot clear thorns');Q.P.z=0;
  Q.gateHit({x:0,y:0,dk:'disc_glow',glow:1},Q.TH);step(![...Q.G.room.t].includes(Q.TH)&&Q.S.opened.includes('e:'+x+','+y),'the Ember disc burns the thorns away');
  const again=go(x,y);step(![...again.t].includes(Q.TH),'burnt thorns stay gone')}
 if(gs.crystal.length){fresh();const [x,y]=gs.crystal[0];const rm=go(x,y);step([...rm.t].includes(Q.EY)&&[...rm.t].includes(Q.SG),'a crystal gate has a seal and an eye');
  Q.gateHit({x:0,y:0,dk:'disc_drive'},Q.EY);step([...Q.G.room.t].includes(Q.SG),'another disc does not wake the eye');
  Q.gateHit({x:0,y:0,dk:'disc_crystal'},Q.EY);step(![...Q.G.room.t].includes(Q.SG)&&![...Q.G.room.t].includes(Q.EY),'the Crystal disc opens the seal');
  const again=go(x,y);step(![...again.t].includes(Q.SG),'an opened seal stays open')}}
// a random duel cannot start while the ground is opening; the drop still happens
fresh();{const h3=Q.HOLES[2],[x3,y3]=h3.key.split(',').map(Number);go(x3,y3);Q.P.x=112;Q.P.y=120;Q.onEnter();Q.G.mode='play';Q.G.dlg=null;Q.G.banner=null;
 if(Q.G.basket){Q.G.strokes=2;Q.basketMade();T(20);Q.G.duelPending='duelist';T(10);step(Q.G.mode!=='duel'&&!Q.G.duel,'no random duel while the ground opens');waitDun();step(Q.G.room.kind==='dun'&&Q.G.dn===Q.HD0+3,'the drop still happens (mode '+Q.G.mode+', room '+Q.G.room.kind+', he '+JSON.stringify(Q.G.holeEnter)+', duel '+!!Q.G.duel+', dlg '+(Q.G.dlg&&Q.G.dlg.pages&&Q.G.dlg.pages[0]||'').slice(0,60)+')')}}
// ambush: duel mid-ambush restores the ambush and clearing opens the gates
fresh();const ak=[...Q.ARENA][0].split(',').map(Number);go(ak[0],ak[1]);Q.P.x=112;Q.P.y=80;Q.onEnter();Q.G.mode='play';T(60);
Q.startDuel('duelist',{lvl:1});T(115);Q.G.duel.phase='ko';Q.G.duel.t=200;T(3);step(!!Q.G.arena,'ambush survives a duel');
for(let w=0;w<8&&Q.G.arena;w++){for(const e of Q.G.ents)if(!e.dead){e.inv=0;e.spawn=0;Q.hitEnemy(e,999,e.x,e.y)}T(120)}step(!Q.G.arena&&![...Q.G.room.t].includes(17),'clearing the ambush opens the gates');
// sword levels and heart pieces
fresh();Q.swordXP(5000);step(Q.S.swl===30,'sword reaches level 30');const mh2=Q.S.maxHp;Q.S.hpc=0;for(let i=0;i<4;i++)Q.heartPiece('t');Q.G.mode='play';T(2);adv();step(Q.S.maxHp===mh2+2,'four heart pieces make a container');
// old save migration (wv 2, three old shards)
const old=JSON.parse(JSON.stringify(Q.newState()));old.wv=2;old.shards=[1,2,4];old.items.sword=1;Q.S=Object.assign(Q.newState(),old);Q.S.wv=2;Q.startLoaded();adv();
step(Q.S.wv===3&&Q.S.shards.length===3&&Q.S.shards.every(d=>d>Q.HD0),'old shards become crown pieces');
return {checks:n,bad};"""

# Layout: screens drawn with worst-case values; any text drawn over other text fails.
LAYOUT = PRE + r"""
const res=[];const shot=(name,setup)=>{try{fresh();setup();Q.G.floats=[];Q.G.banner=null;const t0=Q.G.t,ov=new Set(),off=new Set();let n=0;for(let k=0;k<48;k+=4){Q.G.t=t0+k;const L=window.__frameText();n=Math.max(n,L.length);window.__overlaps(L).forEach(x=>ov.add(x+' @t+'+k));window.__offscreen(L).forEach(x=>off.add(x+' @t+'+k))}Q.G.t=t0;res.push({name,n,ov:[...ov],off:[...off]})}catch(e){res.push({name,n:0,ov:['THREW '+e.message],off:[]})}};
const worst=()=>{const S=Q.S;S.maxHp=32;S.hp=31;S.gems=999;S.bombs=99;S.swl=30;S.swx=0;S.hpc=3;S.deaths=123;S.secrets=['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o'];S.shards=[];for(let n=1;n<=27;n++)S.shards.push(Q.HD0+n);
  for(const k in Q.ITEMS)S.items[k]=1;for(const k of Q.CONSK)S.inv[k]=9;for(const k of ['giant','boom','frost'])S.bag[k]=9;for(const hh of Q.HOLES)S.bk[hh.key]={s:hh.par+3,o:hh.n};S.aces=12;S.putts=99};
for(const [x,y] of [[18,23],[0,0],[35,23],[35,0]])shot('overworld HUD '+x+','+y,()=>{worst();go(x,y)});
shot('hole 27 dungeon HUD',()=>{worst();Q.enterDungeon(Q.HD0+27);T(60);Q.G.mode='play'});
shot('throne HUD',()=>{worst();Q.enterDungeon(Q.NDUN);T(60);Q.G.mode='play'});
shot('pause items',()=>{worst();go(18,23);Q.G.mode='pause';Q.G.ppage=0;Q.G.pcur=Q.INV.length-1});
shot('pause map',()=>{worst();go(18,23);Q.G.mode='pause';Q.G.ppage=1;Q.G.pcur=0});
for(const c of [1,2,3])shot('scorecard '+c,()=>{worst();go(18,23);Q.openCard(c);T(60)});
shot('admin menu',()=>{worst();go(18,23);Q.G.adm={i:26,col:1};Q.G.mode='admin'});
shot('warp menu',()=>{worst();go(18,23);for(const hh of Q.HOLES)Q.S.visited.push(hh.key);Q.openWarp()});
shot('dialog',()=>{worst();go(18,23);Q.say('WWWWWWWWWWWWWWWWWWWWWWWWWWWW WWWWWWWWWWWWWWWWWWWWWWWWWWWW WWWWWWWWWWWWWWWWWWWWWWWWWWWW WWWWWWWWWWWWWWWWWWWWWWWWWWWW');T(200)});
shot('marebear duel',()=>{worst();go(18,23);Q.startDuel('marebear',{lvl:9});T(130);Q.G.duel.love=88});
shot('champion duel ready',()=>{worst();go(18,23);Q.startDuel('shadow',{lvl:9});T(20)});
const golf=(name,f)=>shot('golf '+name,()=>{worst();go(18,23);Q.startGolf(27);T(5);const g=Q.G.golf;g.tries=12;g.strokes=9;g.shape=2;g.fails=11;f(g)});
golf('intro',g=>{g.ph='intro';g.t=20});
const mts=(name,f)=>shot('map throw '+name,()=>{worst();for(const k of ['disc_mid','disc_drive','disc_glow','disc_crystal'])Q.S.items[k]=1;const h=Q.HOLES[3],[x,y]=h.key.split(',').map(Number);go(x,y);Q.P.x=112;Q.P.y=120;Q.onEnter();Q.G.mode='play';Q.G.dlg=null;Q.G.banner=null;Q.G.ents=[];Q.G.npcs=[];const b=Q.G.basket;Q.P.x=b.cx-8;Q.P.y=Math.min(150,b.cy+60);Q.startMT('disc_drive');f(Q.G.mt)});
shot('disc gate hint',()=>{worst();const L=[];for(let y=0;y<Q.WH&&!L.length;y++)for(let x=0;x<Q.WW&&!L.length;x++){const rm=Q.genScreen(x,y);if(rm.jf&&rm.jf.gate==='ember')L.push([x,y])}go(L[0][0],L[0][1]);Q.G.gateHint=0;Q.gateHit({x:120,y:80,dk:'disc_mid'},Q.TH)});
mts('aim',m=>{m.ph='aim'});mts('aim panel top',m=>{m.ph='aim';m.lie.y=150});mts('power',m=>{m.ph='power';m.pw=1.1});mts('release',m=>{m.ph='rel';m.pw=1;m.rel=0.9});
shot('golf full bag',()=>{worst();go(18,23);for(const k of ['disc_mid','disc_drive','disc_glow','disc_crystal'])Q.S.items[k]=1;Q.startGolf(27);T(5);const g=Q.G.golf;g.ph='aim';g.t=200;g.di=g.bag.indexOf('disc_crystal');g.tries=12;g.strokes=9;g.shape=2});
const prac=(name,f)=>shot('practice '+name,()=>{worst();go(18,23);Q.startGolf(0,1);T(5);const g=Q.G.golf;g.tries=12;g.strokes=9;g.fails=11;f(g)});
prac('intro',g=>{g.ph='intro';g.t=20});prac('aim',g=>{g.ph='aim';g.t=200});prac('power',g=>{g.ph='power';g.pw=1.1});prac('release',g=>{g.ph='rel';g.pw=1;g.rel=0.9});
prac('putt',g=>{g.lie={x:g.c.bk.x,y:g.c.bk.y+25};Q.startPutt()});prac('retry',g=>{g.ph='retry';g.t=80;g.failed=1});prac('done',g=>{g.ph='done';g.made=1;g.t=50});
shot('hud crown complete',()=>{worst();go(18,23);Q.S.shards=[];for(let i=1;i<=27;i++)Q.S.shards.push(Q.HD0+i)});
shot('hud crown new piece',()=>{worst();go(18,23);Q.S.shards=[];for(let i=1;i<=12;i++)Q.S.shards.push(Q.HD0+i);Q.drawHUD();Q.S.shards.push(Q.HD0+20);Q.drawHUD()});
golf('aim',g=>{g.ph='aim';g.t=200;g.mk={x:g.lie.x,y:g.lie.y-210};g.pv=null});
golf('power',g=>{g.ph='power';g.pw=1.1});
golf('release',g=>{g.ph='rel';g.pw=1;g.rel=0.9});
golf('retry heart lost',g=>{g.ph='retry';g.t=80;g.heartLost=1;g.failed=1});
golf('retry',g=>{g.ph='retry';g.t=80;g.heartLost=0;g.fails=1;g.failed=1});
golf('retry no hearts at stake',g=>{g.ph='retry';g.t=80;g.heartLost=0;g.fails=4;g.failed=1;Q.S.golfLost={27:1}});golf('intro leave',g=>{g.ph='intro';g.t=40;g.admin=false});
golf('done',g=>{g.ph='done';g.t=50;g.made=1;g.strokes=1});
golf('message',g=>{g.ph='aim';g.msg={s:'OUT OF BOUNDS! +1',c:'#fff',t:50}});
for(const ph of ['x','y','miss'])golf('putt '+ph,g=>{g.lie={x:g.c.bk.x,y:g.c.bk.y+30};Q.startPutt();g.pt.ph=ph;g.pt.t=10;g.pt.res='SHORT! HITS THE CAGE'});
shot('title',()=>{Q.G.mode='title';Q.G.t=200});
for(const nm in Q.SCENES)Q.SCENES[nm].forEach((pg,i)=>shot('scene '+nm+' '+(i+1),()=>{worst();go(18,23);Q.playScene(nm);Q.G.scene.i=i;Q.G.scene.ch=999}));
shot('win',()=>{worst();go(18,23);Q.S.time=359999;Q.G.mode='win';Q.G.winT=300});
const bad=[];for(const r of res){for(const o of r.ov)bad.push(r.name+': "'+o+'" overlap');for(const o of r.off)bad.push(r.name+': "'+o+'" runs off screen')}
return {checks:res.length,bad};"""

STRESS = PRE + r"""
fresh();const S=Q.S;for(const k in Q.ITEMS)S.items[k]=1;S.maxHp=40;S.hp=40;S.bombs=20;S.gems=500;go(18,23);Q.onEnter();
const keys=['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyJ','KeyK','KeyL','Space'];let seed=3;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647};
const places=[()=>{go(10+Math.floor(rnd()*16),4+Math.floor(rnd()*16));Q.onEnter()},()=>{Q.enterDungeon(Q.HD0+1+Math.floor(rnd()*27));T(50)},()=>{const i=Math.floor(rnd()*Q.CAVS.length),k=[...Q.CAVS[i].cells.keys()][0].split(',').map(Number);Q.setRoom(Q.genCavScreen(i,k[0],k[1]));Q.onEnter()}];
let frames=0;for(let r=0;r<12;r++){places[r%3]();Q.G.mode='play';Q.G.dlg=null;for(let f=0;f<1500;f++){if(f%9===0)for(const k of keys)K[k]=rnd()<0.25?1:0;Q.tick();frames++;
  if(['dialog','hold'].includes(Q.G.mode)&&f%30===0){Q.G.mode='play';Q.G.dlg=null}if(Q.G.mode==='gameover'||S.hp<=2){S.hp=40;Q.G.mode='play'}if(Q.G.mode==='golf'){Q.G.golf=null;Q.G.mode='play'}}}
for(const k of keys)K[k]=0;return {checks:frames,bad:[]};"""

SUITES = {'world': WORLD, 'golf': GOLF, 'flows': FLOWS, 'layout': LAYOUT, 'stress': STRESS}

async def run(names):
    from playwright.async_api import async_playwright
    url = build_copy()
    failed = 0
    async with async_playwright() as p:
        kw = {'executable_path': os.environ['CHROME']} if os.environ.get('CHROME') else {}
        browser = await p.chromium.launch(**kw)
        for name in names:
            page = await browser.new_page(viewport={'width': 600, 'height': 640})
            errs = []
            page.on('pageerror', lambda e: errs.append(str(e)))
            page.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            await page.goto(url)
            await page.wait_for_timeout(700)
            await page.keyboard.down('Enter'); await page.wait_for_timeout(120); await page.keyboard.up('Enter')
            await page.wait_for_timeout(500)
            t0 = time.time()
            try:
                r = await page.evaluate('()=>{' + SUITES[name] + '}')
            except Exception as e:
                r = {'checks': 0, 'bad': ['suite threw: ' + str(e).splitlines()[0]]}
            bad = list(r.get('bad', [])) + ['console error: ' + e for e in errs]
            ok = not bad
            failed += 0 if ok else 1
            print('%-7s %s  %s checks  %.0fs' % (name, 'PASS' if ok else 'FAIL', r.get('checks', 0), time.time() - t0))
            if r.get('info'):
                print('        ' + r['info'])
            for b in bad[:30]:
                print('        - ' + b)
            if len(bad) > 30:
                print('        ... and %d more' % (len(bad) - 30))
            await page.close()
        await browser.close()
    return failed

if __name__ == '__main__':
    names = sys.argv[1:] or list(SUITES)
    unknown = [n for n in names if n not in SUITES]
    if unknown:
        sys.exit('unknown suite(s): %s (have: %s)' % (', '.join(unknown), ', '.join(SUITES)))
    sys.exit(1 if asyncio.run(run(names)) else 0)
