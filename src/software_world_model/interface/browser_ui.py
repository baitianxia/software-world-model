"""Dependency-free browser chat assets served by the loopback HTTP adapter."""

from __future__ import annotations


BROWSER_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>软件世界模型 · 项目问答</title>
  <meta name="description" content="连接本地 Git 项目，通过浏览器询问代码行为与版本变化。">
  <link rel="stylesheet" href="/assets/browser.css">
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <a class="brand" href="/" aria-label="软件世界模型首页">
        <span class="brand-mark" aria-hidden="true">SW</span>
        <span>
          <strong>软件世界模型</strong>
          <small>本地项目问答</small>
        </span>
      </a>
      <div class="runtime-status" id="runtime-status" role="status" aria-live="polite">
        <span class="status-dot"></span>
        <span id="runtime-status-text">正在检查服务</span>
      </div>
    </header>

    <main class="workspace">
      <aside class="project-panel" aria-labelledby="project-heading">
        <div class="section-kicker">分析范围</div>
        <h1 id="project-heading">连接一个本地项目</h1>
        <p class="section-copy">项目始终从固定的 Git 版本读取。工作区文件不会被修改。</p>

        <form id="project-form" class="project-form">
          <label for="repository-path">项目文件夹</label>
          <input id="repository-path" name="repository_path" type="text"
                 autocomplete="off" placeholder="/Users/you/project" required>
          <p class="field-help">输入包含 Git 仓库的本机绝对路径。</p>

          <div class="field-row">
            <div>
              <label for="revision">分析版本</label>
              <input id="revision" name="revision" type="text" value="HEAD" required>
            </div>
            <div>
              <label for="selected-paths">读取范围</label>
              <input id="selected-paths" name="selected_paths" type="text" value="." required>
            </div>
          </div>
          <p class="field-help">大型项目首次体验建议填写具体模块，例如 mall-security；多个范围用英文逗号分隔。</p>

          <details class="advanced-fields">
            <summary>比较两个版本</summary>
            <label for="comparison-base">比较起点（可选）</label>
            <input id="comparison-base" name="comparison_base" type="text"
                   placeholder="例如 HEAD~1">
            <p class="field-help">填写后，问题会在起点与分析版本之间比较。</p>
          </details>

          <button class="primary-button" id="connect-button" type="submit">
            <span>连接项目</span>
          </button>
        </form>

        <section class="connected-project" id="connected-project" hidden>
          <div class="project-badge">已连接</div>
          <h2 id="connected-name"></h2>
          <dl>
            <div><dt>版本</dt><dd id="connected-revision"></dd></div>
            <div><dt>范围</dt><dd id="connected-paths"></dd></div>
          </dl>
          <button class="text-button" id="change-project" type="button">更换项目</button>
        </section>

        <div class="privacy-note">
          <strong>仅在本机运行</strong>
          <span>页面无需登录，服务不会接受其他设备的连接。</span>
        </div>
      </aside>

      <section class="chat-panel" aria-labelledby="chat-heading">
        <div class="chat-header">
          <div>
            <div class="section-kicker">对话</div>
            <h2 id="chat-heading">询问代码如何工作</h2>
          </div>
          <button class="quiet-button" id="new-conversation" type="button">新对话</button>
        </div>

        <div class="messages" id="messages" role="log" aria-live="polite" aria-label="对话记录">
          <article class="message assistant-message welcome-message">
            <div class="message-label">系统</div>
            <div class="message-body">
              <p>连接项目后，可以直接询问实现流程、异常分支或版本变化。</p>
              <div class="example-grid" aria-label="示例问题">
                <button type="button" class="example-question">这个项目的主要入口和调用流程是什么？</button>
                <button type="button" class="example-question">失败时有哪些异常分支，分别在哪里处理？</button>
                <button type="button" class="example-question">这个版本相对比较起点修改了什么？</button>
              </div>
            </div>
          </article>
        </div>

        <div class="working" id="working" hidden role="status" aria-live="polite">
          <span class="working-mark" aria-hidden="true"></span>
          <span id="working-text">正在理解问题并查阅项目…</span>
          <time id="working-time">0:00</time>
        </div>

        <form class="composer" id="chat-form">
          <label class="sr-only" for="message-input">输入问题</label>
          <textarea id="message-input" name="message" rows="1"
                    placeholder="请先连接一个项目" maxlength="8000" disabled></textarea>
          <div class="composer-footer">
            <span>Enter 发送 · Shift + Enter 换行</span>
            <button class="send-button" id="send-button" type="submit" disabled>
              发送
            </button>
          </div>
        </form>
      </section>
    </main>
  </div>
  <script src="/assets/browser.js" defer></script>
