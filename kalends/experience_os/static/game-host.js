'use strict';
// Compatibility adapter around the shipped 3D client's HTTP bridge. No command
// is repeated, and the original response remains owned by the scene client.
(() => {
  const experience = new URL(location.href).searchParams.get('experience') || 'pompeii_life';
  const nativeFetch = window.fetch.bind(window);
  const notify = message => {if(window.parent !== window)window.parent.postMessage({...message,experience},location.origin);};
  window.fetch = async (input, options) => {
    const gameRequest = typeof input === 'string' && input.startsWith('/api/');
    let operation = null;
    if (gameRequest) {
      const url = new URL(input, location.origin);
      operation = ({'/api/act':'action','/api/observe':'action','/api/move':'move','/api/advance':'advance'})[url.pathname] || null;
      url.searchParams.set('experience', experience);
      input = url.pathname + url.search;
    }
    let response;
    try {response = await nativeFetch(input, options);}
    catch(error) {if(gameRequest&&options?.method==='POST')notify({kind:'kalends:rejected',reason:'network'});throw error;}
    if (gameRequest && options?.method === 'POST' && window.parent !== window) {
      if (response.ok && operation) {
        const message={kind:'kalends:accepted',operation};
        // Only the server can attach this POST's exact meaningful revision.
        // Missing/old metadata still refreshes the UI but cannot claim a choice.
        if(operation==='action')try{const result=await response.clone().json();if(Number.isInteger(result.accepted_revision)&&result.accepted_revision>0)message.accepted_revision=result.accepted_revision;}catch(_){}
        notify(message);
      } else if (!response.ok) {
        let reason='rejected';try{const result=await response.clone().json();if(result.save_failed===true)reason='save_failed';}catch(_){}
        notify({kind:'kalends:rejected',reason});
      }
    }
    return response;
  };
})();
