export function pythonValue(value:any,depth=0):string {
 const pad=' '.repeat(depth),child=' '.repeat(depth+4);
 if(value&&typeof value==='object'&&!Array.isArray(value)&&Array.isArray(value.shape)&&'dtype' in value&&'data' in value){
  if(value.shape[0]===0&&value.shape.length>1)return `tensor([], size=(${value.shape.join(', ')}), dtype=torch.${value.dtype})`;
  const data=pythonValue(value.data,depth);
  return `tensor(${data}, dtype=torch.${value.dtype})`+(value.truncated?`\n${pad}# shape=${JSON.stringify(value.shape)}，仅显示前 20 个元素`:'');
 }
 if(Array.isArray(value)){
  const items=value.map(v=>pythonValue(v,depth+4));
  const inline='['+items.join(', ')+']';
  if(inline.length+depth<=76&&!inline.includes('\n'))return inline;
  return '[\n'+items.map(v=>child+v).join(',\n')+'\n'+pad+']';
 }
 if(value&&typeof value==='object'){
  const items=Object.entries(value).map(([key,item])=>JSON.stringify(key)+': '+pythonValue(item,depth+4));
  const inline='{'+items.join(', ')+'}';
  if(inline.length+depth<=76&&!inline.includes('\n'))return inline;
  return '{\n'+items.map(item=>child+item).join(',\n')+'\n'+pad+'}';
 }
 if(value===null)return 'None';if(value===true)return 'True';if(value===false)return 'False';
 if(typeof value==='number')return Number.isInteger(value)?String(value):String(Number(value.toPrecision(7)));
 return typeof value==='string'?JSON.stringify(value):String(value);
}
export function inputText(input:unknown,p:{parameters:{name:string}[]}){const args=input as unknown[];return p.parameters.map((param,i)=>`${param.name} = ${pythonValue(args[i])}`).join('\n');}
export function outputText(value:unknown,p:{outputNames?:string[]}){
 if(p.outputNames&&Array.isArray(value)&&value.length===p.outputNames.length)return p.outputNames.map((name,i)=>`${name} = ${pythonValue(value[i])}`).join('\n');
 return pythonValue(value);
}
