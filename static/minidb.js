const labButton=document.querySelector('#lab-nav');
const samples={
  query:`SELECT name, age FROM student
WHERE age >= 17
ORDER BY age DESC, name ASC;`,
  update:`UPDATE student
SET age = age + 1
WHERE id = 2;`,
  catalog:`SELECT table_name, column_name, first_page
FROM pg_catalog
ORDER BY table_name, column_name;`
};
let labResult=null,stage='tokens';

labButton.onclick=()=>{
  document.querySelectorAll('.nav').forEach(button=>button.classList.toggle('active',button===labButton));
  document.querySelector('#title').textContent='MiniDB 实验台';
  document.querySelector('#subtitle').textContent='从 SQL 到物理页，逐阶段观察自研数据库内核';
  document.querySelector('#primary').style.display='none';
  document.querySelector('#content').innerHTML=`<div class="lab-shell"><section class="sql-pane"><div class="pane-title"><h3>SQL 输入</h3><select id="sql-sample" aria-label="选择 SQL 示例"><option value="query">排序查询</option><option value="update">更新数据</option><option value="catalog">查询系统目录</option></select></div><textarea id="sql-editor" spellcheck="false">${samples.query}</textarea><div class="lab-actions"><button class="primary" id="inspect-sql">编译并检查</button><button class="secondary" id="execute-sql">执行 SQL</button></div></section><section class="pipeline-pane"><div class="buffer-bar" id="buffer-bar">尚未运行 · 页 0 为系统目录</div><div class="stage-tabs">${[['tokens','Token'],['ast','AST'],['semantic','语义'],['plan_before','原计划'],['plan_after','优化后'],['result','执行结果'],['system','页与目录']].map(item=>`<button class="stage-tab ${item[0]===stage?'active':''}" data-stage="${item[0]}">${item[1]}</button>`).join('')}</div><pre id="stage-output">点击“编译并检查”，查看 SQL → Token → AST → Semantic → Plan → Optimize 全链路。</pre></section></div>`;
  document.querySelector('#sql-sample').onchange=event=>{document.querySelector('#sql-editor').value=samples[event.target.value]};
  document.querySelector('#inspect-sql').onclick=()=>runLab('inspect');
  document.querySelector('#execute-sql').onclick=()=>runLab('execute');
  document.querySelectorAll('.stage-tab').forEach(button=>button.onclick=()=>{stage=button.dataset.stage;renderStage()});
};

document.querySelectorAll('.nav:not(#lab-nav):not(#os-nav)').forEach(button=>button.addEventListener('click',()=>document.querySelector('#primary').style.display=''));

async function runLab(mode){
  const out=document.querySelector('#stage-output'),buttons=[...document.querySelectorAll('.lab-actions button')];
  out.textContent='正在处理…';out.classList.remove('lab-error');buttons.forEach(button=>button.disabled=true);
  try{
    const response=await api('/api/minidb/'+mode,{method:'POST',body:JSON.stringify({sql:document.querySelector('#sql-editor').value})});
    labResult=response;stage=mode==='execute'?'result':'tokens';renderStage();
    const stats=response.buffer;
    document.querySelector('#buffer-bar').innerHTML=`页 <b>${stats.allocated_pages}</b>　命中率 <b>${(stats.hit_rate*100).toFixed(1)}%</b>　磁盘读 <b>${stats.disk_reads}</b>　磁盘写 <b>${stats.disk_writes}</b>　检查点 <b>${stats.checkpoint_lsn}</b>`;
  }catch(error){out.textContent=error.message;out.classList.add('lab-error')}
  finally{buttons.forEach(button=>button.disabled=false)}
}

function renderStage(){
  document.querySelectorAll('.stage-tab').forEach(button=>button.classList.toggle('active',button.dataset.stage===stage));
  if(!labResult)return;
  let value;
  if(stage==='result')value=labResult.result;
  else if(stage==='system')value=labResult.system;
  else{const last=labResult.result[labResult.result.length-1]||{};value=last[stage]}
  document.querySelector('#stage-output').textContent=typeof value==='string'?value:JSON.stringify(value,null,2);
}

if(new URLSearchParams(location.search).has('lab'))setTimeout(()=>labButton.click(),150);
