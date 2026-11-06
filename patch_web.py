from pathlib import Path
p=Path(__file__).parent/'web'/'index.html'
s=p.read_text()
s=s.replace('<button role="tab" id="tab-routine"','<button role="tab" id="tab-routine"',1)
s=s.replace('</footer>','</footer>\n<section class="wrap" id="watchSync" style="padding-bottom:24px;font-size:13px"></section>',1)
s=s.replace('  try{await backend.save(k,b);if(!IS_PWA', '  try{await backend.save(k,b);syncQueueDay(k,b);if(!IS_PWA',1)
s=s.replace('  try{await backend.saveRoutine(r)}catch(e)', '  try{await backend.saveRoutine(r);syncQueueRoutine()}catch(e)',1)
s=s.replace('  if(IS_PWA){backend=localBackend();loaded=true;', '  if(IS_PWA){backend=localBackend();loaded=true;',1)
s=s.replace('navigator.serviceWorker.register("sw.js").catch(()=>{});return}', 'navigator.serviceWorker.register("sw.js").catch(()=>{});syncStart();return}',1)
# Sync module inline: local-first, existing remote wins only if user approves; remote changes update local after polling.
code=r'''
// --------- Optional Wear OS cloud synchronization ---------
// Credentials are only stored on this device. The server must use HTTPS.
const syncConfKey="split3-wear-sync", syncPrefs=()=>{try{return JSON.parse(localStorage.getItem(syncConfKey)||"null")}catch(e){return null}};
let syncConf=syncPrefs(), syncRev={}, syncBusy=false, syncPending={}, syncBooted=false, syncTimer=null, syncError="";
function syncPanel(){
  const box=$("watchSync");if(!box)return;
  box.innerHTML=`<div style="background:var(--surface);border:1px solid var(--line);padding:14px;border-radius:12px;display:grid;gap:8px">
    <strong>갤럭시 워치 동기화 ${syncConf?"· 연결 설정됨":"· 설정 필요"}</strong>
    <span style="color:var(--muted)">${syncError?esc(syncError):syncConf?"기록은 이 휴대폰에 저장되며 서버와 주기적으로 동기화됩니다.":"HTTPS 동기화 서버 주소와 비밀 토큰을 등록하세요."}</span>
    <input id="syncUrl" placeholder="https://your-server.example.com" style="font:inherit;padding:9px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)" value="${esc(syncConf?.url||'')}">
    <input id="syncToken" type="password" placeholder="동기화 토큰" style="font:inherit;padding:9px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)" value="${esc(syncConf?.token||'')}">
    <div style="display:flex;gap:8px"><button id="syncConnect" class="ghost">연결 / 새로고침</button><button id="syncDisconnect" class="ghost">연결 해제</button></div>
    <small>주의: 처음 연결할 때 서버에 기록이 있으면 기존 휴대폰 데이터를 덮어쓰기 전에 확인합니다. 먼저 JSON 백업을 보관하세요.</small>
  </div>`;
  $("syncConnect").onclick=async()=>{
    const url=$("syncUrl").value.trim().replace(/\/$/,""),token=$("syncToken").value.trim();
    if(!/^https:\/\/[^\s]+$/.test(url)||token.length<24){syncError="HTTPS 주소와 24자 이상의 토큰이 필요합니다.";syncPanel();return}
    syncConf={url,token};localStorage.setItem(syncConfKey,JSON.stringify(syncConf));syncBooted=false;syncRev={};syncPending={};syncError="";await syncStart(true);
  };
  $("syncDisconnect").onclick=()=>{syncConf=null;localStorage.removeItem(syncConfKey);syncBooted=false;syncPending={};syncError="연결을 해제했습니다. 휴대폰 기록은 보존됩니다.";syncPanel()};
}
async function syncReq(path,method,body){
  if(!syncConf)throw Error('No sync configuration');
  const res=await fetch(syncConf.url+path,{method:method||"GET",headers:{"Authorization":"Bearer "+syncConf.token,"Content-Type":"application/json"},body:body?JSON.stringify(body):undefined,cache:"no-store"});
  if(!res.ok)throw Error('동기화 서버 오류 ('+res.status+')');return res.json();
}
function syncQueueDay(k,b){if(!syncConf)return;syncPending[k]=structuredClone(b);syncFlush()}
function syncQueueRoutine(){if(!syncConf)return;syncPending.routine=routineCustom?routineData():{};syncFlush()}
async function syncFlush(){
  if(syncBusy||!syncBooted||!syncConf||!Object.keys(syncPending).length)return;
  syncBusy=true;
  try{
    for(const k of Object.keys(syncPending)){
      const data=syncPending[k];const ep=k==='routine'?'/api/routine':'/api/day/'+k;
      try{
        const out=await syncReq(ep,'PUT',{data,revision:syncRev[k]||0});syncRev[k]=out.revision;
        if(syncPending[k]===data)delete syncPending[k];
      }catch(e){if(String(e).includes('409')){syncError='동일 날짜가 다른 기기에서 변경됐습니다. 충돌을 확인하세요.';}throw e}
    }
    syncError='';
  }catch(e){syncError=e.message;}
  finally{syncBusy=false;syncPanel()}
}
async function syncPoll(){
  if(!syncConf||!syncBooted||syncBusy||Object.keys(syncPending).length)return;
  try{
    const state=await syncReq('/api/state');
    let changed=false;
    for(const [k,remote] of Object.entries(state.days||{})){
      const nextRev=state.revisions[k]||0;
      if(nextRev!==(syncRev[k]||0)){
        docs[k]=norm(remote);syncRev[k]=nextRev;changed=true;
      }
    }
    if((state.revisions.routine||0)!==(syncRev.routine||0)){
      if(state.routine && Object.keys(state.routine).length){applyRoutine(state.routine);await backend.saveRoutine(state.routine)}
      syncRev.routine=state.revisions.routine||0;changed=true;
    }
    if(changed){await backend.saveAll();render()}
    syncError='';
  }catch(e){syncError=e.message;}
  syncPanel();
}
async function syncStart(force=false){
  syncPanel();if(syncTimer)clearInterval(syncTimer);syncTimer=setInterval(()=>{syncFlush().then(syncPoll)},5000);
  if(!syncConf)return;
  try{
    const state=await syncReq('/api/state');
    const remoteCount=Object.keys(state.days||{}).length;
    const localCount=Object.keys(docs).length;
    if(remoteCount&&localCount&&!syncBooted){
      // Guard against overwriting local records when pairing a pre-existing remote account.
      const remoteKeys=Object.keys(state.days);
      const diff=remoteKeys.some(k=>JSON.stringify(docs[k])!==JSON.stringify(norm(state.days[k])));
      if(diff&&!confirm('서버에 기존 기록이 있습니다. 서버의 기록으로 휴대폰 기록을 교체할까요? 먼저 JSON 백업을 권장합니다.')){
        syncError='기록 보호를 위해 연결을 보류했습니다. 백업 후 다시 시도하세요.';
        syncConf=null;localStorage.removeItem(syncConfKey);syncPanel();return;
      }
    }
    if(remoteCount){
      docs={};for(const [k,b] of Object.entries(state.days))docs[k]=norm(b);
      if(state.routine && Object.keys(state.routine).length){applyRoutine(state.routine);await backend.saveRoutine(state.routine)}
      await backend.saveAll();syncRev={...state.revisions};render();
    }else{
      syncRev={...state.revisions};
      for(const [k,b] of Object.entries(docs))syncPending[k]=structuredClone(b);
      syncPending.routine=routineCustom?routineData():{};
    }
    syncBooted=true;syncError='';await syncFlush();syncPanel();
  }catch(e){syncError=e.message;syncPanel()}
}
'''
s=s.replace('// ---------- 휴식 타이머 ----------',code+'\n// ---------- 휴식 타이머 ----------',1)
# fix server empty state sync routine custom: {} accepted
s=s.replace('const CACHE = "split3-v5"','const CACHE = "split3-v6"')
p.write_text(s)
sw=Path(__file__).parent/'web'/'sw.js';sw.write_text(sw.read_text().replace('split3-v5','split3-v6'))
