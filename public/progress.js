// Прогресс хранится на сервере (таблица progress).
const Progress={
  done:new Set(),
  async load(){this.done=new Set((await Auth.api('progress')).done)},
  has(id){return this.done.has(id)},
  async mark(id){await Auth.api('progress',{body:{lesson:id}});this.done.add(id)}
};
