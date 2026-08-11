"""Static same-origin assets for the evaluation-only World Model browser."""

WORLD_MODEL_BROWSER_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>World Model · Evaluation Lab</title>
  <link rel="stylesheet" href="/assets/world-model.css">
</head>
<body>
  <div class="ambient ambient-a"></div>
  <div class="ambient ambient-b"></div>
  <header class="topbar">
    <a class="brand" href="/" aria-label="World Model 首页">
      <span class="brand-mark">WM</span>
      <span><strong>Software World Model</strong><small>Snapshot-first answer lab</small></span>
    </a>
    <div class="mode-rack" aria-label="当前执行模式">
      <span class="mode mode-world">WORLD_MODEL</span>
      <span class="mode mode-eval">EVALUATION_ONLY</span>
      <span id="service-state" class="service-state">正在校验服务…</span>
    </div>
  </header>

  <main>
    <section class="hero">
      <div>
        <p class="eyebrow">ITER-004 · INTERACTIVE EXPERIENCE</p>
        <h1>对已验收的软件世界模型<br><em>自由提问</em></h1>
        <p class="lede">选择固定的 Maven Structure 快照，输入你真正想问的问题。每次发送都会运行 ITER-003 已验收的 Answer、Gateway 与 Citation 链，不会转入旧 Direct 流程。</p>
      </div>
      <aside class="boundary-card">
        <span class="boundary-title">执行边界</span>
        <dl>
          <div><dt>每个问题</dt><dd>1 次模型调用</dd></div>
          <div><dt>隐藏重试</dt><dd>0</dd></div>
          <div><dt>读取权限</dt><dd>固定 Read Bundle</dd></div>
          <div><dt>生产激活</dt><dd>未执行</dd></div>
        </dl>
      </aside>
    </section>

    <section class="workspace">
      <div class="composer-panel panel">
        <div class="section-heading">
          <span class="step">01</span>
          <div><h2>选择正式 Read Set</h2><p>不能输入仓库路径，也不会在提问时扫描工作树。</p></div>
        </div>
        <div id="datasets" class="dataset-grid" role="radiogroup" aria-label="固定数据集"></div>

        <div class="section-heading question-heading">
          <span class="step">02</span>
          <div><h2>输入问题</h2><p>覆盖 Maven reactor 模块、依赖、插件、属性及 A/B 结构差异；超出覆盖会明确返回 Knowledge Gap。</p></div>
        </div>
        <form id="question-form">
          <label class="sr-only" for="question">问题</label>
          <textarea id="question" maxlength="8000" rows="6" placeholder="例如：快照 B 相比 A 新增了哪个 reactor 模块？它在 B 中声明了哪些直接依赖？" required></textarea>
          <div class="examples" aria-label="示例问题">
            <button type="button" class="example" data-question="快照 B 相比 A 新增了哪个 reactor 模块？">A/B 新增模块</button>
            <button type="button" class="example" data-question="列出 B 中所有 reactor 子模块，并说明总数。">模块清单</button>
            <button type="button" class="example" data-question="为什么这个项目采用当前架构，而不是微服务？">设计动机（应返回 Gap）</button>
          </div>
          <div class="submit-row">
            <p id="disclosure">发送即会把本问题和已发布的无 payload Structure 发给已授权模型服务。</p>
            <button id="submit" class="ask-button" type="submit"><span>运行完整链路</span><b aria-hidden="true">→</b></button>
          </div>
        </form>
      </div>

      <div id="result-panel" class="result-panel panel" aria-live="polite">
        <div id="empty-state" class="empty-state">
          <div class="orbit"><span></span><i></i></div>
          <h2>等待一个真实问题</h2>
          <p>结果会在这里显示答案、Read Binding、Coverage、Gap、十阶段 Authority 与独立 Citation。</p>
        </div>
        <div id="loading-state" class="loading-state hidden">
          <div class="scan"><i></i></div>
          <p class="eyebrow">ISOLATED EXECUTION IN PROGRESS</p>
          <h2>正在通过世界模型推理…</h2>
          <ol>
            <li class="active">装载固定 Snapshot Bundles</li>
            <li>启动隔离 Answer 与 exact Gateway</li>
            <li>密封 Authority Result</li>
            <li>独立投影 Citations</li>
          </ol>
          <p class="loading-note">这是真实外部调用，通常需要数十秒。请勿刷新或重复发送。</p>
        </div>
        <div id="error-state" class="error-state hidden">
          <span>EXECUTION FAILED CLOSED</span>
          <h2 id="error-title">请求失败</h2>
          <p id="error-message"></p>
          <button id="retry" type="button">返回提问</button>
        </div>
        <article id="answer-state" class="answer-state hidden">
          <div class="answer-topline">
            <div><p class="eyebrow">SEALED WORLD MODEL RESULT</p><h2>回答</h2></div>
            <div id="answer-badges"></div>
          </div>
          <blockquote id="original-question"></blockquote>
          <div id="answer-body" class="answer-body"></div>
          <div id="metrics" class="metrics"></div>

          <details open>
            <summary>Claims & Citations <span id="claim-count"></span></summary>
            <div id="claims" class="claims"></div>
          </details>
          <details>
            <summary>Read Binding & Views</summary>
            <div id="read-binding" class="json-cards"></div>
          </details>
          <details>
            <summary>10-stage Authority Chain</summary>
            <ol id="authority" class="authority"></ol>
          </details>
          <footer id="result-footer"></footer>
        </article>
      </div>
    </section>
  </main>

  <dialog id="citation-dialog">
    <form method="dialog"><button aria-label="关闭引用">×</button></form>
    <div id="citation-content"></div>
  </dialog>
  <script src="/assets/world-model.js" defer></script>
