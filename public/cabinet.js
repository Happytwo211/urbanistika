(async()=>{
const u=await Auth.me().catch(()=>null);if(!u){location.replace('register.html');return}
await Progress.load().catch(()=>{});
$('av').textContent=u.name[0].toUpperCase();$('un').textContent=u.name;$('ue').textContent=u.email;
$('out').onclick=async()=>{try{await Auth.logout()}catch(e){}location.replace('register.html')};
const done=m=>m.lessons.filter(l=>Progress.has(l.id)).length;
const L=MODULES.reduce((a,m)=>a+m.lessons.length,0),D=MODULES.reduce((a,m)=>a+done(m),0),C=MODULES.filter(m=>m.lessons.length&&done(m)==m.lessons.length).length;
const mi=MODULES.findIndex(m=>m.lessons.length&&done(m)<m.lessons.length);
const href=m=>`module.html?m=${encodeURIComponent(m.id)}&l=${Math.max(m.lessons.findIndex(l=>!Progress.has(l.id)),0)}`;
if(mi<0){$('nx').textContent=D?'Все доступные модули пройдены — новые скоро':'Материалы скоро появятся'}
else{$('nx').textContent=`${D?'Продолжите':'Начните'} с модуля ${mi+1}: ${MODULES[mi].title}`;
 $('go').hidden=false;$('go').textContent=D?'Продолжить обучение':'Начать обучение';$('go').onclick=()=>location.href=href(MODULES[mi])}
$('st').innerHTML=`<div><b>${C}/${MODULES.length}</b>Модулей пройдено</div><div><b>${L-D}</b>Уроков осталось</div><div><b>${L?Math.round(D/L*100):0}%</b>Прогресс прохождения</div>`;
$('ml').innerHTML=MODULES.map((m,k)=>{const n=m.lessons.length,d=done(m),p=n?Math.round(d/n*100):0;
 if(!n)return `<article class="m soon"><span class="n">${k+1}</span><div><h3>${esc(m.title)}</h3><p>Материалы скоро появятся</p></div><div></div><span class="bd">Скоро</span></article>`;
 const s=p==100?['dn','Пройден']:p?['pr','В процессе']:['','Не начат'];
 return `<article class="m" data-h="${esc(href(m))}"><span class="n">${k+1}</span><div><h3>${esc(m.title)}</h3><p>${d} из ${n} уроков</p></div><div><div class="bar"><i data-w="${p}"></i></div></div><span class="bd ${s[0]}">${s[1]}</span></article>`}).join('');
document.querySelectorAll('.bar i').forEach(i=>i.style.width=i.dataset.w+'%');
$('ml').onclick=e=>{const a=e.target.closest('.m[data-h]');if(a)location.href=a.dataset.h};
})();
