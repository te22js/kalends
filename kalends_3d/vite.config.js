import {defineConfig} from 'vite';
export default defineConfig({base:'/immersion/',build:{target:'es2022',sourcemap:true},server:{proxy:{'/api':'http://127.0.0.1:8790','/navigation.js':'http://127.0.0.1:8790','/immersion-assets':'http://127.0.0.1:8790'}}});
