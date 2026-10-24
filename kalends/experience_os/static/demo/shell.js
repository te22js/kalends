'use strict';
window.KALENDS_DEMO = true;
// Presentation only. demo_server.py independently rejects every operator route.
const demoBlocked = 'a[href="/research"],a[href="/about"],a[href^="/research/"],a[href^="/lab/"],a[href^="/studio"],a[href$="/reflect"],a[href="/history-rebirth"],#menu-lab,[data-practice],[data-story-tab="reflect"],[data-bookmark],#diagnostics,.telemetry-choice:has(#telemetry-opt-in),.telemetry-choice:has(#telemetry-opt-in)+p';
function applyDemoShell() {
  document.querySelectorAll(demoBlocked).forEach(node => {
    if (!node.hidden) node.hidden = true;
    if ('disabled' in node) node.disabled = true;
  });
  const saving=document.querySelector('#world-saving');
  if(saving?.textContent==='Saved locally')saving.textContent='Saved in this demo';
  const save = document.querySelector('#save-note');
  if (save && save.textContent !== 'Accepted actions are saved in this temporary demo.') save.textContent = 'Accepted actions are saved in this temporary demo.';
}
document.addEventListener('click', event => {
  if(event.target.closest?.(demoBlocked)){event.preventDefault();event.stopImmediatePropagation();}
}, true);
new MutationObserver(applyDemoShell).observe(document.documentElement,{childList:true,subtree:true});
applyDemoShell();
if (window.top === window.self) {
  const banner=document.createElement('aside');banner.className='demo-banner';
  banner.textContent='Private temporary demo · Shared demo saves · No personal information, please.';
  document.body.prepend(banner);
}
