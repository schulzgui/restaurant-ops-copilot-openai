'use strict';
let token = '', role = '';
const el = id => document.getElementById(id);
async function api(path, body) {
  const response = await fetch(path, {method:body === undefined ? 'GET':'POST', headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json'}, body:body === undefined ? undefined : JSON.stringify(body)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Falha na solicitação');
  return result;
}
function node(tag,text,cls) {const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n;}
async function refresh() {
  const d=await api('/api/dashboard'); role=d.role;
  el('connection').textContent='Conectado como '+(role==='reviewer'?'revisor':'operador')+'.';
  el('mode').textContent=d.mode==='live'?'OPENAI · LLM REAL':'FIXTURE DE TESTE';
  el('count-orders').textContent=d.orders.length;
  el('count-pending').textContent=d.proposals.filter(p=>p.state==='pending_review').length;
  el('count-receipts').textContent=d.receipts.length;
  el('run').disabled=role!=='operator';el('dispatch').disabled=role!=='reviewer';
  el('order-list').replaceChildren(...d.orders.map(o=>{const tr=document.createElement('tr');[o.id,o.status,o.delay_minutes+' min',o.issue].forEach(v=>tr.append(node('td',v)));return tr;}));
  el('proposal-list').replaceChildren(...d.proposals.map(p=>{
    const card=node('article','','card');card.append(node('h3',p.order_id+' · '+p.priority),node('p',p.state+' · '+p.policy_id+' · versão '+p.version,'meta'),node('p',p.message));
    if(p.state==='pending_review') for(const [decision,label] of [['approve','Aprovar'],['reject','Rejeitar']]) {
      const b=node('button',label,decision==='reject'?'reject':'');b.disabled=role!=='reviewer';
      b.onclick=async()=>{b.disabled=true;try{await api('/api/review',{proposal_id:p.id,decision,version:p.version});await refresh();el('action-status').textContent='Decisão registrada.';}catch(e){el('action-status').textContent=e.message;b.disabled=false;}};card.append(b);
    }return card;
  }));
  if(!d.proposals.length)el('proposal-list').append(node('p','Nenhuma proposta registrada. Execute uma análise como operador.'));
  el('history').textContent=JSON.stringify({runs:d.runs,outbox:d.outbox,receipts:d.receipts},null,2);
}
el('connect').onclick=async()=>{token=el('token').value.trim();el('token').value='';try{await refresh();}catch(e){el('connection').textContent=e.message;}};
document.querySelectorAll('[data-prompt]').forEach(b=>b.onclick=()=>{el('prompt').value=b.dataset.prompt;el('prompt').focus();});
el('ask').onsubmit=async e=>{e.preventDefault();el('run').disabled=true;el('answer').textContent='Consultando evidências…';try{const r=await api('/api/run',{prompt:el('prompt').value});el('answer').textContent=r.answer;el('trace').textContent=JSON.stringify(r,null,2);await refresh();}catch(e){el('answer').textContent=e.message;}finally{el('run').disabled=role!=='operator';}};
el('dispatch').onclick=async()=>{try{const r=await api('/api/dispatch',{});await refresh();el('action-status').textContent=r.receipts.length+' recibos locais gravados. Nenhuma mensagem externa enviada.';}catch(e){el('action-status').textContent=e.message;}};
el('audit').onclick=async()=>{try{el('audit-result').textContent=JSON.stringify(await api('/api/audit'),null,2);}catch(e){el('audit-result').textContent=e.message;}};
fetch('/health').then(r=>r.json()).then(r=>{el('mode').textContent=r.mode==='live'?'OPENAI · LLM REAL':'FIXTURE DE TESTE';});
el('run').disabled=true;el('dispatch').disabled=true;
