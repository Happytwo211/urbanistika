(async()=>{
const u=await Auth.me().catch(()=>null);if(!u){location.replace('register.html');return}
await Progress.load().catch(()=>{});
$('av').textContent=u.name[0].toUpperCase();$('un').textContent=u.name;$('ue').textContent=u.email;
$('out').onclick=async()=>{try{await Auth.logout()}catch(e){}location.replace('register.html')};
const q=new URLSearchParams(location.search),mi=MODULES.findIndex(m=>m.id==q.get('m')),M=MODULES[mi];
if(!M||!M.lessons.length){location.replace('cabinet.html');return}
const n=M.lessons.length,i=Math.min(Math.max(+q.get('l')||0,0),n-1),L=M.lessons[i];
const go=k=>location.search=`?m=${encodeURIComponent(M.id)}&l=${k}`;
$('bm').textContent=`Модуль ${mi+1}. ${M.title}`;
$('cnt').textContent=`${i+1}/${n}`;$('lt').textContent=L.title;
$('sg').innerHTML=M.lessons.map((l,k)=>`<a href="?m=${encodeURIComponent(M.id)}&l=${k}" class="${Progress.has(l.id)?'dn':''} ${k==i?'cur':''}" title="${esc(l.title)}">${k==i?'текущий урок':''}</a>`).join('');
L.text.forEach(t=>{const p=document.createElement('p');p.textContent=t;$('tx').append(p)});
$('pv').disabled=i==0;$('pv').onclick=()=>go(i-1);
$('nx').textContent=i<n-1?'Завершить урок и перейти дальше':'Завершить модуль';
$('nx').onclick=async()=>{try{await Progress.mark(L.id)}catch(e){alert('Не удалось сохранить прогресс. Войдите заново.');return}
 if(i<n-1)go(i+1);else location.href='cabinet.html'};
})();
