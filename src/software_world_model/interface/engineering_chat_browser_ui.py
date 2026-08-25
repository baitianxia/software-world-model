"""Same-origin browser assets for the ITER-010 Engineering Chat access page."""

ENGINEERING_CHAT_BROWSER_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Software World Model · Engineering Chat</title>
  <style>
    :root{color-scheme:dark;--ink:#f3f7f5;--muted:#93a49d;--bg:#07100d;--panel:#0c1713;--panel2:#101f1a;--line:#274139;--mint:#7ce9b0;--lime:#d9ff70;--warn:#ffbd72;--danger:#ff8f91;font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(circle at 18% -8%,#183e31 0,transparent 34%),var(--bg);color:var(--ink)}button,textarea{font:inherit}button{cursor:pointer}header{height:72px;padding:0 max(20px,calc((100vw - 1280px)/2));display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid var(--line);background:rgba(7,16,13,.88);backdrop-filter:blur(16px);position:sticky;top:0;z-index:3}.brand{display:flex;align-items:center;gap:12px}.mark{width:31px;height:31px;border:1px solid var(--mint);display:grid;place-items:center;color:var(--lime);font:800 11px ui-monospace,monospace}.brand strong{display:block;font-size:14px}.brand small{display:block;color:var(--muted);margin-top:2px}.badges{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}.badge{padding:7px 9px;border:1px solid var(--line);font:750 10px ui-monospace,monospace;letter-spacing:.04em}.badge.protocol{color:var(--mint)}.badge.warning{color:var(--danger)}main{max-width:1280px;margin:0 auto;padding:24px 20px 44px;display:grid;grid-template-columns:310px minmax(0,1fr);gap:18px}.sidebar,.chat{border:1px solid var(--line);background:rgba(12,23,19,.92)}.sidebar{padding:20px;height:calc(100vh - 116px);position:sticky;top:92px;overflow:auto}.sidebar h1{font-size:23px;line-height:1.16;letter-spacing:-.035em;margin:8px 0 10px}.eyebrow{color:var(--mint);font:800 10px ui-monospace,monospace;letter-spacing:.13em}.lede,.small{color:var(--muted);line-height:1.6}.lede{font-size:13px;margin-bottom:20px}.small{font-size:11px}.primary,.secondary{width:100%;border:0;padding:12px 14px;font-weight:800}.primary{background:var(--lime);color:#07100d}.secondary{background:transparent;color:var(--ink);border:1px solid var(--line);margin-bottom:20px}.primary:disabled,.secondary:disabled{opacity:.45;cursor:not-allowed}.facts{border-top:1px solid var(--line);margin-top:18px;padding-top:16px}.fact{margin-bottom:14px}.fact span{display:block;color:var(--muted);font:700 9px ui-monospace,monospace;text-transform:uppercase;letter-spacing:.09em;margin-bottom:4px}.fact code{display:block;color:#cbd8d2;font:10px/1.5 ui-monospace,monospace;overflow-wrap:anywhere}.status{display:flex;align-items:flex-start;gap:8px}.dot{width:7px;height:7px;border-radius:50%;background:var(--warn);margin-top:5px;box-shadow:0 0 15px var(--warn)}ul{padding-left:17px;margin:8px 0}.chat{min-height:calc(100vh - 116px);display:grid;grid-template-rows:auto minmax(380px,1fr) auto}.chat-head{padding:16px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:15px;align-items:center}.chat-head strong{font-size:13px}.chat-head code{display:block;color:var(--muted);font:9px/1.5 ui-monospace,monospace;margin-top:3px;overflow-wrap:anywhere}.transcript{padding:28px 20px 36px;overflow-y:auto;max-height:calc(100vh - 285px)}.empty{height:100%;min-height:390px;display:grid;place-items:center;text-align:center}.empty div{max-width:520px}.empty h2{font-size:30px;letter-spacing:-.035em;margin:12px 0}.empty p{color:var(--muted);line-height:1.7}.message{max-width:780px;margin:0 0 20px;padding:16px 18px;border:1px solid var(--line);position:relative}.message.user{margin-left:auto;background:#152a22;border-color:#315a4b}.message.assistant{margin-right:auto;background:#0a1511}.message.limitation{border-color:#694a3b}.message-head{display:flex;justify-content:space-between;gap:14px;margin-bottom:9px;color:var(--muted);font:750 9px ui-monospace,monospace;letter-spacing:.07em}.message-body{white-space:pre-wrap;overflow-wrap:anywhere;font-size:15px;line-height:1.72}.turn-failure{color:var(--warn)}.composer{border-top:1px solid var(--line);padding:16px 18px;background:#09130f}.composer-row{display:grid;grid-template-columns:minmax(0,1fr) 112px;gap:10px;align-items:end}textarea{width:100%;min-height:76px;max-height:190px;resize:vertical;padding:13px 14px;background:#06100d;color:var(--ink);border:1px solid var(--line);line-height:1.55}textarea:focus{outline:2px solid rgba(124,233,176,.16);border-color:var(--mint)}.notice{min-height:18px;margin:8px 1px 0;color:var(--muted);font-size:11px}.notice.error{color:var(--danger)}details{border-top:1px solid var(--line);margin-top:16px;padding-top:14px}summary{cursor:pointer;color:var(--muted);font:700 10px ui-monospace,monospace}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#06100d;border:1px solid var(--line);padding:11px;color:#b8c9c1;font:9px/1.55 ui-monospace,monospace;max-height:260px;overflow:auto}@media(max-width:840px){header{height:auto;padding-top:13px;padding-bottom:13px;align-items:flex-start}main{grid-template-columns:1fr}.sidebar{height:auto;position:static}.chat{min-height:700px}.transcript{max-height:none}.badges{display:none}}@media(max-width:560px){.composer-row{grid-template-columns:1fr}.chat-head{align-items:flex-start;flex-direction:column}.empty h2{font-size:24px}}
  </style>
  <script src="/assets/engineering-chat.js" defer></script>
</head>
<body>
  <header>
    <div class="brand"><div class="mark">SWM</div><div><strong>Software World Model</strong><small>Conversational Engineering Agent</small></div></div>
    <div class="badges"><span class="badge protocol">ENGINEERING_CHAT_EXPERIENCE@1</span><span class="badge warning">质量未验收 · 非生产</span></div>
  </header>
  <main>
    <aside class="sidebar">
      <p id="experience-label" class="eyebrow">CHAT ACCESS</p>
      <h1>持续对话入口</h1>
      <p id="experience-scope" class="lede">正在读取当前运行的实际能力边界…</p>
      <button id="new-conversation" class="secondary" type="button">＋ 新对话</button>
      <div class="status"><span id="status-dot" class="dot"></span><div><strong id="runtime-status">正在读取运行状态…</strong><p id="provider-status" class="small"></p></div></div>
      <div class="facts">
        <div class="fact"><span>产品版本</span><code id="product-version">—</code></div>
        <div class="fact"><span>工程 / exact revision</span><code id="project-version">—</code></div>
        <div class="fact"><span>Conversation</span><code id="conversation-id">尚未建立</code></div>
        <div class="fact"><span>固定地址</span><code>http://127.0.0.1:8765/</code></div>
      </div>
      <details open><summary>已知限制</summary><ul id="limitations" class="small"></ul></details>
      <details><summary>运行详情</summary><pre id="runtime-details">尚未装载</pre></details>
    </aside>
    <section class="chat" aria-label="工程对话">
      <div class="chat-head"><div><strong>消息历史</strong><code id="conversation-meta">等待服务端建立 Conversation</code></div><span id="turn-status" class="badge">NO TURN</span></div>
      <div id="transcript" class="transcript" aria-live="polite">
        <div id="empty" class="empty"><div><p class="eyebrow">SERVER-OWNED CONVERSATION</p><h2>在同一个对话里继续追问。</h2><p>消息、Turn 与 Context identity 由服务端创建。点击“新对话”会得到空 Context，不继承上一段对话。</p></div></div>
      </div>
      <form id="composer" class="composer">
        <label class="small" for="message">输入工程问题</label>
        <div class="composer-row"><textarea id="message" maxlength="16000" placeholder="例如：登录流程是怎样的？" required></textarea><button id="send" class="primary" type="submit">发送 Turn →</button></div>
        <p id="notice" class="notice">Provider 未配置时会记录失败 Turn；Conversation 仍可继续。</p>
      </form>
    </section>
  </main>
</body>
</html>'''


ENGINEERING_CHAT_BROWSER_JAVASCRIPT = r'''"use strict";
const byId=id=>document.getElementById(id);
let health=null;
let projection=null;
let busy=false;

async function api(path, options={}) {
  const request={...options};
  if (request.body !== undefined) {
    request.headers={"Content-Type":"application/json",...(request.headers||{})};
  }
  const response=await fetch(path,request);
  let value;
  try { value=await response.json(); }
  catch (_) { throw new Error(`HTTP ${response.status}: invalid JSON`); }
  if (!response.ok) throw new Error(value.message||value.error||`HTTP ${response.status}`);
  return value;
}

function setBusy(value) {
  busy=value;
  byId("send").disabled=value||!projection;
  byId("new-conversation").disabled=value;
  byId("message").disabled=value||!projection;
}

function setNotice(message, error=false) {
  const notice=byId("notice");
  notice.textContent=message;
  notice.classList.toggle("error",error);
}

function renderHealth(value) {
  health=value;
  const agentEnabled=value.capabilities.semantic_agent_execution;
  byId("experience-label").textContent=agentEnabled?"ENGINEERING CHAT":"CHAT ACCESS";
  byId("experience-scope").textContent=agentEnabled
    ?"本运行已接入受控主工程 Agent 执行器；只有经过当前 Evidence、fresh Review 和 Delivery Authorization 的 Turn 才会显示为成功。答案质量仍待真实验收。"
    :"本运行只验证 Conversation、Turn、消息历史和失败隔离。Provider 与工程 Agent 未接通，每个 Turn 会如实失败，不会伪造答案。";
  byId("runtime-status").textContent=`${value.status} · ${value.implementation_scope}`;
  byId("provider-status").textContent=`Provider ${value.provider.status} · dispatch ${value.provider.external_dispatch?"ENABLED":"DISABLED"}`;
  byId("product-version").textContent=`${value.product.version} @ ${value.product.revision}`;
  byId("project-version").textContent=`${value.project.name} @ ${value.project.repository_revision}`;
  const list=byId("limitations");
  list.replaceChildren();
  value.known_limitations.forEach(text=>{const item=document.createElement("li");item.textContent=text;list.append(item);});
  byId("runtime-details").textContent=JSON.stringify(value,null,2);
}

function messageNode(message, turns) {
  const article=document.createElement("article");
  article.className=`message ${message.role==="USER"?"user":"assistant"}${message.kind==="LIMITATION"?" limitation":""}`;
  const head=document.createElement("div");
  head.className="message-head";
  const role=document.createElement("span");
  role.textContent=message.role==="USER"?"YOU":"ENGINEERING AGENT";
  const identity=document.createElement("span");
  identity.textContent=`#${message.sequence} · ${message.message_id}`;
  head.append(role,identity);
  const body=document.createElement("div");
  body.className="message-body";
  body.textContent=message.content;
  article.append(head,body);
  if (message.role==="ASSISTANT") {
    const turn=turns.find(item=>item.turn_id===message.turn_id);
    if (turn) {
      const state=document.createElement("p");
      const failed=turn.state==="FAILED";
      state.className=`small${failed?" turn-failure":""}`;
      state.textContent=failed
        ?`Turn ${turn.sequence} · FAILED · ${turn.failure.code} · Provider dispatch ${turn.provider_dispatch_count}`
        :`Turn ${turn.sequence} · ${turn.state} · ${turn.quality_status} · Provider dispatch ${turn.provider_dispatch_count}`;
      article.append(state);
    }
  }
  return article;
}

function renderProjection(value) {
  projection=value;
  const conversation=value.conversation;
  byId("conversation-id").textContent=conversation.conversation_id;
  byId("conversation-meta").textContent=`revision ${conversation.revision} · ${conversation.state} · Context ${conversation.context_digest}`;
  const lastTurn=value.turns[value.turns.length-1];
  byId("turn-status").textContent=lastTurn?`TURN ${lastTurn.sequence} · ${lastTurn.state}`:"NO TURN";
  byId("turn-status").classList.toggle("warning",Boolean(lastTurn&&lastTurn.state==="FAILED"));
  const transcript=byId("transcript");
  transcript.replaceChildren();
  if (value.messages.length===0) {
    const empty=document.createElement("div");
    empty.className="empty";
    const box=document.createElement("div");
    const eyebrow=document.createElement("p");eyebrow.className="eyebrow";eyebrow.textContent="EMPTY CONTEXT";
    const title=document.createElement("h2");title.textContent="新对话已经建立。";
    const copy=document.createElement("p");copy.textContent="这里没有上一段对话的消息、指代或工作状态。现在可以提交第一个真实 Turn。";
    box.append(eyebrow,title,copy);empty.append(box);transcript.append(empty);
  } else {
    value.messages.forEach(message=>transcript.append(messageNode(message,value.turns)));
    transcript.scrollTop=transcript.scrollHeight;
  }
  setBusy(false);
}

async function newConversation() {
  if (busy) return;
  setBusy(true);
  setNotice("正在由服务端创建空 Conversation…");
  try {
    renderProjection(await api("/v1/engineering-chat/conversations",{method:"POST",body:"{}"}));
    setNotice("新 Conversation 已建立；Context 为空。",false);
    byId("message").focus();
  } catch (error) {
    setNotice(`新建对话失败：${error.message}`,true);
    setBusy(false);
  }
}

byId("new-conversation").addEventListener("click",newConversation);
byId("composer").addEventListener("submit",async event=>{
  event.preventDefault();
  if (busy||!projection) return;
  const message=byId("message").value.trim();
  if (!message) return;
  const conversation=projection.conversation;
  setBusy(true);
  setNotice("正在提交 Turn…");
  try {
    const value=await api(`/v1/engineering-chat/conversations/${conversation.conversation_id}/turns`,{
      method:"POST",
      body:JSON.stringify({conversation_revision:conversation.revision,message})
    });
    renderProjection(value);
    byId("message").value="";
    const turn=value.submitted_turn;
    if (turn.state==="SUCCEEDED") {
      setNotice(`Turn ${turn.sequence} 已交付：${turn.state} / ${turn.quality_status}。Conversation 保持 ${value.conversation.state}。`,false);
    } else {
      setNotice(`Turn ${turn.sequence} 已记录：${turn.state} / ${turn.failure.code}。Conversation 保持 ${value.conversation.state}。`,true);
    }
  } catch (error) {
    setNotice(`Turn 提交失败：${error.message}`,true);
    setBusy(false);
  }
});

setBusy(true);
api("/health").then(value=>{renderHealth(value);setBusy(false);return newConversation();}).catch(error=>{
  byId("runtime-status").textContent="BLOCKED";
  setNotice(`启动失败：${error.message}`,true);
  setBusy(false);
});'''


__all__ = [
    "ENGINEERING_CHAT_BROWSER_HTML",
    "ENGINEERING_CHAT_BROWSER_JAVASCRIPT",
]