</body>
</html>
"""


BROWSER_CSS = """@charset "UTF-8";
:root {
  --paper: #f5f3ee;
  --surface: #fffefb;
  --surface-muted: #ebe8e0;
  --ink: #20211f;
  --ink-muted: #6f706b;
  --line: #d9d5cb;
  --accent: #274c77;
  --accent-dark: #17344f;
  --accent-soft: #dce7f1;
  --success: #28704c;
  --danger: #a44332;
  --shadow: 0 18px 55px rgba(48, 45, 37, 0.08);
  font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
    "PingFang SC", "Microsoft YaHei", sans-serif;
  color: var(--ink);
  background: var(--paper);
}

* { box-sizing: border-box; }

html, body { min-height: 100%; }

body {
  margin: 0;
  background:
    linear-gradient(rgba(39, 76, 119, 0.028) 1px, transparent 1px),
    linear-gradient(90deg, rgba(39, 76, 119, 0.028) 1px, transparent 1px),
    var(--paper);
  background-size: 28px 28px;
}

button, input, textarea { font: inherit; }
button { color: inherit; }

.shell {
  width: min(1480px, 100%);
  min-height: 100vh;
  margin: 0 auto;
  padding: 0 28px 28px;
}

.topbar {
  height: 82px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: var(--ink);
  text-decoration: none;
}

.brand-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border: 1px solid var(--ink);
  background: var(--ink);
  color: var(--surface);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px;
  letter-spacing: .06em;
}

.brand strong, .brand small { display: block; }
.brand strong { font-size: 15px; letter-spacing: .02em; }
.brand small { margin-top: 2px; color: var(--ink-muted); font-size: 12px; }

.runtime-status {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(255, 254, 251, .7);
  color: var(--ink-muted);
  font-size: 12px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #aaa79f;
  box-shadow: 0 0 0 4px rgba(170, 167, 159, .12);
}

.runtime-status.ready .status-dot { background: var(--success); box-shadow: 0 0 0 4px rgba(40,112,76,.12); }
.runtime-status.blocked .status-dot { background: var(--danger); box-shadow: 0 0 0 4px rgba(164,67,50,.12); }

.workspace {
  min-height: calc(100vh - 110px);
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  border: 1px solid var(--line);
  background: var(--surface);
  box-shadow: var(--shadow);
}

.project-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 34px 30px 28px;
  border-right: 1px solid var(--line);
  background: #f0ede6;
}

.section-kicker {
  margin-bottom: 9px;
  color: var(--accent);
  font-size: 11px;
  font-weight: 750;
  letter-spacing: .13em;
  text-transform: uppercase;
}

.project-panel h1, .chat-header h2 {
  margin: 0;
  font-family: Georgia, "Songti SC", "STSong", serif;
  font-weight: 500;
  letter-spacing: -.025em;
}

.project-panel h1 { font-size: 28px; line-height: 1.18; }
.section-copy { margin: 12px 0 28px; color: var(--ink-muted); font-size: 13px; line-height: 1.65; }

.project-form label {
  display: block;
  margin: 0 0 8px;
  color: #474843;
  font-size: 12px;
  font-weight: 700;
}

.project-form input {
  width: 100%;
  height: 44px;
  padding: 0 12px;
  border: 1px solid #c9c5bb;
  border-radius: 5px;
  outline: 0;
  background: var(--surface);
  color: var(--ink);
  font-size: 13px;
  transition: border-color .16s, box-shadow .16s;
}

.project-form input:focus, .composer textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(39,76,119,.11);
}

.field-help { margin: 7px 0 18px; color: var(--ink-muted); font-size: 11px; line-height: 1.45; }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.advanced-fields {
  margin: 3px 0 21px;
  padding: 12px 0 0;
  border-top: 1px solid var(--line);
}

.advanced-fields summary {
  margin-bottom: 14px;
  cursor: pointer;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
}

