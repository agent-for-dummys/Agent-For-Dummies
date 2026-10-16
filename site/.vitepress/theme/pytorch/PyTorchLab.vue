<script setup lang="ts">
import { KeepAlive, onMounted, ref } from 'vue';
import pytorch from '../../../../oj/course.json';
import CourseWorkspace from './CourseWorkspace.vue';
import AgentWorkspace from './AgentWorkspace.vue';
import { prepareLearningPage } from './editor-runtime';
type Track='pytorch'|'agent';
const track=ref<Track>('pytorch');
onMounted(()=>{
 const requested=new URLSearchParams(location.search).get('course');
 const saved=localStorage.getItem('learning-course');
 track.value=requested==='agent'||requested==='pytorch'?requested:saved==='agent'?'agent':'pytorch';
});
async function switchCourse(next:Track){
 await prepareLearningPage();track.value=next;localStorage.setItem('learning-course',next);
 const url=new URL(location.href);url.searchParams.set('course',next);history.replaceState(history.state,'',url);
}
</script>
<template><KeepAlive><AgentWorkspace v-if="track==='agent'" key="agent" @switch-course="switchCourse"/><CourseWorkspace v-else key="pytorch" track="pytorch" :course="pytorch" @switch-course="switchCourse"/></KeepAlive></template>
