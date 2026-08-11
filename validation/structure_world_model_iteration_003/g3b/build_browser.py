#!/usr/bin/env python3
"""Build the immutable local G3b evaluation browser from sealed run outputs."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import stat
from typing import Mapping, Sequence

from software_world_model.cross_cutting import canonical_json_bytes, digest_of


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--output-root", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    evidence = _directory(arguments.evidence_root)
    output = _new_directory(arguments.output_root)
    output.mkdir(mode=0o700)
    pages = output / "pages"
    citations = output / "citations"
    pages.mkdir(mode=0o700)
    citations.mkdir(mode=0o700)
    batch = _load(evidence / "batch-result.json")
    batch_core = {
        key: value for key, value in batch.items() if key != "document_digest"
    }
    if batch.get("document_digest") != digest_of(batch_core).value:
        raise RuntimeError("browser batch Result digest is invalid")
    batch_terminals = {
        item["run_key"]: item for item in batch.get("terminals", [])
    }
    entries: list[dict[str, object]] = []
    for terminal_path in sorted((evidence / "runs").glob("*/terminal.json")):
        terminal = _load(terminal_path)
        terminal_core = {
            key: value
            for key, value in terminal.items()
            if key != "document_digest"
        }
        run_directory = terminal_path.parent
        run_key = str(terminal["run_key"])
        if (
            terminal.get("document_digest") != digest_of(terminal_core).value
            or batch_terminals.get(run_key, {}).get("document_digest")
            != terminal.get("document_digest")
        ):
            raise RuntimeError("browser terminal digest is invalid")
        entry: dict[str, object] = {
            "run_key": run_key,
            "case_id": terminal["case_id"],
            "run_number": terminal["run_number"],
            "status": terminal["status"],
            "failure_stage": terminal["failure_stage"],
            "page": None,
            "question": None,
            "citations": [],
        }
        page_source = run_directory / "answer-output" / "evaluation.html"
        if terminal["status"] == "SUCCESS":
            summary_path = _verified_reference(
                terminal.get("answer_summary"), evidence, "Answer summary"
            )
            summary = _load(summary_path)
            page_source = _existing_descendant_file(page_source, evidence)
            page = _load(page_source)
            if (
                page.get("page_digest") != summary.get("page_digest")
                or page.get("page_digest")
                != digest_of(
                    ["WORLD_MODEL_EVALUATION_PAGE_PAYLOAD@1", page.get("page")]
                ).value
            ):
                raise RuntimeError("browser page differs from its sealed summary")
            page_name = f"{terminal_path.parent.name}.json"
            shutil.copy2(page_source, pages / page_name)
            entry["page"] = f"pages/{page_name}"
            entry["question"] = page.get("page", {}).get("request", {}).get(
                "original_question"
            )
            projected: list[dict[str, object]] = []
            for number, value in enumerate(
                terminal.get("citation_projections", []), start=1
            ):
                source = _verified_reference(
                    value.get("projection"), evidence, "Citation projection"
                )
                name = f"{terminal_path.parent.name}-{number:02d}.json"
                shutil.copy2(source, citations / name)
                projected.append(
                    {
                        "result_id": value["result_id"],
                        "seal_digest": value["seal_digest"],
                        "path": f"citations/{name}",
                    }
                )
            entry["citations"] = projected
        entries.append(entry)
    if (
        len(entries) != batch.get("run_count")
        or {item["run_key"] for item in entries}
        != {item["run_key"] for item in batch.get("terminals", [])}
    ):
        raise RuntimeError("browser run index differs from the sealed batch")
    core = {
        "schema": "swm.iter-003.g3b-browser-index@1",
        "environment": "EVALUATION_ONLY",
        "mode": "WORLD_MODEL",
        "implementation_commit": batch["implementation_commit"],
        "batch_result_digest": batch["document_digest"],
        "run_count": len(entries),
        "runs": entries,
        "production_activation": "NOT_EXECUTED",
    }
    index = {**core, "document_digest": digest_of(core).value}
    _write_new(output / "index.json", canonical_json_bytes(index))
    _write_new(output / "index.html", _HTML.encode("utf-8"))
    _write_new(output / "app.js", _JAVASCRIPT.encode("utf-8"))
    _write_new(output / "styles.css", _CSS.encode("utf-8"))
    print(canonical_json_bytes(index).decode("utf-8"))
    return 0


_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ITER-003 · World Model Evaluation</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div class="watermark" aria-label="Evaluation only">EVALUATION_ONLY</div>
  <header>
    <div><span class="eyebrow">ITER-003 / G3b</span><h1>World Model Evidence Console</h1></div>
    <div class="identity"><span id="mode">WORLD_MODEL</span><code id="commit">loading</code></div>
  </header>
  <main>
    <aside>
      <label for="run-select">评测请求</label>
      <select id="run-select"></select>
      <div class="status-card"><span id="run-status">—</span><small id="run-key">—</small></div>
      <nav id="section-nav"></nav>
    </aside>
    <section class="content">
      <article class="hero panel">
        <p class="kicker">原始问题</p><h2 id="question">加载中…</h2>
        <div class="answer" id="answer"></div>
      </article>
      <section class="metrics" id="metrics"></section>
      <section class="panel" id="binding"><h3>Exact Read Binding</h3><div class="body"></div></section>
      <section class="panel" id="views"><h3>Views · Coverage · Modality</h3><div class="toolbar"><button id="show-a">A</button><button id="show-b">B</button><button id="show-all" class="active">A / B</button></div><div class="body"></div></section>
      <section class="panel" id="limitations"><h3>View Limitation / Knowledge Gap</h3><div class="body"></div></section>
      <section class="panel" id="citations"><h3>Fact / Evidence Citations</h3><div class="body"></div><pre id="citation-detail">点击引用后由独立 Citation Projector 加载。</pre></section>
      <section class="panel" id="authority"><h3>完整权威链</h3><div class="body chain"></div></section>
      <section class="panel" id="raw"><details><summary>Sealed page payload</summary><pre class="body"></pre></details></section>
    </section>
  </main>
  <script src="app.js"></script>
</body>
</html>
"""