.primary-button, .send-button, .quiet-button, .text-button, .example-question {
  border: 0;
  cursor: pointer;
}

.primary-button {
  width: 100%;
  height: 46px;
  border-radius: 5px;
  background: var(--accent);
  color: white;
  font-size: 13px;
  font-weight: 720;
  transition: background .16s, transform .16s;
}

.primary-button:hover, .send-button:hover { background: var(--accent-dark); }
.primary-button:active, .send-button:active { transform: translateY(1px); }
.primary-button:disabled, .send-button:disabled { cursor: not-allowed; opacity: .48; }

.connected-project {
  padding: 19px;
  border: 1px solid #c9c5bb;
  border-radius: 6px;
  background: var(--surface);
}

.project-badge { color: var(--success); font-size: 11px; font-weight: 800; letter-spacing: .08em; }
.connected-project h2 { margin: 8px 0 15px; font-size: 17px; overflow-wrap: anywhere; }
.connected-project dl { margin: 0; }
.connected-project dl div { display: grid; grid-template-columns: 48px 1fr; gap: 8px; margin-top: 7px; font-size: 11px; }
.connected-project dt { color: var(--ink-muted); }
.connected-project dd { margin: 0; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; overflow-wrap: anywhere; }
.text-button { margin-top: 17px; padding: 0; background: transparent; color: var(--accent); font-size: 12px; font-weight: 700; }

.privacy-note {
  margin-top: auto;
  padding-top: 28px;
  display: grid;
  gap: 5px;
  color: var(--ink-muted);
  font-size: 11px;
  line-height: 1.5;
}
.privacy-note strong { color: var(--ink); font-size: 12px; }

.chat-panel {
  min-width: 0;
  display: grid;
  grid-template-rows: auto minmax(240px, 1fr) auto auto;
  height: calc(100vh - 110px);
  min-height: 640px;
  background: var(--surface);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 27px 34px 23px;
  border-bottom: 1px solid var(--line);
}
.chat-header h2 { font-size: 23px; }

.quiet-button {
  padding: 9px 13px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: transparent;
  color: var(--ink-muted);
  font-size: 12px;
}
.quiet-button:hover { border-color: #aaa69c; color: var(--ink); }

.messages {
  overflow-y: auto;
  padding: 30px clamp(26px, 5vw, 76px) 24px;
  scroll-behavior: smooth;
}

.message { width: min(840px, 100%); margin: 0 auto 28px; }
.message-label { margin-bottom: 8px; color: var(--ink-muted); font-size: 11px; font-weight: 750; letter-spacing: .06em; }
.message-body { font-size: 15px; line-height: 1.75; white-space: pre-wrap; overflow-wrap: anywhere; }
.message-body p { margin: 0; }
.user-message .message-body {
  margin-left: auto;
  width: fit-content;
  max-width: min(680px, 92%);
  padding: 13px 16px;
  border-radius: 8px 8px 2px 8px;
  background: var(--accent-soft);
  line-height: 1.6;
}
.user-message .message-label { text-align: right; }
.assistant-message:not(.welcome-message) { padding-left: 18px; border-left: 2px solid var(--accent); }
.error-message { padding-left: 18px; border-left: 2px solid var(--danger); }
.error-message .message-label { color: var(--danger); }
.message-meta { margin-top: 10px; color: var(--ink-muted); font-size: 11px; line-height: 1.5; }

.welcome-message { padding-top: clamp(24px, 7vh, 80px); }
.welcome-message .message-body > p { max-width: 620px; font-family: Georgia, "Songti SC", serif; font-size: 22px; line-height: 1.45; }
.example-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 25px; }
.example-question {
  min-height: 90px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #faf9f5;
  text-align: left;
  color: #555650;
  font-size: 12px;
  line-height: 1.55;
  transition: border-color .16s, background .16s;
}
.example-question:hover { border-color: var(--accent); background: var(--surface); color: var(--ink); }

.working {
  width: min(840px, calc(100% - 52px));
  margin: 0 auto 14px;
  padding: 11px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--line);
  border-radius: 5px;
  color: var(--ink-muted);
  font-size: 11px;
}
.working[hidden] { display: none; }
.working-mark {
  width: 12px;
  height: 12px;
  border: 2px solid #bdc7d0;
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin .8s linear infinite;
}
.working time { margin-left: auto; font-variant-numeric: tabular-nums; }
@keyframes spin { to { transform: rotate(360deg); } }

