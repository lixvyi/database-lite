const osButton = document.querySelector('#os-nav');

osButton.onclick = async () => {
  document.querySelectorAll('.nav').forEach(button => button.classList.toggle('active', button === osButton));
  document.querySelector('#title').textContent = 'OS 存储仿真台';
  document.querySelector('#subtitle').textContent = '观察页目录、内存缓存、WAL 屏障与检查点';
  document.querySelector('#primary').style.display = 'none';
  document.querySelector('#content').innerHTML = '<p>正在读取仿真状态…</p>';
  await renderOS();
};

async function renderOS() {
  try {
    document.querySelector('#primary').style.display = 'none';
    const data = await api('/api/os/status');
    const stats = data.stats;
    const cached = new Set(data.frames.map(frame => frame.page_id));
    const metrics = [
      ['缓存策略', stats.policy],
      ['命中率', (stats.hit_rate * 100).toFixed(1) + '%'],
      ['脏页', stats.dirty],
      ['磁盘读取', stats.disk_reads],
      ['WAL LSN', stats.wal_durable_lsn],
      ['Checkpoint', stats.checkpoint_lsn],
    ];
    const pages = data.pages.map(page => `<div title="Page ${page.page_id} · offset ${page.offset}" class="page-cell ${page.allocated ? 'used' : ''} ${cached.has(page.page_id) ? 'cached' : ''}">${page.page_id}</div>`).join('');
    const frames = data.frames.map(frame => `<tr><td>${frame.page_id}</td><td>${frame.generation}</td><td>${frame.dirty ? '是' : '否'}</td><td>${frame.pin_count}</td><td>${frame.page_lsn}</td></tr>`);
    const events = data.events.length ? data.events.map(event => `${event.event.padEnd(6)} page=${event.page_id}${event.lsn ? ' lsn=' + event.lsn : ''}`).join('\n') : '尚无事件';
    document.querySelector('#content').innerHTML = `<div class="os-shell">
      <div class="os-metrics">${metrics.map(item => `<div class="os-metric"><small>${item[0]}</small><b>${item[1]}</b></div>`).join('')}</div>
      <section class="os-panel">
        <div class="section-head"><h3>页目录 · ${stats.allocated_pages}/${stats.total_pages} 已分配</h3><div class="os-actions">
          <button class="secondary" data-os="allocate">分配页</button><button class="secondary" data-os="write">修改内存页</button><button class="primary" data-os="checkpoint">Checkpoint</button>
        </div></div>
        <div class="page-map">${pages}</div><h3>Buffer Frames</h3>${table(['Page', 'Generation', 'Dirty', 'Pin', 'Page LSN'], frames)}
        <p class="os-note">深色表示已分配页，朱红外框表示当前驻留内存。数据文件偏移 = page_id × 4096。</p>
      </section>
      <section class="os-panel"><h3>缓存事件</h3><pre class="event-log">${events}</pre></section>
    </div>`;
    document.querySelector('#primary').style.display = 'none';
    document.querySelectorAll('[data-os]').forEach(button => button.onclick = () => osAction(button.dataset.os, data));
  } catch (error) {
    document.querySelector('#content').innerHTML = `<p class="error">${esc(error.message)}</p>`;
  }
}

async function osAction(action, state) {
  const body = { action };
  if (action === 'write') {
    const used = state.pages.find(page => page.allocated);
    if (!used) {
      await api('/api/os/action', { method: 'POST', body: JSON.stringify({ action: 'allocate' }) });
      return osAction('write', await api('/api/os/status'));
    }
    body.page_id = used.page_id;
    body.text = 'memory update ' + new Date().toISOString();
  }
  try {
    const data = await api('/api/os/action', { method: 'POST', body: JSON.stringify(body) });
    toast('操作完成');
    await renderOS();
  } catch (error) { toast(error.message); }
}

document.querySelectorAll('.nav:not(#os-nav):not(#lab-nav)').forEach(button => button.addEventListener('click', () => document.querySelector('#primary').style.display = ''));
if (new URLSearchParams(location.search).has('os')) setTimeout(() => osButton.click(), 180);