_CSS = """:root{color-scheme:dark;--bg:#07110f;--panel:#0e1d19;--line:#284139;--ink:#edf8f2;--muted:#91aca2;--mint:#77f2b5;--amber:#ffc56e;--red:#ff7f76}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 80% 0,#16332a 0,transparent 32%),var(--bg);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,sans-serif}.watermark{position:fixed;z-index:9;right:24px;bottom:18px;color:#77f2b555;border:1px solid #77f2b533;padding:7px 12px;letter-spacing:.18em;font-weight:800;pointer-events:none}header{height:92px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 32px;background:#07110fcc;backdrop-filter:blur(12px);position:sticky;top:0;z-index:5}.eyebrow,.kicker{color:var(--mint);font-size:11px;letter-spacing:.16em;text-transform:uppercase}h1{font-size:24px;margin:2px 0}h2{font-size:26px;max-width:900px;margin:4px 0 20px}h3{margin:0 0 16px;font-size:17px}.identity{text-align:right}.identity span{display:block;color:var(--mint);font-weight:800}.identity code{color:var(--muted);font-size:11px}main{display:grid;grid-template-columns:260px minmax(0,1fr);max-width:1500px;margin:auto}aside{border-right:1px solid var(--line);min-height:calc(100vh - 92px);padding:28px 22px;position:sticky;top:92px;align-self:start}label{display:block;color:var(--muted);font-size:12px;margin-bottom:8px}select{width:100%;background:#132721;color:var(--ink);border:1px solid var(--line);padding:11px;border-radius:8px}.status-card{margin:16px 0;padding:14px;border:1px solid var(--line);background:#0b1714;border-radius:8px}.status-card span{display:block;color:var(--mint);font-weight:800}.status-card small{display:block;color:var(--muted);overflow-wrap:anywhere;margin-top:4px}nav a{display:block;color:var(--muted);text-decoration:none;padding:7px 0}.content{padding:30px;min-width:0}.panel{background:linear-gradient(145deg,#10231d,#0b1714);border:1px solid var(--line);border-radius:12px;padding:22px;margin-bottom:18px;box-shadow:0 18px 60px #0003}.hero{border-top:3px solid var(--mint)}.answer{white-space:pre-wrap;font-size:16px}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:18px}.metric{border:1px solid var(--line);border-radius:10px;padding:15px;background:#0b1714}.metric b{display:block;color:var(--mint);font-size:19px}.metric small{color:var(--muted)}pre{white-space:pre-wrap;overflow:auto;background:#06100d;border:1px solid #20372f;border-radius:8px;padding:14px;color:#c8e3d8}.view,.binding-row,.chain-row,.citation{border-left:2px solid var(--line);padding:10px 14px;margin:8px 0;background:#091411}.view b,.chain-row b{color:var(--mint)}.muted{color:var(--muted)}.warn{color:var(--amber)}.fail{color:var(--red)}button{background:#12261f;border:1px solid var(--line);color:var(--ink);padding:7px 12px;border-radius:7px;margin-right:6px;cursor:pointer}button.active,button:hover{border-color:var(--mint);color:var(--mint)}.toolbar{margin:-4px 0 12px}.citation button{margin-top:8px}@media(max-width:900px){main{display:block}aside{position:static;min-height:0;border-right:0;border-bottom:1px solid var(--line)}.metrics{grid-template-columns:repeat(2,1fr)}header{padding:0 16px}.content{padding:16px}}
"""


