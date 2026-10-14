(() => {
  'use strict';
  const { marked, DOMPurify, mermaid, losslessParse, losslessStringify } = window.docVendor;
  const snapshot = losslessParse(document.getElementById('doc-data').textContent);
  marked.setOptions({ gfm: true, breaks: true });
  marked.use({ renderer: { html() { return ''; } } });
  mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'neutral' });
  const docs = snapshot.documents;
  const names = { raw: '原始需求', spec: '需求分析', plan: '详细设计', api: '接口设计', data: '数据结构设计', task: '任务清单', implement: '实现记录' };
  const labels = { timestamp: '时间', timeSource: '时间来源', inputType: '输入类型', questionContext: '问题上下文', timezone: '时区', entries: '输入记录', terms: '业务术语', meaning: '含义', scope: '适用范围', aliases: '别名', goals: '需求目标', included: '包含范围', excluded: '排除范围', rules: '核心规则', scenarios: '场景', mainFlow: '主要流程', stateTransitions: '状态变化', steps: '处理步骤', exceptions: '异常与边界', acceptance: '验收标准', trigger: '触发条件', summary: '说明', modules: '模块', methods: '方法', implementation: '实现方案', policies: '事务、并发与异常', codeChanges: '代码变更', interfaces: '接口', requestParams: '请求参数', responseFields: '返回字段', requestExample: '请求示例', responseExample: '返回示例', permissions: '权限', errors: '错误行为', relationships: '关系', tables: '表', fields: '字段', indexes: '索引', redis: 'Redis', messages: '消息', otherStructures: '其他结构', migrationNotes: '迁移说明', tasks: '任务', dependsOn: '前置任务', locations: '实现位置', completionCriteria: '完成标准', taskResults: '任务结果', verifications: '实际验证', remaining: '未完成项', command: '命令', result: '结果', source: '来源', sourceRefs: '出处', scenarioRefs: '关联场景', interfaceRefs: '关联接口', dataRefs: '关联数据', designRefs: '设计依据', taskRefs: '关联任务', evidenceRefs: '验证依据', status: '状态', title: '标题', goal: '目标', objective: '实现目标', text: '原文', diagram: '流程图', kind: '类型', dataType: '数据类型', nullable: '可空', default: '默认值', constraints: '约束', purpose: '用途', expected: '预期结果', precondition: '前置条件', action: '操作', condition: '条件', from: '原状态', to: '目标状态', allowed: '允许', recordedAt: '记录时间', authorizedScope: '授权范围', conclusion: '整体结论', change: '变更', role: '职责', responsibility: '职责', signature: '签名', entryPoint: '实现入口', verificationPlan: '计划验证方式', description: '说明', notes: '说明' };
  Object.assign(labels, { overallFlow: '整体流程', overallDiagram: '整体流程图', acceptanceRefs: '验收依据', scenarioRef: '需求场景', taskRef: '任务', acceptanceRef: '验收项', skill: '技能', name: '名称', method: '方法', path: '路径', dataType: '数据类型', required: '必填', location: '位置', default: '默认值', status: '状态', type: '类型', change: '变更', parameters: '参数', returns: '返回', sharedBehavior: '共用方法行为', transaction: '事务', transactions: '事务', concurrency: '并发', idempotency: '幂等', externalFailures: '外部调用失败', requestParams: '请求参数', responseFields: '返回字段', inputType: '输入类型' });
  const text = s => String(s ?? '');
  const esc = s => text(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const safe = html => DOMPurify.sanitize(html, { USE_PROFILES: { html: true }, FORBID_TAGS: ['style', 'script', 'iframe', 'form'], FORBID_ATTR: ['style'] });
  const md = s => safe(marked.parse(text(s)));
  const normalize = p => { const stack = []; for (const part of p.split('/')) { if (part === '..') stack.pop(); else if (part && part !== '.') stack.push(part); } return stack.join('/'); };
  const index = new Map();
  const docMap = new Map(docs.map(d => [d.path, d]));
  const key = (path, id) => path + '#' + id;
  function isRef(node) { return node && typeof node === 'object' && 'path' in node && 'id' in node && Object.keys(node).every(k => ['path','id','locator','url'].includes(k)); }
  function collect(node, path) { if (Array.isArray(node)) node.forEach(v => collect(v, path)); else if (node && typeof node === 'object') { if (isRef(node)) return; if (typeof node.id === 'string') index.set(key(path, node.id), 'entity-' + path.replace(/[^a-zA-Z0-9]/g, '-') + '-' + node.id.replace(/[^a-zA-Z0-9]/g, '-')); Object.values(node).forEach(v => collect(v, path)); } }
  docs.forEach(d => collect(d.data, d.path));
  function refHtml(ref, current) { const base = current.split('/').slice(0, -1).join('/'); const path = normalize(base + '/' + ref.path); const anchor = index.get(key(path, ref.id)); const detail = ref.locator ? ` · ${esc(ref.locator)}` : ''; const external = typeof ref.url === 'string' && /^https?:\/\//i.test(ref.url) ? ` · <a href="${esc(ref.url)}" target="_blank" rel="noopener noreferrer">原始链接</a>` : ''; return (anchor ? `<a href="#${esc(anchor)}">${esc(ref.id)}</a>` : `<span class="muted">${esc(ref.id)}</span>`) + detail + external; }
  function code(s) { return `<div class="code-wrap"><button class="copy" type="button">复制</button><pre><code>${esc(s)}</code></pre></div>`; }
  function value(v, current, field) {
    if (v === null) return '<span class="muted">null</span>';
    if (typeof v === 'boolean') return v ? '是' : '否';
    if (typeof v === 'string') return field === 'text' && docMap.get(current)?.data.documentType === 'raw' ? `<pre class="raw-text">${esc(v)}</pre>` : field.toLowerCase().endsWith('diagram') ? `<div class="mermaid-src">${code(v)}</div>` : ['text', 'summary', 'meaning', 'scope', 'purpose', 'description', 'goal', 'objective', 'implementation', 'overallFlow', 'trigger', 'condition', 'expected', 'action', 'precondition', 'notes', 'role', 'responsibility', 'constraints', 'permissions', 'migrationNotes', 'verificationPlan'].includes(field) ? md(v) : esc(v);
    if (Array.isArray(v)) return v.length ? '<ol>' + v.map(x => '<li>' + value(x, current, field) + '</li>').join('') + '</ol>' : '<span class="empty">无</span>';
    if (v && typeof v === 'object') {
      if (isRef(v)) return refHtml(v, current);
      if (field.endsWith('Example')) return code(losslessStringify(v, null, 2));
      if (typeof v.id === 'string') return entry(v, current, field);
      return '<dl class="kv">' + Object.entries(v).map(([k, x]) => `<dt>${esc(labels[k] || k)}</dt><dd>${value(x, current, k)}</dd>`).join('') + '</dl>';
    }
    return esc(v);
  }
  function entry(obj, current, field, depth = 0) {
    if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
      const anchor = obj.id ? index.get(key(current, obj.id)) : '';
      const title = obj.name || obj.title || obj.id || labels[field] || field;
      const badge = obj.status || obj.result;
      let html = `<article class="entry" ${anchor ? `id="${esc(anchor)}"` : ''} data-status="${esc(obj.status || '')}"><h3>${esc(obj.id && title !== obj.id ? obj.id + ' · ' + title : title)}${badge ? `<span class="badge ${esc(badge)}">${esc(badge)}</span>` : ''}</h3>`;
      for (const [k, v] of Object.entries(obj)) {
        if (['id', 'name', 'title', 'status', 'result', 'schemaVersion', 'documentType', 'requirementId', '$schema'].includes(k)) continue;
        if (k === 'attachments') { html += `<h4>附件</h4><ul>${v.map(a => { const base = current.split('/').slice(0,-1).join('/'); const target = normalize(base + '/' + a.path); const href = target.split('/').map(encodeURIComponent).join('/'); return `<li><a href="${esc(href)}">${esc(a.path)}</a> · ${esc(a.source)}</li>`; }).join('')}</ul>`; continue; }
        if (k === 'sourceRefs' || k.endsWith('Refs') || k === 'scenarioRef' || k === 'taskRef' || k === 'acceptanceRef') { html += `<p class="refs">${esc(labels[k] || k)}：${value(v, current, k)}</p>`; continue; }
        if (Array.isArray(v) && v.some(x => x && typeof x === 'object' && 'id' in x) && depth < 3) { html += `<details open><summary>${esc(labels[k] || k)}（${v.length}）</summary>${v.map(x => entry(x, current, k, depth + 1)).join('')}</details>`; continue; }
        html += `<div class="property"><h4>${esc(labels[k] || k)}</h4>${value(v, current, k)}</div>`;
      }
      return html + '</article>';
    }
    return value(obj, current, field);
  }
  const root = document.getElementById('content');
  const id = docs[0]?.data.requirementId || '需求文档';
  const sha = docs.map(d => d.path + ' ' + d.sha256.slice(0, 12)).join('\n');
  document.getElementById('meta').textContent = `${id}\n生成于 ${snapshot.generatedAt}\n源文件摘要：\n${sha}\n这是生成时快照；JSON 更新后需重新渲染。`;
  document.getElementById('meta').style.whiteSpace = 'pre-wrap';
  function overview(d) {
    const x = d.data, p = d.path;
    const link = v => index.get(key(p,v.id)) ? `<a href="#${esc(index.get(key(p,v.id)))}">${esc(v.id)}</a>` : esc(v.id);
    const table = (head, rows) => `<div class="overview"><h3>总览</h3><table><thead><tr>${head.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(cell=>`<td>${cell}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
    if (x.documentType === 'spec') return table(['场景编号','名称','说明'], (x.scenarios||[]).map(v=>[link(v),esc(v.name),esc(v.summary)]));
    if (x.documentType === 'plan') return table(['场景','实现入口','接口','数据'], (x.scenarios||[]).map(v=>[refHtml(v.scenarioRef,p),esc(v.entryPoint||''),value(v.interfaceRefs||[],p,'interfaceRefs'),value(v.dataRefs||[],p,'dataRefs')]));
    if (x.documentType === 'api') return table(['接口','方法','路径','用途'], (x.interfaces||[]).map(v=>[link(v),esc(v.method),code(v.path),esc(v.purpose)]));
    if (x.documentType === 'task') return table(['任务','目标','场景','依赖','状态'], (x.tasks||[]).map(v=>[link(v),esc(v.goal),value(v.scenarioRefs||[],p,'scenarioRefs'),esc((v.dependsOn||[]).join(', ')||'无'),`<span class="badge ${esc(v.status)}">${esc(v.status)}</span>`]));
    if (x.documentType === 'implement') return table(['验证项','命令','结果'], (x.verifications||[]).map(v=>[link(v),code(v.command),`<span class="badge ${esc(v.result)}">${esc(v.result)}</span>`]));
    return '';
  }
  root.innerHTML = `<header><h1>${esc(id)}</h1><p>结构化需求文档 · ${esc(snapshot.generatedAt)}</p></header>` + docs.map(d => {
    const kind = d.data.documentType;
    const sectionId = 'doc-' + kind;
    const sections = Object.entries(d.data).filter(([k]) => !['$schema','schemaVersion','documentType','requirementId','title'].includes(k));
    return `<section class="document" id="${sectionId}"><h2>${esc(names[kind] || d.data.title)}</h2>${overview(d)}${sections.map(([k,v]) => `<div class="chapter"><h3>${esc(labels[k] || k)}</h3>${Array.isArray(v) && v.some(x => x && typeof x === 'object' && 'id' in x) ? v.map(x => entry(x,d.path,k)).join('') : value(v,d.path,k)}</div>`).join('')}</section>`;
  }).join('');
  document.getElementById('nav').innerHTML = docs.map(d => `<a href="#doc-${esc(d.data.documentType)}">${esc(names[d.data.documentType] || d.data.title)}</a>`).join('');
  root.addEventListener('click', e => { if (e.target.classList.contains('copy')) { navigator.clipboard?.writeText(e.target.nextElementSibling.textContent); e.target.textContent = '已复制'; setTimeout(() => e.target.textContent = '复制', 1300); } });
  function filter() { const q = document.getElementById('search').value.trim().toLowerCase(), status = document.getElementById('status-filter').value; document.querySelectorAll('.entry').forEach(el => { const match = (!q || el.textContent.toLowerCase().includes(q)) && (status === 'all' || !el.dataset.status || el.dataset.status === status); el.classList.toggle('hidden', !match); }); }
  document.getElementById('search').addEventListener('input', filter);
  document.getElementById('status-filter').addEventListener('change', filter);
  async function diagrams() { let n = 0; for (const node of document.querySelectorAll('.mermaid-src')) { const source = node.textContent.replace(/^复制/, '').trim(); try { const result = await mermaid.render('diagram-' + (++n), source); node.innerHTML = DOMPurify.sanitize(result.svg, { USE_PROFILES: { svg: true, svgFilters: true } }); } catch (_) { node.insertAdjacentHTML('afterbegin', '<p class="diagram-error">图表渲染失败，以下为原始图表代码：</p>'); } } }
  diagrams();
})();
