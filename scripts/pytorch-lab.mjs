export function pytorchLab(md) {
  md.block.ruler.before('fence','pytorch_lab',(state,start,end,silent)=>{
    const line=state.src.slice(state.bMarks[start]+state.tShift[start],state.eMarks[start]);
    if(line.trim()!=='::: pytorch-lab' || start+1>=end)return false;
    const close=state.src.slice(state.bMarks[start+1]+state.tShift[start+1],state.eMarks[start+1]);
    if(close.trim()!==':::')return false;
    if(silent)return true;
    const token=state.push('pytorch_lab','',0);token.block=true;token.map=[start,start+2];state.line=start+2;return true;
  },{alt:['paragraph','reference','blockquote','list']});
  md.renderer.rules.pytorch_lab=()=>'<PyTorchLab />\n';
}
