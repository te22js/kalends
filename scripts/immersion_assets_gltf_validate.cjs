'use strict';
// Run the official Khronos schema/buffer validator without uploading assets.
// npm install --prefix /tmp/kalends-gltf-validator --ignore-scripts gltf-validator
// KALENDS_GLTF_VALIDATOR=/tmp/kalends-gltf-validator/node_modules/gltf-validator node scripts/immersion_assets_gltf_validate.cjs
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),validator=require(process.env.KALENDS_GLTF_VALIDATOR||'gltf-validator');
(async()=>{
 const environment=process.argv.includes('--environment');
 const files=environment?['environment/pompeii_district.glb']:['characters/roman_female.glb','characters/roman_male.glb','foliage/pine.glb','foliage/broadleaf.glb','foliage/shrub.glb'];const results=[];
 for(const file of files){
  const asset=fs.readFileSync(path.join(root,'kalends_3d/assets',file));
  const report=await validator.validateBytes(new Uint8Array(asset),{uri:file,maxIssues:300,externalResourceFunction:uri=>Promise.reject(new Error('Runtime GLBs must be self-contained: '+uri))});
  results.push({file,sha256:crypto.createHash('sha256').update(asset).digest('hex'),report});
 }
 const result={schema:'kalends-khronos-validation-v1',validator:validator.version(),package:'gltf-validator',source:'https://github.com/KhronosGroup/glTF-Validator',local_only:true,files:results,scope:'Official glTF2 schema/accessor/image/skin/animation checks; does not measure browser visual quality or performance.'};
 fs.writeFileSync(path.join(root,'kalends_3d/assets/characters',environment?'environment_khronos_validation.json':'khronos_validation.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(results.map(({file,report})=>({file,...Object.fromEntries(Object.entries(report.issues).filter(([k])=>k!=='messages')),issues:report.issues.messages.slice(0,5)})),null,2));
 if(results.some(r=>r.report.issues.numErrors>0))process.exitCode=1;
})().catch(error=>{console.error(error);process.exitCode=1;});
