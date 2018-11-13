import Vue from 'vue';
import Router from 'vue-router';
import Ping from '@/components/Ping';
import Songs from '@/components/Songs';

Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Songs',
      component: Songs,
    },
    {
      path: '/ping',
      name: 'Ping',
      component: Ping,
    },
  ],
  mode: 'hash',
});