.composer {
  margin: 0 clamp(20px, 5vw, 64px) 28px;
  padding: 13px 14px 10px;
  border: 1px solid #c9c5bb;
  border-radius: 8px;
  background: var(--surface);
  box-shadow: 0 8px 30px rgba(48,45,37,.06);
}
.composer:focus-within { border-color: var(--accent); }
.composer textarea {
  display: block;
  width: 100%;
  max-height: 180px;
  resize: none;
  padding: 4px 2px 9px;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--ink);
  font-size: 14px;
  line-height: 1.55;
}
.composer textarea:disabled { cursor: not-allowed; }
.composer-footer { display: flex; align-items: center; justify-content: space-between; gap: 14px; color: var(--ink-muted); font-size: 10px; }
.send-button { min-width: 72px; height: 34px; border-radius: 5px; background: var(--accent); color: white; font-size: 12px; font-weight: 700; }

.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
[hidden] { display: none !important; }

@media (max-width: 900px) {
  .shell { padding: 0; }
  .topbar { height: 70px; padding: 0 18px; }
  .workspace { min-height: calc(100vh - 70px); grid-template-columns: 1fr; border-left: 0; border-right: 0; }
  .project-panel { border-right: 0; border-bottom: 1px solid var(--line); padding: 25px 20px; }
  .privacy-note { margin-top: 18px; }
  .chat-panel { height: auto; min-height: 700px; }
  .project-panel h1 { font-size: 24px; }
  .example-grid { grid-template-columns: 1fr; }
  .example-question { min-height: 64px; }
}

