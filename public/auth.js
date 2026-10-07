// Клиент API сервера. Сессия живёт в HttpOnly-cookie (JS её не видит), для изменяющих запросов нужен CSRF-токен.
const Auth={
  csrf:'',user:null,
  async api(path,opt={}){
    const post=!!opt.body;
    const r=await fetch('/api/'+path,{method:post?'POST':'GET',credentials:'same-origin',
      headers:{'Content-Type':'application/json','X-CSRF-Token':this.csrf},body:post?JSON.stringify(opt.body):undefined});
    let d={};try{d=await r.json()}catch(e){}
    if(!r.ok)throw Object.assign(new Error(d.error||'Ошибка сервера'),{status:r.status,fields:d.fields});
    return d;
  },
  async _set(d){this.csrf=d.csrf;this.user=d.user;return d.user},
  async me(){try{return await this._set(await this.api('me'))}catch(e){if(e.status==401)return null;throw e}},
  async register(f){return this._set(await this.api('register',{body:f}))},
  async login(f){return this._set(await this.api('login',{body:f}))},
  async logout(){await this.api('logout',{body:{}});this.user=null}
};
