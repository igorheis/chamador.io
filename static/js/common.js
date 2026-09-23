const icons={"Água":"💧","Valo":"🦷","Anestesia":"💉","Gazes":"🩹","Suporte presencial":"👤","Limpeza":"🧹","Abridor":"🔧"};
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const age=iso=>{const seconds=Math.max(0,Math.floor((Date.now()-new Date(iso).getTime())/1000));if(seconds<60)return `${seconds}s`;if(seconds<3600)return `${Math.floor(seconds/60)} min`;return `${Math.floor(seconds/3600)} h ${Math.floor(seconds%3600/60)} min`};
const fmtTime=iso=>iso?new Date(iso).toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"}):"—";
const fmtDate=iso=>iso?new Date(iso).toLocaleDateString("pt-BR"):"—";
function connectLive(onEvent){const proto=location.protocol==="https:"?"wss":"ws";let ws;let stopped=false;const open=()=>{if(stopped)return;ws=new WebSocket(`${proto}://${location.host}/ws`);ws.onmessage=e=>onEvent(JSON.parse(e.data));ws.onclose=()=>setTimeout(open,1400);ws.onerror=()=>ws.close()};open();return {close(){stopped=true;ws?.close()}}}
async function api(url,options={}){const r=await fetch(url,{headers:{"Content-Type":"application/json",...(options.headers||{})},...options});if(!r.ok){const data=await r.json().catch(()=>({}));throw Error(data.detail||"Não foi possível completar a ação.")}return r.status===204?null:r.json()}
function statusLabel(s){return s==="em_atendimento"?"Em atendimento":s==="concluido"?"Concluído":"Solicitado"}
