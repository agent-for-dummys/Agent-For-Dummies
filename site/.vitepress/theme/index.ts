import DefaultTheme from 'vitepress/theme';
import Layout from './Layout.vue';
import AlgorithmWalkthrough from './algorithms/AlgorithmWalkthrough.vue';
import type { Theme } from 'vitepress';
import { defineAsyncComponent } from 'vue';
import './style.css';
import './pytorch/fonts.css';
import { prepareLearningPage } from './pytorch/editor-runtime';

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app, router }) {
    app.component('AlgorithmWalkthrough', AlgorithmWalkthrough);
    const loadLab = () => import('./pytorch/PyTorchLab.vue');
    app.component('PyTorchLab', defineAsyncComponent(loadLab));
    if (!import.meta.env.SSR) {
      const previous = router.onBeforePageLoad;
      let navigation = 0;
      router.onBeforePageLoad = async href => {
        const current = ++navigation;
        if (await previous?.(href) === false) return false;
        if (/\/(?:pytorch|practice)(?:\.html)?(?:[?#]|$)/.test(href)) await Promise.all([loadLab(), prepareLearningPage()]);
        if (current !== navigation) return false;
      };
    }
  }
} satisfies Theme;
