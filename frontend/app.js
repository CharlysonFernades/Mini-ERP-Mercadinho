'use strict';

const paths = {
  store:'<path d="m3 10 2-6h14l2 6M4 13v7h16v-7M9 20v-6h6v6"/><path d="M3 10v1a3 3 0 0 0 6 0v-1m0 1a3 3 0 0 0 6 0v-1m0 1a3 3 0 0 0 6 0v-1"/>',
  dashboard:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  package:'<path d="m12 3 9 5v9l-9 5-9-5V8zM3 8l9 5 9-5M12 13v9M7.5 5.5l9 5"/>',
  arrows:'<path d="M3 7h17m-4-4 4 4-4 4M21 17H4m4 4-4-4 4-4"/>',
  chart:'<path d="M4 3v17h17M8 15v-4m5 4V6m5 9V9"/>',
  wallet:'<path d="M20 8V5a2 2 0 0 0-2-2H6a3 3 0 0 0 0 6h14v11H6a3 3 0 0 1-3-3V6"/><path d="M20 12h-5v5h5M16 14.5h.1"/>',
  alert:'<path d="m10.3 4-8 14a2 2 0 0 0 1.7 3h16a2 2 0 0 0 1.7-3l-8-14a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4m0 4h.01"/>',
  sale:'<path d="M3 3h2l3 12h11l3-9H6M9 20h.01M18 20h.01"/><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
  refresh:'<path d="M20 7a8 8 0 0 0-14-1L3 9m0-6v6h6M4 17a8 8 0 0 0 14 1l3-3m0 6v-6h-6"/>',
  'arrow-right':'<path d="M4 12h16m-6-6 6 6-6 6"/>',
  'arrow-up-right':'<path d="M7 17 17 7M7 7h10v10"/>',
  'arrow-down-left':'<path d="M17 7 7 17M7 7v10h10"/>',
  'chevron-down':'<path d="m6 9 6 6 6-6"/>',
  'chevron-right':'<path d="m9 6 6 6-6 6"/>',
  'chevron-left':'<path d="m15 6-6 6 6 6"/>',
  shield:'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6"/>',
  check:'<path d="m5 12 4 4L19 6"/>',
  close:'<path d="m6 6 12 12M6 18 18 6"/>',
  edit:'<path d="m16 3 5 5-12 12-6 1 1-6zM13 6l5 5"/>',
  history:'<path d="M3 11a9 9 0 1 1 3 8M3 4v7h7m2-4v5l3 2"/>',
  trophy:'<path d="M8 3h8v7a4 4 0 0 1-8 0zM8 5H4v3a4 4 0 0 0 4 4m8-7h4v3a4 4 0 0 1-4 4M12 14v6m-4 1h8"/>',
  trash:'<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>'
};
const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.package}</svg>`;
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const titleCase = value => String(value).replace(/(^|\s)\S/g, char => char.toLocaleUpperCase('pt-BR'));
const fold = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const money = value => new Intl.NumberFormat('pt-BR', {style:'currency',currency:'BRL'}).format(value);
const number = value => new Intl.NumberFormat('pt-BR').format(value);
const dateLabel = iso => new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR', {day:'numeric',month:'long',year:'numeric'});
const labels = {overview:'Visão geral',products:'Produtos e estoque',movements:'Movimentações',reports:'Relatórios'};
const statusLabels = {normal:'Em estoque',low:'Estoque baixo',critical:'Crítico'};
const main = document.querySelector('#main');
const dialog = document.querySelector('#form-dialog');
let state = null;
let currentView = 'overview';
let filters = {query:'', status:'all', operation:'all', date:'', page:1};
let formContext = null;
let saving = false;
let loading = false;
let toastTimer;

function hydrateIcons(root=document) {
  root.querySelectorAll('[data-icon]').forEach(element => { element.innerHTML = icon(element.dataset.icon); });
}
hydrateIcons();

function productTile(name) {
  const index = [...name].reduce((sum, letter) => sum + letter.charCodeAt(0), 0) % 4;
  const initials = name.split(' ').slice(0, 2).map(word => word[0]).join('').toUpperCase();
  return `<span class="product-tile tone-${index}" aria-hidden="true">${escapeHTML(initials)}</span>`;
}
function productCell(name,status) {
  return `<div class="product-cell">${productTile(name)}<div><strong>${escapeHTML(titleCase(name))}</strong>${status?`<span class="mobile-status">${pill(status)}</span>`:''}</div></div>`;
}
function pill(status) { return `<span class="pill ${status}">${statusLabels[status]}</span>`; }
function empty(title, description, action='', symbol='package') {
  return `<div class="empty-state">${icon(symbol)}<h3>${title}</h3><p>${description}</p>${action}</div>`;
}
function heading(title, description, actions=true) {
  return `<div class="page-heading"><div><div class="eyebrow">MEU MERCADINHO</div><h1>${title}</h1><p class="heading-description">${description}</p></div>${actions ? `<div class="heading-actions"><button class="button" data-action="movement">${icon('arrows')}Registrar movimento</button><button class="button primary" data-action="create">${icon('plus')}Novo produto</button></div>` : ''}</div>`;
}
function metrics(report=false) {
  const s = state.summary;
  return `<div class="metrics">
    <article class="metric featured"><div class="metric-head"><span class="metric-label">Valor em estoque</span><span class="metric-icon">${icon('wallet')}</span></div><div class="metric-value">${money(s.value)}</div><p class="metric-note">${report ? 'Quantidade × preço unitário' : 'Valor dos produtos disponíveis'}</p></article>
    <article class="metric"><div class="metric-head"><span class="metric-label">Produtos cadastrados</span><span class="metric-icon">${icon('package')}</span></div><div class="metric-value">${number(s.products).padStart(2,'0')}</div><p class="metric-note"><strong>${number(s.units)} unidades</strong> em estoque</p></article>
    <article class="metric warning"><div class="metric-head"><span class="metric-label">Precisam de atenção</span><span class="metric-icon">${icon('alert')}</span></div><div class="metric-value">${number(s.low+s.critical).padStart(2,'0')}</div><p class="metric-note"><strong>${s.critical} críticos</strong> · ${s.low} com estoque baixo</p></article>
    <article class="metric sky"><div class="metric-head"><span class="metric-label">${report ? 'Valor médio por produto' : 'Unidades vendidas hoje'}</span><span class="metric-icon">${icon(report ? 'chart' : 'sale')}</span></div><div class="metric-value">${report ? money(s.average) : number(s.todayOut).padStart(2,'0')}</div><p class="metric-note">${report ? 'Valor em estoque ÷ produtos' : `${number(s.todayIn)} unidades recebidas hoje`}</p></article>
  </div>`;
}
function movementChart() {
  const max = Math.max(10, ...state.week.flatMap(day => [day.in, day.out]));
  const scale = Math.ceil(max / 10) * 10;
  const total = state.week.reduce((sum, day) => sum + day.out, 0);
  return `<section class="panel"><div class="panel-head"><div><h2>Movimentação do estoque</h2><p class="panel-subtitle">Últimos 7 dias</p></div><div class="legend"><span><i class="entry"></i>Entradas</span><span><i></i>Vendas</span></div></div><div class="chart-wrap"><div class="chart-summary"><strong>${number(total)}</strong>unidades vendidas no período</div><div class="chart" role="img" aria-label="Entradas e vendas por dia: ${state.week.map(day => `${dateLabel(day.date)}: ${day.in} entradas e ${day.out} vendas`).join('; ')}"><div class="chart-axis"><span>${scale}</span><span>${Math.round(scale/2)}</span><span>0</span></div><div class="chart-plot">${state.week.map(day => `<div class="bar-day ${day.date===state.today?'today':''}" title="${dateLabel(day.date)} · Entradas: ${day.in} · Vendas: ${day.out}"><div class="bars"><span class="bar entry" style="height:${day.in / scale * 100}%"></span><span class="bar" style="height:${day.out / scale * 100}%"></span></div><span class="day-label">${day.date===state.today?'Hoje':new Date(`${day.date}T12:00:00`).toLocaleDateString('pt-BR',{weekday:'short'}).replace('.','')}</span></div>`).join('')}</div></div><div class="chart-caption"><span>Quantidade em unidades</span><span>${dateLabel(state.week[0].date).split(' de ')[0]} – ${dateLabel(state.today)}</span></div></div></section>`;
}
function alerts() {
  const items = state.products.filter(product => product.status !== 'normal').sort((a,b)=> a.quantity / a.minimum - b.quantity / b.minimum);
  return `<section class="panel"><div class="panel-head"><div class="alert-heading">${icon('alert')}<h2>Hora de repor</h2></div><span class="alert-count">${items.length}</span></div><div class="alert-list">${items.slice(0,3).map(product => `<div class="alert-item">${productTile(product.name)}<div class="product-info"><strong>${escapeHTML(titleCase(product.name))}</strong><small><span class="stock-amount">${product.quantity} un.</span> disponíveis · mín. ${product.minimum}</small></div><button class="icon-button" data-action="restock" data-name="${escapeHTML(product.name)}" aria-label="Repor ${escapeHTML(titleCase(product.name))}" title="Repor estoque">${icon('plus')}</button></div>`).join('')}</div>${items.length ? `<div class="panel-link"><button class="text-button" data-action="alerts">Ver produtos em atenção ${icon('arrow-right')}</button></div>` : `<div class="empty-alert">${icon('check')}<p>${state.products.length ? 'Tudo em dia por aqui.' : 'Os alertas aparecerão aqui.'}</p></div>`}</section>`;
}
function tableControls() {
  return `<div class="table-tools"><label class="search-field">${icon('search')}<input id="product-search" type="search" placeholder="Buscar produto…" aria-label="Buscar produto" value="${escapeHTML(filters.query)}" autocomplete="off"></label><select id="status-filter" class="filter-select" aria-label="Filtrar situação do estoque"><option value="all">Todas as situações</option><option value="normal" ${filters.status==='normal'?'selected':''}>Em estoque</option><option value="low" ${filters.status==='low'?'selected':''}>Estoque baixo</option><option value="critical" ${filters.status==='critical'?'selected':''}>Crítico</option><option value="attention" ${filters.status==='attention'?'selected':''}>Precisam de atenção</option></select></div>`;
}
function filteredProducts() {
  return state.products.filter(product => fold(product.name).includes(fold(filters.query)) && (filters.status==='all' || (filters.status==='attention' ? product.status!=='normal' : product.status===filters.status)));
}
function productRows(items) {
  return items.map(product => `<tr><td>${productCell(product.name,product.status)}</td><td><span class="stock-number">${number(product.quantity)}</span><span class="unit-label">un.</span><div class="minimum-label">mín. ${number(product.minimum)}</div></td><td class="price desktop-column">${money(product.price)}</td><td class="value desktop-column">${money(product.value)}</td><td>${pill(product.status)}</td><td><div class="row-actions"><button class="icon-button" data-action="restock" data-name="${escapeHTML(product.name)}" title="Repor estoque" aria-label="Repor ${escapeHTML(titleCase(product.name))}">${icon('plus')}</button><button class="icon-button" data-action="edit" data-name="${escapeHTML(product.name)}" title="Editar produto" aria-label="Editar ${escapeHTML(titleCase(product.name))}">${icon('edit')}</button></div></td></tr>`).join('');
}
function productTableContent(limit=0) {
  const items = filteredProducts();
  const visible = limit ? items.slice(0,limit) : items;
  if(!state.products.length) return empty('Seu estoque começa aqui','Cadastre seu primeiro produto para acompanhar as quantidades e receber alertas de reposição.','<button class="button primary" data-action="create">'+icon('plus')+'Cadastrar primeiro produto</button>');
  if(!items.length) return empty('Nenhum produto encontrado','Tente outro nome ou altere o filtro.','<button class="button small" data-action="clear-filters">Limpar filtros</button>','search');
  return `<div class="table-scroll"><table class="stock-table"><caption class="sr-only">Produtos, quantidades, preços e situação do estoque</caption><thead><tr><th scope="col">Produto</th><th scope="col">Estoque atual</th><th scope="col" class="desktop-column">Preço unitário</th><th scope="col" class="desktop-column">Valor em estoque</th><th scope="col">Situação</th><th scope="col"><span class="sr-only">Ações</span></th></tr></thead><tbody>${productRows(visible)}</tbody></table></div><div class="table-footer"><span>Mostrando ${visible.length} de ${items.length} produtos</span>${limit ? '<a href="#products" class="text-button">Ver estoque completo '+icon('arrow-right')+'</a>' : '<span>Quantidades em unidades</span>'}</div>`;
}
function stockPanel(overview=false) {
  return `<section class="panel"><div class="stock-section-head"><div class="title-with-count"><h2>${overview?'Seu estoque':'Todos os produtos'}</h2><span class="count-chip">${state.products.length}</span></div>${tableControls()}</div><div id="product-table-content">${productTableContent(overview?5:0)}</div></section>`;
}
function overview() {
  return heading('Visão geral','Tudo o que você precisa acompanhar, em um só lugar.')+`<div class="date-label">${icon('calendar')}${titleCase(new Date(`${state.today}T12:00:00`).toLocaleDateString('pt-BR',{weekday:'long'}))}, ${dateLabel(state.today)}</div>`+metrics()+`<div class="overview-grid">${movementChart()}${alerts()}</div>`+stockPanel(true);
}
function productsPage() {
  return heading('Produtos e estoque','Cadastre, ajuste e acompanhe cada produto do seu mercadinho.')+stockPanel();
}
function historyItems() {
  return state.history.filter(item => fold(item.Produto).includes(fold(filters.query)) && (filters.operation==='all' || (filters.operation==='entries' ? ['Compra','Cadastro'].includes(item.Operação) : filters.operation==='adjustments' ? ['Ajuste','Exclusão'].includes(item.Operação) : item.Operação===filters.operation)) && (!filters.date || item.Data.split('/').reverse().join('-')===filters.date));
}
function historyContent() {
  const items = historyItems();
  const pages = Math.max(1, Math.ceil(items.length/12));
  filters.page = Math.min(filters.page, pages);
  const start = (filters.page-1)*12;
  const visible = items.slice(start,start+12);
  if(!items.length) return empty('Nenhuma movimentação por aqui',state.history.length?'Ajuste os filtros para encontrar os registros.':'Compras, vendas e cadastros aparecerão aqui assim que forem registrados.','','history');
  return `<div class="table-scroll"><table class="history-table"><caption class="sr-only">Histórico de movimentações</caption><thead><tr><th scope="col">Data e hora</th><th scope="col">Produto</th><th scope="col">Operação</th><th scope="col">Quantidade</th></tr></thead><tbody>${visible.map(item => {const entry=['Compra','Cadastro'].includes(item.Operação);const adjustment=['Ajuste','Exclusão'].includes(item.Operação);return `<tr><td class="movement-date">${item.Data}<small>${item.Hora}</small></td><td>${productCell(item.Produto)}</td><td><span class="operation"><span class="operation-icon ${entry?'entry':adjustment?'adjust':''}">${icon(entry?'arrow-down-left':adjustment?'edit':'arrow-up-right')}</span>${escapeHTML(item.Operação)}</span>${item.Anterior && item.Atual ? `<small class="adjust-detail">Preço: ${money(item.Anterior['Preço Unitário'])} → ${money(item.Atual['Preço Unitário'])}<br>Mínimo: ${escapeHTML(item.Anterior['Estoque Minimo'])} → ${escapeHTML(item.Atual['Estoque Minimo'])}</small>`:''}</td><td><strong>${entry?'+':item.Operação==='Venda'?'−':item.Quantidade>0?'+':''}${number(item.Quantidade)}</strong> <span class="unit-label">un.</span></td></tr>`;}).join('')}</tbody></table></div><div class="table-footer"><span>${start+1}–${start+visible.length} de ${number(items.length)} movimentações</span><div class="pagination"><button class="icon-button" data-action="previous-page" aria-label="Página anterior" ${filters.page===1?'disabled':''}>${icon('chevron-left')}</button><span>${filters.page} / ${pages}</span><button class="icon-button" data-action="next-page" aria-label="Próxima página" ${filters.page===pages?'disabled':''}>${icon('chevron-right')}</button></div></div>`;
}
function movementsPage() {
  return heading('Movimentações','Um histórico de cada entrada, venda e ajuste do seu estoque.')+`<section class="panel"><div class="stock-section-head"><div class="title-with-count"><h2>Histórico do mercadinho</h2><span class="count-chip">${number(state.history.length)}</span></div><div class="table-tools"><label class="search-field">${icon('search')}<input id="history-search" type="search" placeholder="Buscar produto…" aria-label="Buscar produto no histórico" value="${escapeHTML(filters.query)}"></label><input type="date" class="filter-select" id="history-date" aria-label="Filtrar data das movimentações" value="${filters.date}"></div></div><div class="tabs" role="group" aria-label="Tipo de movimentação">${[['all','Todas'],['entries','Entradas'],['Venda','Vendas'],['adjustments','Ajustes']].map(([value,label])=>`<button class="tab ${filters.operation===value?'active':''}" data-action="history-tab" data-value="${value}" aria-pressed="${filters.operation===value}">${label}</button>`).join('')}</div><div id="history-content">${historyContent()}</div></section>`;
}
function ranking(kind,title,description) {
  const items=state.rankings[kind];
  const max=items[0]?.quantity||1;
  return `<section class="panel"><div class="panel-head"><div><h2>${title}</h2><p class="panel-subtitle">${description}</p></div>${icon('trophy')}</div><div class="report-body">${items.length?items.map((item,index)=>`<div class="ranking-row"><span class="ranking-number">${index+1}</span><div><span class="ranking-name">${escapeHTML(titleCase(item.name))}</span><div class="ranking-bar-track"><div class="ranking-bar" style="width:${item.quantity/max*100}%"></div></div></div><span class="ranking-units">${number(item.quantity)} <span class="unit-label">un.</span></span></div>`).join(''):empty('Ranking em construção','Registre movimentações para ver os destaques.','','chart')}</div></section>`;
}
function health() {
  const s=state.summary;const a=s.products?s.normal/s.products*100:0;const b=s.products?(s.normal+s.low)/s.products*100:0;
  return `<section class="panel"><div class="panel-head"><div><h2>Situação do estoque</h2><p class="panel-subtitle">Distribuição dos produtos cadastrados</p></div></div><div class="health-wrap"><div class="donut" style="background:${s.products?`conic-gradient(#137653 0% ${a}%,#e8b65c ${a}% ${b}%,#d7766b ${b}% 100%)`:'#e8edea'}" role="img" aria-label="${s.normal} produtos em estoque normal, ${s.low} com estoque baixo e ${s.critical} críticos"><div class="donut-inner"><strong>${s.products}</strong><small>produtos</small></div></div><div class="health-legend"><div class="health-row"><i></i>Em estoque<b>${s.normal}</b></div><div class="health-row low"><i></i>Estoque baixo<b>${s.low}</b></div><div class="health-row critical"><i></i>Crítico<b>${s.critical}</b></div></div></div><div class="note-box">Crítico: abaixo do mínimo. Estoque baixo: do mínimo até menos de 1,4× o mínimo. Em estoque: a partir de 1,4× o mínimo.</div></section>`;
}
function reportsPage() {
  return heading('Relatórios','Entenda seu estoque e descubra os produtos mais movimentados.',false)+metrics(true)+`<div class="report-grid">${ranking('sales','Produtos mais vendidos','Ranking por unidades · todo o histórico')}${ranking('purchases','Produtos mais recebidos','Compras e cadastros · todo o histórico')}</div><div class="report-grid">${health()}${movementChart()}</div><p class="report-note">O valor em estoque usa o preço unitário atual. O histórico original não registra o preço de cada venda, por isso este painel não calcula faturamento ou lucro.</p>`;
}
function render() {
  if(!state) return;
  const views={overview,products:productsPage,movements:movementsPage,reports:reportsPage};
  document.title=`${labels[currentView]} · Mercadinho ERP`;
  document.querySelector('#breadcrumb-page').textContent=labels[currentView];
  document.querySelectorAll('[data-nav],[data-mobile-nav]').forEach(link=>{
    const selected=(link.dataset.nav||link.dataset.mobileNav)===currentView;
    link.classList.toggle('active',selected);
    if(selected)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');
  });
  document.querySelector('#demo-badge').hidden=!state.demo;
  document.querySelector('#sync-label').textContent=`Atualizado às ${new Date(state.updatedAt).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}`;
  main.innerHTML=views[currentView]();
}
function route() {
  const view=location.hash.slice(1);
  currentView=Object.hasOwn(labels,view)?view:'overview';
  filters={query:'',status:'all',operation:'all',date:'',page:1};
  render();
  window.scrollTo({top:0,behavior:'instant'});
}
async function loadState(notify=false) {
  if(loading)return;
  loading=true;
  try{
    const response=await fetch('/api/state',{cache:'no-store'});
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||'Não foi possível carregar os dados.');
    state=data;render();
    if(notify)toast('Estoque atualizado.');
  }catch(error){
    if(state){toast(error.message,true);document.querySelector('#sync-label').textContent='Sem atualização · confira a conexão';}
    else main.innerHTML=`<div class="connection-error">${empty('Não foi possível abrir o estoque',escapeHTML(error.message),'<button class="button primary" data-action="refresh">Tentar novamente</button>','alert')}</div>`;
  }finally{loading=false;}
}
function toast(message,error=false) {
  clearTimeout(toastTimer);
  const element=document.querySelector('#toast');
  element.innerHTML=icon(error?'alert':'check')+`<span>${escapeHTML(message)}</span>`;
  element.classList.toggle('error',error);element.hidden=false;
  toastTimer=setTimeout(()=>{element.hidden=true;},4500);
}
function modalFrame(title,description,body) {
  dialog.innerHTML=`<div class="dialog-head"><div><div class="dialog-kicker">MERCADINHO ERP</div><h2 id="dialog-title">${title}</h2><p>${description}</p></div><button class="icon-button" type="button" data-action="close-dialog" aria-label="Fechar janela">${icon('close')}</button></div><form class="dialog-form" id="erp-form">${body}<p class="form-error" id="form-error" role="alert" hidden></p><div class="dialog-actions"><button type="button" class="button" data-action="close-dialog">Cancelar</button><button type="submit" class="button primary" id="save-button">${icon('check')}<span>Salvar</span></button></div></form>`;
  if(!dialog.open)dialog.showModal();
  dialog.querySelector('input:not(:disabled),select')?.focus();
}
function openProduct(name) {
  const product=state.products.find(p=>p.name===name);
  formContext={type:product?'edit':'create',product};
  modalFrame(product?'Editar produto':'Novo produto',product?'Atualize as informações e os limites de estoque.':'Mais um produto, tudo sob controle.',`
    <div class="form-field"><label for="product-name">Nome do produto</label><input id="product-name" name="name" maxlength="80" minlength="2" required placeholder="Ex.: Arroz branco" value="${escapeHTML(product?.name?titleCase(product.name):'')}" ${product?'disabled':''} autocomplete="off"><small>Use apenas letras e espaços.</small></div>
    <div class="form-grid"><div class="form-field"><label for="product-quantity">${product?'Quantidade atual':'Quantidade inicial'}</label><input id="product-quantity" name="quantity" type="number" inputmode="numeric" min="${product?0:1}" max="1000000" step="1" required placeholder="0" value="${product?.quantity??''}"></div><div class="form-field"><label for="product-price">Preço unitário (R$)</label><input id="product-price" name="price" type="number" inputmode="decimal" min="0.01" max="1000000" step="0.01" required placeholder="0,00" value="${product?.price??''}"></div></div>
    <div class="form-field"><label for="product-minimum">Estoque mínimo</label><input id="product-minimum" name="minimum" type="number" inputmode="numeric" min="1" max="1000000" step="1" required placeholder="Ex.: 10" value="${product?.minimum??''}"><small>O painel avisa quando o produto precisa de reposição.</small></div>
    ${product?`<div class="form-info">${icon('history')}As alterações ficam registradas no histórico.</div>${product.quantity===0?'<button type="button" class="delete-button" data-action="confirm-delete">Excluir produto sem estoque</button><div class="delete-confirm" id="delete-confirm" hidden><p>Excluir este produto? O histórico será mantido.</p><button type="button" class="button danger small" data-action="delete-product">Confirmar exclusão</button></div>':''}`:''}
  `);
  document.querySelector('#save-button span').textContent=product?'Salvar alterações':'Cadastrar produto';
}
function openMovement(name='',operation='Venda') {
  if(!state.products.length){openProduct();toast('Cadastre um produto para registrar movimentações.');return;}
  formContext={type:'movement',operation};
  modalFrame('Registrar movimento','Entradas e vendas atualizam seu estoque na hora.',`
    <div class="dialog-movement-tabs" role="group" aria-label="Tipo de movimento"><button type="button" class="${operation==='Venda'?'active':''}" data-action="movement-type" data-value="Venda" aria-pressed="${operation==='Venda'}">${icon('arrow-up-right')}Venda</button><button type="button" class="${operation==='Compra'?'active':''}" data-action="movement-type" data-value="Compra" aria-pressed="${operation==='Compra'}">${icon('arrow-down-left')}Entrada / compra</button></div>
    <div class="form-field"><label for="movement-product">Produto</label><select id="movement-product" name="name" required><option value="">Selecione um produto</option>${state.products.map(product=>`<option value="${escapeHTML(product.name)}" ${product.name===name?'selected':''}>${escapeHTML(titleCase(product.name))} · ${product.quantity} un.</option>`).join('')}</select></div>
    <div class="form-field"><label for="movement-quantity">Quantidade de unidades</label><input id="movement-quantity" name="quantity" type="number" inputmode="numeric" min="1" max="1000000" step="1" required placeholder="Ex.: 5"></div>
    <div class="form-info" id="movement-preview"><span>Estoque após o movimento</span><strong>Selecione um produto</strong></div>
  `);
  updateMovementPreview();
}
function updateMovementPreview() {
  if(formContext?.type!=='movement')return;
  const product=state.products.find(p=>p.name===document.querySelector('#movement-product').value);
  const input=document.querySelector('#movement-quantity');
  const amount=Number(input.value)||0;
  const out=formContext.operation==='Venda';
  const remaining=product?product.quantity+(out?-amount:amount):0;
  const preview=document.querySelector('#movement-preview');
  preview.classList.toggle('invalid',Boolean(product&&remaining<0));
  preview.innerHTML=product?`<span>Estoque atual: ${number(product.quantity)} un.</span><strong>${remaining<0?'Estoque insuficiente':`${number(remaining)} un. após ${out?'a venda':'a entrada'}`}</strong>`:'<span>Estoque após o movimento</span><strong>Selecione um produto</strong>';
  input.max=product&&out?product.quantity:1000000;
  document.querySelector('#save-button span').textContent=out?'Registrar venda':'Registrar entrada';
}
async function submitForm(event) {
  event.preventDefault();
  if(saving)return;
  const fields=new FormData(event.target);
  let endpoint;let data;let message;
  if(formContext.type==='movement'){
    endpoint='/api/movements';data={name:fields.get('name'),quantity:Number(fields.get('quantity')),operation:formContext.operation};
    message=formContext.operation==='Venda'?'Venda registrada e estoque atualizado.':'Entrada registrada e estoque atualizado.';
  }else{
    const product=formContext.product;
    endpoint=product?'/api/products/update':'/api/products';
    data={name:product?.name||fields.get('name'),quantity:Number(fields.get('quantity')),price:Number(fields.get('price')),minimum:Number(fields.get('minimum'))};
    if(product)data.expected={'Qtde':product.quantity,'Preço Unitário':product.price,'Estoque Minimo':product.minimum};
    message=product?'Produto atualizado.':'Produto cadastrado com sucesso.';
  }
  await save(endpoint,data,message);
}
async function save(endpoint,data,message) {
  if(saving)return;
  saving=true;
  const buttons=[...dialog.querySelectorAll('button')];
  buttons.forEach(button=>{button.disabled=true;});
  const errorBox=document.querySelector('#form-error');errorBox.hidden=true;
  try{
    const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-ERP-Token':state.csrf},body:JSON.stringify(data)});
    const result=await response.json();
    if(!response.ok)throw new Error(result.error||'Não foi possível salvar.');
    state=result;dialog.close();render();toast(message);
  }catch(error){errorBox.textContent=error instanceof TypeError?'A conexão falhou. Feche esta janela e atualize o estoque para conferir se o movimento foi salvo antes de repetir.':error.message;errorBox.hidden=false;errorBox.scrollIntoView({block:'nearest'});}
  finally{saving=false;buttons.forEach(button=>{button.disabled=false;});}
}
function renderHistoryOnly(){document.querySelector('#history-content').innerHTML=historyContent();}
document.addEventListener('click',event=>{
  if(event.target.closest('.skip-link')){event.preventDefault();main.focus();return;}
  const button=event.target.closest('[data-action]');if(!button||button.disabled)return;
  const action=button.dataset.action;
  if(action==='close-dialog'){if(!saving)dialog.close();return;}
  if(action==='refresh'){loadState(true);return;}
  if(!state)return;
  if(action==='create')openProduct();
  if(action==='edit')openProduct(button.dataset.name);
  if(action==='movement')openMovement();
  if(action==='restock')openMovement(button.dataset.name,'Compra');
  if(action==='alerts'){
    currentView='products';filters={query:'',status:'attention',operation:'all',date:'',page:1};
    history.pushState(null,'','#products');render();window.scrollTo({top:0,behavior:'instant'});
  }
  if(action==='clear-filters'){filters.query='';filters.status='all';render();}
  if(action==='history-tab'){
    filters.operation=button.dataset.value;filters.page=1;
    document.querySelectorAll('[data-action="history-tab"]').forEach(tab=>{tab.classList.toggle('active',tab===button);tab.setAttribute('aria-pressed',String(tab===button));});renderHistoryOnly();
  }
  if(action==='next-page'){filters.page++;renderHistoryOnly();}
  if(action==='previous-page'){filters.page--;renderHistoryOnly();}
  if(action==='movement-type'){
    formContext.operation=button.dataset.value;
    document.querySelectorAll('[data-action="movement-type"]').forEach(tab=>{tab.classList.toggle('active',tab===button);tab.setAttribute('aria-pressed',String(tab===button));});updateMovementPreview();
  }
  if(action==='confirm-delete')document.querySelector('#delete-confirm').hidden=false;
  if(action==='delete-product'&&formContext?.product)save('/api/products/delete',{name:formContext.product.name},'Produto excluído. O histórico foi mantido.');
});
document.addEventListener('input',event=>{
  if(event.target.id==='product-search'){filters.query=event.target.value;document.querySelector('#product-table-content').innerHTML=productTableContent(currentView==='overview'?5:0);}
  if(event.target.id==='history-search'){filters.query=event.target.value;filters.page=1;renderHistoryOnly();}
  if(event.target.id==='movement-quantity')updateMovementPreview();
});
document.addEventListener('change',event=>{
  if(event.target.id==='status-filter'){filters.status=event.target.value;document.querySelector('#product-table-content').innerHTML=productTableContent(currentView==='overview'?5:0);}
  if(event.target.id==='history-date'){filters.date=event.target.value;filters.page=1;renderHistoryOnly();}
  if(event.target.id==='movement-product')updateMovementPreview();
});
dialog.addEventListener('submit',submitForm);
dialog.addEventListener('cancel',event=>{if(saving)event.preventDefault();});
dialog.addEventListener('click',event=>{if(event.target===dialog&&!saving){const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)dialog.close();}});
window.addEventListener('hashchange',route);
window.addEventListener('popstate',route);
route();loadState();
