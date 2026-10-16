<script setup lang="ts">
import {onUnmounted,ref} from 'vue';
defineProps<{code:string}>();
const copied=ref(false),failed=ref(false);
let timer:ReturnType<typeof setTimeout>|undefined;
async function copy(code:string){
 try{await navigator.clipboard.writeText(code);copied.value=true;failed.value=false;}
 catch{failed.value=true;}
 if(timer)clearTimeout(timer);
 timer=setTimeout(()=>{copied.value=false;failed.value=false;},1600);
}
onUnmounted(()=>{if(timer)clearTimeout(timer);});
</script>
<template>
 <div class="agent-code"><button type="button" class="copy-code" :aria-label="copied?'代码已复制':'复制代码'" @click="copy(code)"><svg viewBox="0 0 20 20" aria-hidden="true"><rect x="7" y="6" width="9" height="11" rx="1.5"/><path d="M12 6V3H3v11h4"/></svg><span>{{copied?'已复制':failed?'复制失败':'复制'}}</span></button><pre><code>{{code}}</code></pre></div>
</template>
