"""Product-owned browser surface for the ITER-010 direction preview."""

ENGINEERING_QA_BROWSER_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Software World Model · Engineering QA</title>
  <style>
    :root{color-scheme:dark;--bg:#07110f;--panel:#0d1c18;--line:#27453b;--text:#e9f5ef;--muted:#91aaa0;--mint:#88f0bc;--acid:#d9ff72;--warn:#ffb76b;--danger:#ff8b8b;font-family:Inter,ui-sans-serif,system-ui,sans-serif}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% 0,#153a2e 0,transparent 38%),var(--bg);color:var(--text)}header{border-bottom:1px solid var(--line);padding:18px max(22px,calc((100vw - 1180px)/2));display:flex;justify-content:space-between;gap:20px;align-items:center;background:rgba(7,17,15,.84);position:sticky;top:0;backdrop-filter:blur(14px)}header strong{font-size:14px}header small{display:block;color:var(--muted);margin-top:3px}.badges{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}.badge{font:700 10px ui-monospace,monospace;border:1px solid var(--line);padding:7px 9px}.badge.mode{color:var(--mint)}.badge.preview{color:var(--danger)}main{max-width:1180px;margin:0 auto;padding:64px 22px 80px}.hero{max-width:820px;margin-bottom:36px}.hero p:first-child{font:700 11px ui-monospace,monospace;color:var(--mint);letter-spacing:.15em}.hero h1{font-size:clamp(38px,6vw,70px);line-height:1.03;letter-spacing:-.055em;margin:12px 0}.hero h1 em{font-style:normal;color:var(--acid)}.hero .lede{color:var(--muted);font-size:16px;line-height:1.7}.workspace{display:grid;grid-template-columns:minmax(340px,.8fr) minmax(420px,1.2fr);gap:18px}.panel{border:1px solid var(--line);background:rgba(13,28,24,.9);padding:26px;box-shadow:0 28px 90px rgba(0,0,0,.22)}h2{font-size:18px;margin:0 0 8px}.hint{font-size:12px;color:var(--muted);line-height:1.6}textarea{width:100%;min-height:190px;margin:20px 0 15px;background:#06100d;color:var(--text);border:1px solid var(--line);padding:15px;font:15px/1.65 inherit;resize:vertical}textarea:focus{outline:2px solid rgba(136,240,188,.2);border-color:var(--mint)}button{border:0;background:var(--acid);color:#07110f;font-weight:800;padding:13px 17px;cursor:pointer}button:disabled{opacity:.5;cursor:not-allowed}.state{min-height:430px;display:flex;flex-direction:column;justify-content:center}.hidden{display:none!important}.eyebrow{font:700 10px ui-monospace,monospace;color:var(--mint);letter-spacing:.14em}.answer{font-size:17px;line-height:1.8;white-space:pre-wrap}.question{border-left:2px solid var(--acid);padding:10px 13px;color:var(--muted);font-size:12px;background:rgba(217,255,114,.035)}.citation-list{display:flex;gap:7px;flex-wrap:wrap;margin:18px 0}.citation{background:transparent;border:1px solid rgba(136,240,188,.35);color:var(--mint);font:700 10px ui-monospace,monospace;padding:8px 10px}.error{color:var(--danger)}details{border-top:1px solid var(--line);padding-top:15px;margin-top:20px}summary{cursor:pointer;font:700 11px ui-monospace,monospace;color:var(--muted)}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#06100d;border:1px solid var(--line);padding:13px;color:#bdd0c8;font:10px/1.55 ui-monospace,monospace;max-height:330px;overflow:auto}dialog{width:min(850px,92vw);background:var(--panel);color:var(--text);border:1px solid var(--mint);padding:24px}dialog::backdrop{background:rgba(0,0,0,.75)}dialog form{float:right}dialog form button{background:transparent;color:var(--text);border:1px solid var(--line);padding:5px 10px}@media(max-width:850px){.workspace{grid-template-columns:1fr}.state{min-height:320px}header{align-items:flex-start}.hero h1{font-size:42px}}
  </style>
</head>
<body>
  <header><div><strong>Software World Model</strong><small>认知引导的自适应工程问答</small></div><div class="badges"><span class="badge mode">ENGINEERING_QA</span><span class="badge preview">方向体验 · 非验收 · 非生产</span></div></header>
  <main>
    <section class="hero"><p>WORLD MODEL COGNITION → ADAPTIVE INVESTIGATION</p><h1>先回答工程目标，<em>再展开必要代码。</em></h1><p class="lede">系统从精确版本的软件世界模型认知出发，根据每一步只读调查结果决定下一步；回答与独立审核只读取调查结束后密封的证据包。</p></section>
    <section class="workspace">
      <form id="question-form" class="panel"><h2>提出自然问题</h2><p class="hint">用途、架构、启动、业务流程、配置、故障、影响与实现细节都进入同一协议，不按题型切换后端。</p><label class="hidden" for="question">问题</label><textarea id="question" maxlength="16000" placeholder="例如：这个系统如何启动，哪个配置会影响请求超时？" required></textarea><button id="submit" type="submit">开始受控调查 →</button><p id="health" class="hint">正在验证本机方向体验边界…</p></form>
      <section class="panel">
        <div id="empty" class="state"><p class="eyebrow">READY WHEN YOU ARE</p><h2>答案、Limitation 与 Citation 会显示在这里</h2><p class="hint">World Model Cognition、Ledger、Broker 操作和 Review Finding 默认折叠在开发者详情中。</p></div>
        <div id="loading" class="state hidden"><p class="eyebrow">INVESTIGATING</p><h2>正在按新结果决定下一步…</h2><p class="hint">模型没有文件、Shell、网络或凭据权限；只有 Broker 编译、Worker 只读执行。</p></div>
        <div id="error" class="state hidden"><p class="eyebrow error">FAIL CLOSED</p><h2 id="error-title">未形成可交付答案</h2><p id="error-message" class="hint error"></p></div>
        <article id="result" class="hidden"><p class="eyebrow">REVIEWED RESULT</p><p id="original-question" class="question"></p><div id="answer" class="answer"></div><div id="citations" class="citation-list"></div><details><summary>开发者详情</summary><pre id="details"></pre></details><p id="footer" class="hint"></p></article>
      </section>
    </section>
  </main>
  <dialog id="citation-dialog"><form method="dialog"><button aria-label="关闭">×</button></form><h2>Citation</h2><pre id="citation-content"></pre></dialog>
  <script>
    "use strict";
    const $=id=>document.getElementById(id),states=[$("empty"),$("loading"),$("error"),$("result")];let preparedRequestId=null;
    function show(node){states.forEach(item=>item.classList.add("hidden"));node.classList.remove("hidden")}
    async function api(url,options={}){const response=await fetch(url,{...options,headers:{"Content-Type":"application/json",...(options.headers||{})}});let value;try{value=await response.json()}catch{throw new Error(`HTTP ${response.status}: invalid JSON`)}if(!response.ok)throw new Error(value.message||value.error||`HTTP ${response.status}`);return value}
    function clear(node){while(node.firstChild)node.removeChild(node.firstChild)}
    async function citation(ref){const dialog=$("citation-dialog"),content=$("citation-content");content.textContent="正在读取密封 Result 的 Citation…";dialog.showModal();try{content.textContent=JSON.stringify(await api(ref.url),null,2)}catch(error){content.textContent=`Citation 读取失败：${error.message}`}}
    function render(value){const answer=value.answer;$("original-question").textContent=value.request.original_question;$("answer").textContent=answer?.body||value.limitation?.message||"未授权交付正文。";clear($("citations"));(value.citations||[]).forEach(ref=>{const button=document.createElement("button");button.type="button";button.className="citation";button.textContent=ref.label;button.addEventListener("click",()=>citation(ref));$("citations").append(button)});$("details").textContent=JSON.stringify(value.developer_details,null,2);$("footer").textContent=`Result ${value.result_id} · ${value.status} · Production Activation NOT_EXECUTED`;show($("result"))}
    $("question-form").addEventListener("submit",async event=>{event.preventDefault();const question=$("question").value.trim();if(!question)return;$("submit").disabled=true;show($("loading"));try{render(await api("/v1/engineering-qa/questions",{method:"POST",body:JSON.stringify({request_id:preparedRequestId||`engq-${crypto.randomUUID()}`,question})}))}catch(error){$("error-message").textContent=error.message;show($("error"))}finally{$("submit").disabled=false}});
    api("/health").then(value=>{preparedRequestId=value.prepared_request_id||null;if(value.prepared_question){$("question").value=value.prepared_question}$("health").textContent=`READY · ${value.mode} · ${value.environment}${value.external_provider_dispatch?" · EXACT LIVE GRANT":""}`}).catch(error=>{$("health").textContent=`BLOCKED · ${error.message}`;$("health").classList.add("error")});
  </script>
</body>
</html>'''


__all__ = ["ENGINEERING_QA_BROWSER_HTML"]
