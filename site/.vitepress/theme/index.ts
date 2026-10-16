import DefaultTheme from 'vitepress/theme';
import Layout from './Layout.vue';
import AlgorithmWalkthrough from './algorithms/AlgorithmWalkthrough.vue';
import type { Theme } from 'vitepress';
import './style.css';

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('AlgorithmWalkthrough', AlgorithmWalkthrough);
  }
} satisfies Theme;
