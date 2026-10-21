/* Records the actual WebGL canvas. HTML HUD/dialogue are outside this track. */
export function recordScene(canvas,{seconds=20,onStatus=()=>{}}={}){
  if(!canvas.captureStream||!globalThis.MediaRecorder)throw Error('Canvas recording is unavailable in this browser. Screenshots remain available.');
  const type=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm'].find(t=>MediaRecorder.isTypeSupported(t));if(!type)throw Error('This browser cannot encode a WebM scene capture.');
  const stream=canvas.captureStream(30),recorder=new MediaRecorder(stream,{mimeType:type,videoBitsPerSecond:5_000_000}),chunks=[];
  recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
  const done=new Promise((resolve,reject)=>{recorder.onerror=e=>{stream.getTracks().forEach(t=>t.stop());reject(e.error||Error('Scene recording failed.'));};recorder.onstop=()=>{stream.getTracks().forEach(t=>t.stop());const blob=new Blob(chunks,{type}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='kalends-immersion-scene.webm';link.click();setTimeout(()=>URL.revokeObjectURL(url),2000);onStatus('Scene capture downloaded. It contains the 3D scene; HTML dialogue is outside the video.');resolve({bytes:blob.size,mime:type,seconds});};});
  recorder.start(1000);onStatus('Recording '+seconds+' seconds of the actual 3D scene…');setTimeout(()=>{if(recorder.state==='recording')recorder.stop();},seconds*1000);return done;
}
