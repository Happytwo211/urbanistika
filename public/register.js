(async()=>{
if(await Auth.me().catch(()=>null)){location.replace('cabinet.html');return}
const reg=$('reg'),log=$('log');
const tab=n=>{reg.hidden=n!='reg';log.hidden=n!='log';document.querySelectorAll('.tabs button').forEach(b=>b.classList.toggle('on',b.dataset.t==n))};
document.querySelectorAll('[data-t]').forEach(b=>b.onclick=()=>tab(b.dataset.t));
if(location.hash=='#login')tab('log');
document.querySelectorAll('.eye').forEach(b=>b.onclick=()=>{const i=b.previousElementSibling;i.type=i.type=='password'?'text':'password'});
const show=(f,k,m)=>f.querySelector(`[name=${k}]`).closest('.f').querySelector('.e').textContent=m||'';
const busy=(f,v)=>f.querySelector('.btn').disabled=v;
reg.onsubmit=async e=>{
  e.preventDefault();
  const d=Object.fromEntries(new FormData(reg));
  const c={
    name:d.name.trim().length<2?'Введите имя':'',
    email:/^\S+@\S+\.\S+$/.test(d.email)?'':'Введите корректный email',
    city:d.city.trim()?'':'Укажите город и район',
    password:/^(?=.*[A-Za-zА-Яа-я])(?=.*\d).{8,}$/.test(d.password)?'':'Минимум 8 символов, буква и цифра',
    password2:d.password===d.password2?'':'Пароли не совпадают'};
  Object.keys(c).forEach(k=>show(reg,k,c[k]));
  if(Object.values(c).some(Boolean)||!d.ok)return;
  busy(reg,true);
  try{await Auth.register({name:d.name.trim(),email:d.email.trim(),city:d.city.trim(),password:d.password});location.href='cabinet.html'}
  catch(x){const f=x.fields||{};Object.keys(f).forEach(k=>show(reg,k,f[k]));if(!Object.keys(f).length)show(reg,'password2',x.message);busy(reg,false)}
};
log.onsubmit=async e=>{
  e.preventDefault();
  const d=Object.fromEntries(new FormData(log));
  show(log,'password','');busy(log,true);
  try{await Auth.login({email:d.email.trim(),password:d.password});location.href='cabinet.html'}
  catch(x){show(log,'password',x.message);busy(log,false)}
};
})();