_JAVASCRIPT = """'use strict';
const $=id=>document.getElementById(id);let indexData,currentPage,currentEntry,filter='ALL';
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
async function boot(){indexData=await (await fetch('index.json')).json();$('commit').textContent=indexData.implementation_commit;$('mode').textContent=indexData.mode;for(const run of indexData.runs){const o=el('option','',`${run.case_id} · #${run.run_number} · ${run.status}`);o.value=run.run_key;$('run-select').append(o)}$('run-select').addEventListener('change',()=>loadRun($('run-select').value));for(const id of ['binding','views','limitations','citations','authority','raw']){const a=el('a','',document.querySelector(`#${id} h3, #${id} summary`)?.textContent||id);a.href=`#${id}`;$('section-nav').append(a)}$('show-a').onclick=()=>setFilter('A');$('show-b').onclick=()=>setFilter('B');$('show-all').onclick=()=>setFilter('ALL');await loadRun(indexData.runs[0].run_key)}
async function loadRun(key){currentEntry=indexData.runs.find(x=>x.run_key===key);$('run-status').textContent=currentEntry.status;$('run-status').className=currentEntry.status==='SUCCESS'?'':'fail';$('run-key').textContent=key;$('question').textContent=currentEntry.question||'该运行没有可交付页面';if(!currentEntry.page){renderFailure(currentEntry.failure_stage);return}currentPage=(await (await fetch(currentEntry.page)).json()).page;render()}
function render(){const p=currentPage;$('question').textContent=p.request.original_question;$('answer').textContent=p.answer.body;const b=p.execution_boundary;const metrics=[['Provider calls',b.provider_call_count],['Network ops',b.network_operation_count],['Snapshots',p.read_binding.snapshots.length],['Authority stages',p.authority_chain.stages.length]];$('metrics').replaceChildren(...metrics.map(([k,v])=>{const n=el('div','metric');n.append(el('b','',String(v)),el('small','',k));return n}));renderBinding(p);renderViews(p);renderLimitations(p);renderCitations(p);renderAuthority(p);$('raw').querySelector('pre').textContent=JSON.stringify(p,null,2)}
function renderFailure(stage){currentPage=null;$('answer').textContent=`Failure stage: ${stage}`;$('metrics').replaceChildren();for(const id of ['binding','views','limitations','citations','authority'])$(id).querySelector('.body').replaceChildren();$('citation-detail').textContent='该运行没有 Citation Projection。';$('raw').querySelector('pre').textContent='No deliverable page.'}
function renderBinding(p){const root=$('binding').querySelector('.body');root.replaceChildren();const rows=[['Session',p.read_binding.session_id],['Read Set',p.read_binding.read_set_digest],['Ordered Bundle',p.read_binding.ordered_bundle_digest],['Profiles',p.read_binding.profile_refs.join(', ')]];for(const [k,v] of rows){const n=el('div','binding-row');n.append(el('b','',k+' · '),el('code','',String(v)));root.append(n)}for(const [i,s] of p.read_binding.snapshots.entries()){const n=el('div','binding-row');n.append(el('b','',`Snapshot ${i?'B':'A'} · `),el('code','',s.snapshot_id),el('div','muted',s.source_revision));root.append(n)}}
function renderViews(p){const root=$('views').querySelector('.body');root.replaceChildren();const views=[...p.views.candidate_resolution_views.map(x=>x.view),...p.views.query_result_views.map(x=>x.view)];views.forEach(v=>{const indexes=new Set((v.coverage||[]).map(c=>p.read_binding.snapshots.findIndex(s=>s.source_revision===c.source_revision)).filter(i=>i>=0));const label=indexes.size>1?'AB':indexes.has(0)?'A':indexes.has(1)?'B':'AB';if(filter!=='ALL'&&label!==filter&&label!=='AB')return;const n=el('div','view');n.dataset.snapshot=label;n.append(el('b','',`${label} · ${v.operation}`),el('div','muted',`${v.completeness} · ${v.relation_modalities.join(', ')}`),el('pre','',JSON.stringify(v.result_payload,null,2)));root.append(n)})}
function setFilter(value){filter=value;for(const id of ['show-a','show-b','show-all'])$(id).classList.remove('active');$(`show-${value==='ALL'?'all':value.toLowerCase()}`).classList.add('active');renderViews(currentPage)}
function renderLimitations(p){const root=$('limitations').querySelector('.body');root.replaceChildren();const items=p.limitations.length?p.limitations:[{source:'page',code:'NONE',detail:'Coverage 对本问题完整，无额外 limitation。'}];for(const x of items){const n=el('div',x.code==='NONE'?'view':'view warn');n.append(el('b','',x.code),el('div','',x.detail||x.source));root.append(n)}}
function renderCitations(p){const root=$('citations').querySelector('.body');root.replaceChildren();const ids=new Set();for(const group of [p.views.candidate_resolution_views,p.views.query_result_views])for(const x of group){for(const id of x.view.evidence_metadata_ids||[])ids.add(id)}const projected=new Map(currentEntry.citations.map(x=>[x.result_id,x]));for(const [resultId,c] of projected){const n=el('div','citation');n.append(el('b','',resultId),el('div','muted',c.seal_digest));const button=el('button','','打开独立 Citation Projection');button.onclick=async()=>{$('citation-detail').textContent='加载中…';const value=await (await fetch(c.path)).json();$('citation-detail').textContent=JSON.stringify(value.citation_projection,null,2)};n.append(button);root.append(n)}if(!projected.size)root.append(el('div','muted',`本页密封 Evidence metadata ${ids.size} 项；此 Knowledge Gap 无正文投影。`))}
function renderAuthority(p){const root=$('authority').querySelector('.body');root.replaceChildren();p.authority_chain.stages.forEach((x,i)=>{const n=el('div','chain-row');n.append(el('b','',`${String(i+1).padStart(2,'0')} · ${x.stage}`),el('div','muted',x.authority_id),el('code','',x.authority_digest));root.append(n)})}
boot().catch(err=>{$('answer').textContent=`Browser artifact failed closed: ${err.name}`});
"""


