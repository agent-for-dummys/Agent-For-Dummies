<script setup lang="ts">
import {ref} from 'vue';
import DockerWorkspace from './DockerWorkspace.vue';
import FoundationWorkspace from './FoundationWorkspace.vue';
import type {NavigationState} from './course-navigation';
const emit=defineEmits<{navigation:[state:NavigationState]}>();
const selected=ref('docker-build');
const docker=ref<InstanceType<typeof DockerWorkspace>>();
const foundation=ref<InstanceType<typeof FoundationWorkspace>>();
const completions={docker:[] as string[],foundation:[] as string[]};
function update(kind:'docker'|'foundation',state:NavigationState){
 completions[kind]=state.completed;
 if(selected.value.startsWith('docker')===(kind==='docker'))selected.value=state.selected;
 emit('navigation',{selected:selected.value,completed:[...completions.docker,...completions.foundation]});
}
function selectTarget(id:string){
 const workspace=id.startsWith('docker')?docker.value:foundation.value;
 if(!workspace?.selectTarget(id))return false;
 selected.value=id;
 emit('navigation',{selected:id,completed:[...completions.docker,...completions.foundation]});
 return true;
}
defineExpose({selectTarget});
</script>
<template>
 <DockerWorkspace v-show="selected.startsWith('docker')" ref="docker" @navigation="update('docker',$event)"/>
 <FoundationWorkspace v-show="!selected.startsWith('docker')" ref="foundation" @navigation="update('foundation',$event)"/>
</template>