</body>
</html>
'''


WORLD_MODEL_BROWSER_CSS = r'''
:root{--bg:#07100f;--panel:rgba(13,27,25,.86);--panel2:#112724;--ink:#ecf6ef;--muted:#91aaa0;--line:rgba(177,220,201,.15);--mint:#88f0bc;--acid:#d9ff72;--orange:#ffb76b;--danger:#ff8b8b;--mono:"SFMono-Regular",Consolas,"Liberation Mono",monospace;--sans:Inter,ui-sans-serif,system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
*{box-sizing:border-box}html{background:var(--bg);color:var(--ink);font-family:var(--sans)}body{margin:0;min-height:100vh;background:radial-gradient(circle at 45% -10%,rgba(74,181,137,.14),transparent 38%),linear-gradient(180deg,#07100f 0%,#091412 100%);overflow-x:hidden}.ambient{position:fixed;border-radius:50%;filter:blur(100px);pointer-events:none;opacity:.15}.ambient-a{width:35vw;height:35vw;background:#56ffc1;right:-15vw;top:18vh}.ambient-b{width:28vw;height:28vw;background:#d9ff72;left:-18vw;bottom:-10vw}.topbar{height:82px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 max(28px,calc((100vw - 1420px)/2));position:sticky;top:0;z-index:10;background:rgba(7,16,15,.82);backdrop-filter:blur(18px)}.brand{display:flex;align-items:center;gap:13px;color:var(--ink);text-decoration:none}.brand-mark{width:40px;height:40px;border:1px solid rgba(136,240,188,.45);display:grid;place-items:center;font:700 12px var(--mono);color:var(--mint);background:rgba(136,240,188,.07);clip-path:polygon(14% 0,100% 0,100% 86%,86% 100%,0 100%,0 14%)}.brand strong,.brand small{display:block}.brand strong{font-size:14px;letter-spacing:.03em}.brand small{font:10px var(--mono);color:var(--muted);margin-top:3px}.mode-rack{display:flex;align-items:center;gap:8px}.mode,.service-state{font:700 10px var(--mono);letter-spacing:.08em;padding:7px 9px;border:1px solid}.mode-world{color:var(--mint);border-color:rgba(136,240,188,.3);background:rgba(136,240,188,.06)}.mode-eval{color:var(--orange);border-color:rgba(255,183,107,.3);background:rgba(255,183,107,.06)}.service-state{color:var(--muted);border-color:var(--line)}.service-state.ready{color:var(--acid)}.service-state.failed{color:var(--danger)}main{max-width:1420px;margin:0 auto;padding:64px 28px 70px}.hero{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:70px;align-items:end;margin-bottom:48px}.eyebrow{font:700 10px var(--mono);letter-spacing:.19em;color:var(--mint);margin:0 0 16px}.hero h1{font-size:clamp(40px,5vw,72px);line-height:1.02;letter-spacing:-.055em;margin:0;max-width:900px;font-weight:650}.hero h1 em{font-style:normal;color:var(--acid)}.lede{font-size:16px;line-height:1.7;color:var(--muted);max-width:760px;margin:25px 0 0}.boundary-card{border:1px solid var(--line);background:linear-gradient(145deg,rgba(16,39,34,.9),rgba(8,19,17,.8));padding:20px;box-shadow:0 30px 70px rgba(0,0,0,.22)}.boundary-title{font:700 10px var(--mono);letter-spacing:.15em;color:var(--orange)}.boundary-card dl{margin:15px 0 0}.boundary-card dl div{display:flex;justify-content:space-between;padding:10px 0;border-top:1px solid var(--line);font-size:12px}.boundary-card dt{color:var(--muted)}.boundary-card dd{margin:0;font:600 11px var(--mono)}.workspace{display:grid;grid-template-columns:minmax(420px,.82fr) minmax(500px,1.18fr);gap:18px;align-items:start}.panel{border:1px solid var(--line);background:var(--panel);box-shadow:0 24px 90px rgba(0,0,0,.21);backdrop-filter:blur(14px)}.composer-panel{padding:28px}.section-heading{display:flex;gap:15px;align-items:flex-start}.step{font:700 10px var(--mono);color:var(--acid);border:1px solid rgba(217,255,114,.3);padding:6px}.section-heading h2{font-size:17px;margin:1px 0 5px}.section-heading p{font-size:12px;color:var(--muted);line-height:1.5;margin:0}.dataset-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin:21px 0 32px}.dataset{appearance:none;text-align:left;color:var(--ink);background:rgba(255,255,255,.02);border:1px solid var(--line);padding:14px 12px;min-height:104px;cursor:pointer;transition:.18s ease}.dataset:hover{border-color:rgba(136,240,188,.4);transform:translateY(-1px)}.dataset.selected{border-color:var(--mint);background:rgba(136,240,188,.08);box-shadow:inset 0 0 0 1px rgba(136,240,188,.1)}.dataset strong,.dataset small,.dataset span{display:block}.dataset strong{font:700 11px var(--mono);color:var(--mint)}.dataset span{font-size:12px;margin:9px 0 4px}.dataset small{font:9px var(--mono);color:var(--muted)}.question-heading{padding-top:25px;border-top:1px solid var(--line)}textarea{width:100%;resize:vertical;min-height:148px;margin-top:20px;border:1px solid rgba(177,220,201,.22);background:#07110f;color:var(--ink);font:15px/1.7 var(--sans);padding:17px;outline:none;transition:.18s}textarea:focus{border-color:var(--mint);box-shadow:0 0 0 3px rgba(136,240,188,.08)}textarea::placeholder{color:#587068}.examples{display:flex;flex-wrap:wrap;gap:7px;margin:10px 0 20px}.example{border:1px solid var(--line);background:transparent;color:var(--muted);font-size:10px;padding:7px 9px;cursor:pointer}.example:hover{color:var(--mint);border-color:rgba(136,240,188,.35)}.submit-row{display:flex;align-items:center;justify-content:space-between;gap:20px}.submit-row p{color:var(--muted);font-size:10px;line-height:1.5;max-width:310px;margin:0}.ask-button{border:0;background:var(--acid);color:#07100f;padding:14px 16px 14px 18px;font-weight:800;display:flex;gap:24px;align-items:center;cursor:pointer;white-space:nowrap}.ask-button:hover{background:#e6ff99}.ask-button:disabled{opacity:.45;cursor:not-allowed}.ask-button b{font-size:20px}.result-panel{min-height:628px;padding:28px;position:relative}.hidden{display:none!important}.empty-state,.loading-state,.error-state{min-height:570px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}.empty-state h2,.loading-state h2,.error-state h2{font-size:24px;margin:20px 0 8px}.empty-state p,.loading-note,.error-state p{max-width:460px;color:var(--muted);line-height:1.65;font-size:13px}.orbit{width:100px;height:100px;border:1px solid rgba(136,240,188,.2);border-radius:50%;position:relative;animation:spin 12s linear infinite}.orbit span{position:absolute;inset:18px;border:1px dashed rgba(217,255,114,.35);border-radius:50%}.orbit i{position:absolute;width:10px;height:10px;background:var(--acid);border-radius:50%;top:-5px;left:45px;box-shadow:0 0 20px var(--acid)}@keyframes spin{to{transform:rotate(360deg)}}.scan{width:min(420px,80%);height:2px;background:var(--line);position:relative;margin-bottom:40px;overflow:hidden}.scan i{position:absolute;width:35%;height:100%;background:var(--mint);animation:scan 1.7s ease-in-out infinite}@keyframes scan{0%{left:-35%}100%{left:100%}}.loading-state ol{list-style:none;padding:0;margin:22px 0;text-align:left;color:#5e756d;font:11px/2.1 var(--mono)}.loading-state li::before{content:"○";margin-right:10px}.loading-state li.active{color:var(--mint)}.loading-state li.active::before{content:"●"}.error-state>span{font:700 10px var(--mono);color:var(--danger);letter-spacing:.14em}.error-state button{margin-top:15px;border:1px solid rgba(255,139,139,.35);color:var(--danger);background:transparent;padding:10px 15px;cursor:pointer}.answer-topline{display:flex;justify-content:space-between;align-items:start}.answer-topline h2{font-size:30px;margin:0}.answer-topline .eyebrow{margin-bottom:8px}#answer-badges{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}#answer-badges span{font:700 9px var(--mono);border:1px solid var(--line);padding:6px 8px;color:var(--mint)}#original-question{margin:25px 0 18px;border-left:2px solid var(--acid);background:rgba(217,255,114,.035);padding:12px 15px;color:#b9cbc4;font-size:12px}.answer-body{white-space:pre-wrap;font-size:16px;line-height:1.8;padding:2px 0 22px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);margin-bottom:22px}.metric{padding:12px;border-right:1px solid var(--line)}.metric:last-child{border-right:0}.metric span,.metric strong{display:block}.metric span{font:9px var(--mono);color:var(--muted);text-transform:uppercase}.metric strong{font:700 13px var(--mono);margin-top:6px;color:var(--acid)}details{border-top:1px solid var(--line);padding:14px 0}summary{cursor:pointer;font:700 11px var(--mono);letter-spacing:.08em;color:#c8d7d1}summary span{color:var(--muted)}.claims{display:grid;gap:9px;margin-top:13px}.claim{border:1px solid var(--line);background:rgba(255,255,255,.018);padding:13px}.claim-head{display:flex;justify-content:space-between;gap:15px}.claim-kind{font:700 9px var(--mono);color:var(--orange)}.claim p{font-size:12px;line-height:1.65;color:#c7d5d0}.citation-list{display:flex;flex-wrap:wrap;gap:6px}.citation-button{font:9px var(--mono);color:var(--mint);border:1px solid rgba(136,240,188,.24);background:rgba(136,240,188,.04);padding:6px 8px;cursor:pointer}.json-cards{display:grid;gap:8px;margin-top:13px}.json-card{display:grid;grid-template-columns:140px 1fr;gap:12px;font:10px/1.55 var(--mono);border:1px solid var(--line);padding:10px}.json-card span:first-child{color:var(--muted)}.json-card span:last-child{overflow-wrap:anywhere}.authority{list-style:none;padding:0;margin:13px 0 0;display:grid;grid-template-columns:repeat(2,1fr);gap:7px;counter-reset:auth}.authority li{counter-increment:auth;border:1px solid var(--line);padding:9px;font:10px var(--mono);color:#c8d7d1}.authority li::before{content:counter(auth,decimal-leading-zero);color:var(--acid);margin-right:9px}.answer-state footer{font:9px/1.7 var(--mono);color:#688078;border-top:1px solid var(--line);padding-top:14px;margin-top:5px;overflow-wrap:anywhere}dialog{width:min(900px,92vw);max-height:85vh;background:#0b1916;color:var(--ink);border:1px solid rgba(136,240,188,.35);padding:25px;box-shadow:0 40px 120px #000}dialog::backdrop{background:rgba(0,0,0,.75);backdrop-filter:blur(5px)}dialog form{position:sticky;top:0;float:right}dialog form button{border:1px solid var(--line);background:#0b1916;color:var(--ink);font-size:20px;cursor:pointer}.citation-title{font:700 11px var(--mono);color:var(--mint);overflow-wrap:anywhere}.citation-meta{color:var(--muted);font:10px/1.6 var(--mono);overflow-wrap:anywhere}.citation-item{border-top:1px solid var(--line);padding:15px 0}.citation-item h4{margin:0 0 8px;font:700 11px var(--mono);color:var(--orange)}.citation-item pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#07110f;padding:13px;color:#c9d8d2;font:11px/1.55 var(--mono);max-height:360px;overflow:auto}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}@media(max-width:1000px){.hero{grid-template-columns:1fr}.workspace{grid-template-columns:1fr}.boundary-card{max-width:500px}.result-panel{min-height:520px}}@media(max-width:650px){.topbar{height:auto;padding:14px 18px;align-items:flex-start;gap:12px}.brand small,.service-state{display:none}.mode-rack{flex-wrap:wrap;justify-content:flex-end}main{padding:42px 15px}.hero{gap:28px}.hero h1{font-size:40px}.composer-panel,.result-panel{padding:20px}.dataset-grid{grid-template-columns:1fr}.submit-row{align-items:stretch;flex-direction:column}.ask-button{justify-content:space-between}.metrics{grid-template-columns:repeat(2,1fr)}.metric:nth-child(2){border-right:0}.metric:nth-child(-n+2){border-bottom:1px solid var(--line)}.authority{grid-template-columns:1fr}.json-card{grid-template-columns:1fr}.answer-topline{gap:15px;flex-direction:column}#answer-badges{justify-content:flex-start}}
'''


WORLD_MODEL_BROWSER_JS = r'''
"use strict";
const state={datasets:[],selected:null,busy:false,last:null};
const $=id=>document.getElementById(id);
const els={service:$("service-state"),datasets:$("datasets"),form:$("question-form"),question:$("question"),submit:$("submit"),empty:$("empty-state"),loading:$("loading-state"),error:$("error-state"),answer:$("answer-state"),errorTitle:$("error-title"),errorMessage:$("error-message"),retry:$("retry"),answerBadges:$("answer-badges"),originalQuestion:$("original-question"),answerBody:$("answer-body"),metrics:$("metrics"),claims:$("claims"),claimCount:$("claim-count"),readBinding:$("read-binding"),authority:$("authority"),footer:$("result-footer"),dialog:$("citation-dialog"),citationContent:$("citation-content")};
function node(tag,attrs={},text=""){const n=document.createElement(tag);Object.entries(attrs).forEach(([k,v])=>{if(k==="class")n.className=v;else if(k.startsWith("data-"))n.setAttribute(k,v);else n[k]=v});if(text!=="")n.textContent=String(text);return n}
function clear(n){while(n.firstChild)n.removeChild(n.firstChild)}
function show(which){[els.empty,els.loading,els.error,els.answer].forEach(n=>n.classList.add("hidden"));which.classList.remove("hidden")}
async function request(url,options={}){const response=await fetch(url,{...options,headers:{"Content-Type":"application/json",...(options.headers||{})}});let value;try{value=await response.json()}catch{throw new Error(`HTTP ${response.status}: invalid JSON response`)}if(!response.ok)throw new Error(value.message||value.error||`HTTP ${response.status}`);return value}
function renderDatasets(){clear(els.datasets);state.datasets.forEach((dataset,index)=>{const b=node("button",{type:"button",class:`dataset${dataset.id===state.selected?" selected":""}`,role:"radio"});b.setAttribute("aria-checked",String(dataset.id===state.selected));b.append(node("strong",{},dataset.id));b.append(node("span",{},dataset.label));b.append(node("small",{},`${dataset.snapshot_count} snapshot${dataset.snapshot_count===1?"":"s"}`));b.addEventListener("click",()=>{if(state.busy)return;state.selected=dataset.id;renderDatasets()});els.datasets.append(b);if(index===0&&!state.selected)state.selected=dataset.id});if(state.selected&&!els.datasets.querySelector(".selected"))renderDatasets()}
function badge(text){return node("span",{},text)}
function metric(label,value){const box=node("div",{class:"metric"});box.append(node("span",{},label),node("strong",{},value));return box}
function card(label,value){const box=node("div",{class:"json-card"});box.append(node("span",{},label),node("span",{},typeof value==="string"?value:JSON.stringify(value)));return box}
function renderResult(result){state.last=result;const page=result.page;const answer=page.answer||{};const boundary=page.execution_boundary||{};const summary=result.execution||{};clear(els.answerBadges);els.answerBadges.append(badge(page.mode),badge(page.environment),badge(result.dataset_id));els.originalQuestion.textContent=page.request?.original_question||result.question;els.answerBody.textContent=answer.body||"未生成正文回答。";clear(els.metrics);els.metrics.append(metric("Provider calls",boundary.provider_call_count??"—"),metric("Network ops",boundary.network_operation_count??"—"),metric("Retries",summary.selective_retry_count??0),metric("Elapsed",summary.elapsed_milliseconds==null?"—":`${summary.elapsed_milliseconds} ms`));
 const claims=Array.isArray(answer.claims)?answer.claims:[];els.claimCount.textContent=`${claims.length}`;clear(els.claims);if(!claims.length)els.claims.append(node("p",{},"此结果没有正文 Claim 引用。"));claims.forEach(claim=>{const box=node("section",{class:"claim"}),head=node("div",{class:"claim-head"});head.append(node("span",{class:"claim-kind"},claim.kind||"CLAIM"),node("span",{class:"claim-kind"},claim.gap_code||"SUPPORTED"));box.append(head,node("p",{},claim.text||""));const links=node("div",{class:"citation-list"});(claim.view_result_ids||[]).forEach(resultId=>{const ref=(result.citations||[]).find(item=>item.result_id===resultId);if(ref){const b=node("button",{type:"button",class:"citation-button"},`Open ${resultId.slice(-8)}`);b.addEventListener("click",()=>openCitation(ref));links.append(b)}});box.append(links);els.claims.append(box)});
 const snapshots=(page.read_binding?.snapshots||[]).map(item=>item.snapshot_id);const viewGroups=[...(page.views?.candidate_resolution_views||[]),...(page.views?.query_result_views||[])];const viewIds=viewGroups.map(item=>item.view?.result_id||item.result_id||item.resolution_id||item.step_id||"sealed view");clear(els.readBinding);els.readBinding.append(card("Dataset",result.dataset_id),card("Snapshot IDs",snapshots),card("Read-set digest",page.read_binding?.read_set_digest||"—"),card("View results",viewIds),card("Limitations",page.limitations||[]));
 clear(els.authority);(page.authority_chain?.stages||[]).forEach(item=>els.authority.append(node("li",{},item.stage||JSON.stringify(item))) );
 els.footer.textContent=`Request ${result.request_id} · sealed page ${result.page_digest} · accepted product ${result.accepted_product_commit} · Production Activation NOT_EXECUTED`;show(els.answer)}
async function openCitation(ref){els.citationContent.textContent="正在读取并验签独立 Citation Projection…";els.dialog.showModal();try{const value=await request(ref.url);const projection=value.citation_projection||{};clear(els.citationContent);els.citationContent.append(node("p",{class:"citation-title"},value.result_id),node("p",{class:"citation-meta"},`seal ${value.seal_digest} · projection ${value.projection_digest}`));const citations=Array.isArray(projection.citations)?projection.citations:[];if(!citations.length)els.citationContent.append(node("p",{},"该 Result 没有 Citation observations。"));citations.forEach((citation,index)=>{const box=node("section",{class:"citation-item"});box.append(node("h4",{},`${index+1}. ${citation.locator||citation.artifact_id||"citation"}`),node("p",{class:"citation-meta"},`${citation.evidence_id||""} · bytes ${citation.byte_start??"?"}-${citation.byte_end??"?"}`),node("pre",{},citation.observation||"（无 observation 正文）"));els.citationContent.append(box)})}catch(error){els.citationContent.textContent=`Citation 读取失败：${error.message}`}}
async function submit(event){event.preventDefault();if(state.busy)return;const question=els.question.value.trim();if(!question||!state.selected)return;state.busy=true;els.submit.disabled=true;show(els.loading);const requestId=`wm-${crypto.randomUUID()}`;try{const result=await request("/v1/world-model/questions",{method:"POST",body:JSON.stringify({request_id:requestId,dataset_id:state.selected,question})});renderResult(result)}catch(error){els.errorTitle.textContent="完整链路未生成可验证结果";els.errorMessage.textContent=error.message;show(els.error)}finally{state.busy=false;els.submit.disabled=false}}
async function initialize(){try{const [health,datasets]=await Promise.all([request("/health"),request("/v1/world-model/datasets")]);if(health.mode!=="WORLD_MODEL"||health.environment!=="EVALUATION_ONLY")throw new Error("服务模式不符合 WORLD_MODEL / EVALUATION_ONLY");state.datasets=datasets.datasets||[];state.selected=state.datasets[0]?.id||null;renderDatasets();els.service.textContent=`READY · ${String(health.accepted_product_commit||"").slice(0,9)}`;els.service.classList.add("ready")}catch(error){els.service.textContent="SERVICE BLOCKED";els.service.classList.add("failed");els.errorTitle.textContent="服务未通过启动校验";els.errorMessage.textContent=error.message;show(els.error)}}
els.form.addEventListener("submit",submit);els.retry.addEventListener("click",()=>show(state.last?els.answer:els.empty));document.querySelectorAll(".example").forEach(button=>button.addEventListener("click",()=>{els.question.value=button.dataset.question;els.question.focus()}));initialize();
'''