def _load(path: Path) -> Mapping[str, object]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"document is not a regular file: {path}")
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise ValueError(f"document is not canonical JSON: {path}")
    return value


def _verified_reference(
    value: object,
    root: Path,
    label: str,
) -> Path:
    if not isinstance(value, dict) or set(value) != {"path", "digest", "size"}:
        raise ValueError(f"{label} reference is not closed")
    path = _existing_descendant_file(Path(str(value["path"])), root)
    if (
        value["digest"] != "sha256:" + sha256(path.read_bytes()).hexdigest()
        or value["size"] != path.stat().st_size
    ):
        raise RuntimeError(f"{label} reference drifted")
    return path


def _existing_descendant_file(path: Path, root: Path) -> Path:
    if (
        not path.is_absolute()
        or path.resolve(strict=True) != path
        or not path.is_file()
        or path.is_symlink()
        or not _is_within(path, root)
    ):
        raise ValueError("browser input file escapes its evidence root")
    return path


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _directory(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=True) != path or not path.is_dir() or path.is_symlink():
        raise ValueError("evidence root must be a canonical directory")
    return path


def _new_directory(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=False) != path or path.exists():
        raise ValueError("browser output must be a new canonical directory")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("browser output parent must be canonical")
    return path


def _write_new(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        remaining = memoryview(payload)
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError("browser artifact is not a regular file")
    finally:
        os.close(descriptor)


if __name__ == "__main__":
    raise SystemExit(main())
