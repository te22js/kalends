'use strict';
// Compatibility adapter around the unchanged, shipped 3D client's HTTP bridge.
// An explicit iframe URL identifies its compiled life; no cookie/global active
// world can switch another tab's commands to a different journal.
(() => {
  const experience = new URL(location.href).searchParams.get('experience') || 'pompeii_life';
  const nativeFetch = window.fetch.bind(window);
  window.fetch = async (input, options) => {
    const gameRequest = typeof input === 'string' && input.startsWith('/api/');
    let acceptedOperation = false;
    if (gameRequest) {
      const url = new URL(input, location.origin);
      acceptedOperation = ['/api/act', '/api/move', '/api/advance'].includes(url.pathname);
      url.searchParams.set('experience', experience);
      input = url.pathname + url.search;
    }
    const response = await nativeFetch(input, options);
    if (gameRequest && acceptedOperation && response.ok && options?.method === 'POST' && window.parent !== window) {
      window.parent.postMessage({kind: 'kalends:accepted', experience}, location.origin);
    }
    return response;
  };
})();
