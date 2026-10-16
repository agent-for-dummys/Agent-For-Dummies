<script setup lang="ts">
import {verdictLabels as labels} from './verdicts';
withDefaults(defineProps<{verdict:string;message?:string;line?:number;showType?:boolean}>(),{showType:true});
</script>
<template><div class="error-feedback" role="status"><p v-if="showType" class="error-type"><strong>错误类型：</strong><span>{{ labels[verdict]||verdict }}</span></p><pre v-if="message" class="error-detail"><span v-if="line">第 {{ line }} 行
</span>{{ message }}</pre></div></template>
<style scoped>
.error-feedback{margin:8px 0 18px;min-width:0}.error-type{font-size:14px;line-height:1.8;margin:0 0 12px;color:var(--vp-c-text-1)}.error-type strong{font-weight:600}.error-type span{color:var(--lab-red);font-weight:500}.error-feedback pre.error-detail{margin:0;padding:13px 15px;border:1px solid color-mix(in srgb,var(--lab-red) 25%,transparent);border-radius:7px;background:var(--lab-red-soft);color:var(--lab-red);font:13px/1.8 var(--vp-font-family-mono);white-space:pre-wrap;overflow-wrap:anywhere;max-width:100%;font-variant-ligatures:none;font-feature-settings:'liga' 0,'calt' 0}
</style>