@media (max-width: 520px) {
  .brand small { display: none; }
  .runtime-status { max-width: 48%; }
  .runtime-status span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .field-row { grid-template-columns: 1fr; }
  .chat-header { padding: 22px 18px; }
  .chat-header h2 { font-size: 20px; }
  .messages { padding: 22px 18px; }
  .composer { margin: 0 14px 18px; }
  .composer-footer > span { display: none; }
  .composer-footer { justify-content: flex-end; }
  .welcome-message { padding-top: 20px; }
  .welcome-message .message-body > p { font-size: 19px; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; animation-duration: .01ms !important; animation-iteration-count: 1 !important; }
}
"""


BROWSER_JS = """(() => {
  'use strict';

  const storageKey = 'swm.browser.project.v1';
  const elements = {
    runtime: document.getElementById('runtime-status'),
    runtimeText: document.getElementById('runtime-status-text'),
    projectForm: document.getElementById('project-form'),
    repositoryPath: document.getElementById('repository-path'),
    revision: document.getElementById('revision'),
    selectedPaths: document.getElementById('selected-paths'),
    comparisonBase: document.getElementById('comparison-base'),
    connectButton: document.getElementById('connect-button'),
    connectedProject: document.getElementById('connected-project'),
    connectedName: document.getElementById('connected-name'),
    connectedRevision: document.getElementById('connected-revision'),
    connectedPaths: document.getElementById('connected-paths'),
    changeProject: document.getElementById('change-project'),
    messages: document.getElementById('messages'),
    chatForm: document.getElementById('chat-form'),
    messageInput: document.getElementById('message-input'),
    sendButton: document.getElementById('send-button'),
    newConversation: document.getElementById('new-conversation'),
    working: document.getElementById('working'),
    workingText: document.getElementById('working-text'),
    workingTime: document.getElementById('working-time')
  };

  const state = {
    project: null,
    modelActive: false,
    busy: false,
    conversationId: makeId(),
    turn: 0,
    history: [],
    timer: null,
    startedAt: 0
  };

  function makeId() {
    if (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function') {
      return globalThis.crypto.randomUUID();
    }
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  }

  async function api(path, body) {
    const response = await fetch(path, {
      method: body === undefined ? 'GET' : 'POST',
      headers: body === undefined ? {} : {'Content-Type': 'application/json'},
      body: body === undefined ? undefined : JSON.stringify(body)
    });
    let payload;
    try {
      payload = await response.json();
    } catch (_) {
      payload = {message: '服务返回了无法识别的内容'};
    }
    if (!response.ok) {
      const error = new Error(payload.message || '请求未完成');
      error.code = payload.error || 'REQUEST_FAILED';
      throw error;
    }
    return payload;
  }

  function friendlyError(error) {
    const messages = {
      LIVE_INTEGRATION_HELD: '真实问答能力尚未启用，请让运行人员使用体验模式启动服务。',
      SOURCE_OPERATION_FAILED: '无法读取这个文件夹。请确认路径存在并且是 Git 项目。',
      SOURCE_TARGET_NOT_FOUND: '找不到指定的 Git 版本，请检查版本名称。',
      SOURCE_TARGET_AMBIGUOUS: '版本标识不够明确，请使用分支、标签或完整提交编号。',
      NO_ACTIVE_STRATEGY: '当前体验环境没有启用问答方案。',
      QUALIFICATION_INVALID: '当前模型能力证明已失效，需要重新验收后再启动。',
      CONTROL_STATE_DENIED: '本轮没有取得足够的源码依据。请缩小读取范围，或把问题描述得更具体后重试。',
      STRUCTURED_OUTPUT_INVALID: '模型返回的分析结果不完整，请换一种更具体的问法后重试。',
      MANAGEMENT_STATE_CONFLICT: '本轮分析状态没有正常完成，请新建对话后重试。',
      INVALID_ARGUMENT: '输入内容不完整或格式不正确，请检查后重试。'
    };
    return messages[error.code] || error.message || '操作没有完成，请稍后重试。';
  }

  async function checkHealth() {
    try {
      const health = await api('/health');
      state.modelActive = Boolean(health.reviewed_answer_preparation_active);
      elements.runtime.classList.toggle('ready', state.modelActive);
      elements.runtime.classList.toggle('blocked', !state.modelActive);
      elements.runtimeText.textContent = state.modelActive ? '问答服务已就绪' : '浏览器已就绪 · 模型未启用';
    } catch (_) {
      state.modelActive = false;
      elements.runtime.classList.add('blocked');
      elements.runtimeText.textContent = '服务连接异常';
    }
    updateComposer();
  }

  function saveProject(project) {
    state.project = project;
    localStorage.setItem(storageKey, JSON.stringify(project));
    showProject();
  }

  function restoreProject() {
    try {
      const value = JSON.parse(localStorage.getItem(storageKey) || 'null');
      if (value && value.scope_id && value.source_id && value.binding_id) {
        state.project = value;
      }
    } catch (_) {
      localStorage.removeItem(storageKey);
    }
    showProject();
  }

  function showProject() {
    const connected = Boolean(state.project);
    elements.projectForm.hidden = connected;
    elements.connectedProject.hidden = !connected;
    if (connected) {
      elements.connectedName.textContent = state.project.display_name;
      const target = state.project.target_parameters;
      elements.connectedRevision.textContent = target.base
        ? `${target.base.slice(0, 9)} → ${target.target.slice(0, 9)}`
        : target.revision.slice(0, 12);
      elements.connectedPaths.textContent = state.project.selected_paths;
    }
    updateComposer();
  }

  function updateComposer() {
    const enabled = Boolean(state.project) && state.modelActive && !state.busy;
    elements.messageInput.disabled = !enabled;
    elements.sendButton.disabled = !enabled || !elements.messageInput.value.trim();
    if (!state.project) {
      elements.messageInput.placeholder = '请先连接一个项目';
    } else if (!state.modelActive) {
      elements.messageInput.placeholder = '项目已连接，真实问答能力尚未启用';
    } else if (state.busy) {
      elements.messageInput.placeholder = '正在分析上一个问题';
    } else {
      elements.messageInput.placeholder = '询问实现流程、异常分支或版本变化';
    }
  }

  function setProjectBusy(busy) {
    elements.connectButton.disabled = busy;
    elements.connectButton.querySelector('span').textContent = busy ? '正在连接…' : '连接项目';
  }

  elements.projectForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    setProjectBusy(true);
    try {
      const payload = await api('/v1/browser/projects', {
        request_id: makeId(),
        repository_path: elements.repositoryPath.value.trim(),
        revision: elements.revision.value.trim(),
        selected_paths: elements.selectedPaths.value.trim(),
        comparison_base: elements.comparisonBase.value.trim() || null
      });
      saveProject(payload.project);
      addMessage('assistant', `已连接“${payload.project.display_name}”。现在可以直接提问。`, '固定版本已确认');
    } catch (error) {
      addMessage('error', friendlyError(error));
    } finally {
      setProjectBusy(false);
    }
  });

  elements.changeProject.addEventListener('click', () => {
    state.project = null;
    localStorage.removeItem(storageKey);
    showProject();
    elements.repositoryPath.focus();
  });

  function addMessage(role, text, meta) {
    const article = document.createElement('article');
    article.className = `message ${role === 'user' ? 'user-message' : role === 'error' ? 'error-message' : 'assistant-message'}`;
    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = role === 'user' ? '你' : role === 'error' ? '未完成' : '项目回答';
    const body = document.createElement('div');
    body.className = 'message-body';
    body.textContent = text;
    article.append(label, body);
    if (meta) {
      const detail = document.createElement('div');
      detail.className = 'message-meta';
      detail.textContent = meta;
      article.append(detail);
    }
    elements.messages.append(article);
    elements.messages.scrollTop = elements.messages.scrollHeight;
  }

  function beginWorking() {
    state.busy = true;
    state.startedAt = Date.now();
    elements.working.hidden = false;
    elements.workingText.textContent = '正在理解问题并查阅项目…';
    updateWorkingTime();
    state.timer = setInterval(updateWorkingTime, 1000);
    updateComposer();
  }

  function updateWorkingTime() {
    const seconds = Math.floor((Date.now() - state.startedAt) / 1000);
    elements.workingTime.textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
    if (seconds >= 20) elements.workingText.textContent = '正在整理依据并复核回答，请稍候…';
  }

  function endWorking() {
    state.busy = false;
    elements.working.hidden = true;
    if (state.timer) clearInterval(state.timer);
    state.timer = null;
    updateComposer();
  }

  async function sendMessage(text) {
    if (!state.project || !state.modelActive || state.busy) return;
    state.turn += 1;
    addMessage('user', text);
    elements.messageInput.value = '';
    resizeComposer();
    beginWorking();
    try {
      const priorHistory = state.history.slice(-6);
      const payload = await api('/v1/browser/chat', {
        request_id: makeId(),
        conversation_id: state.conversationId,
        turn_number: state.turn,
        message: text,
        history: priorHistory,
        project: state.project
      });
      const metaParts = [`已基于固定版本复核 · ${payload.claim_count} 条已确认事实`];
      if (payload.sources && payload.sources.length) {
        metaParts.push(`${payload.sources.length} 处源码位置`);
      }
      if (payload.unresolved_count) {
        metaParts.push(`${payload.unresolved_count} 项尚未确认`);
      }
      const meta = metaParts.join(' · ');
      addMessage('assistant', payload.message, meta);
      state.history.push(
        {role: 'user', content: text},
        {role: 'assistant', content: payload.message}
      );
    } catch (error) {
      addMessage('error', friendlyError(error));
    } finally {
      endWorking();
      elements.messageInput.focus();
    }
  }

  elements.chatForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const text = elements.messageInput.value.trim();
    if (text) sendMessage(text);
  });

  elements.messageInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      elements.chatForm.requestSubmit();
    }
  });

  function resizeComposer() {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = `${Math.min(elements.messageInput.scrollHeight, 180)}px`;
    updateComposer();
  }
  elements.messageInput.addEventListener('input', resizeComposer);

  document.querySelectorAll('.example-question').forEach((button) => {
    button.addEventListener('click', () => {
      if (!state.project || !state.modelActive) {
        elements.repositoryPath.focus();
        return;
      }
      elements.messageInput.value = button.textContent.trim();
      resizeComposer();
      elements.messageInput.focus();
    });
  });

  elements.newConversation.addEventListener('click', () => {
    if (state.busy) return;
    state.conversationId = makeId();
    state.turn = 0;
    state.history = [];
    elements.messages.querySelectorAll('.message:not(.welcome-message)').forEach((item) => item.remove());
    elements.messageInput.focus();
  });

  restoreProject();
  checkHealth();
})();
"""


__all__ = ["BROWSER_CSS", "BROWSER_HTML", "BROWSER_JS"]
