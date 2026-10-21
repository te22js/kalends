"""Package selected free Quaternius nature meshes as lightweight GLBs.

Preserves original geometry, UVs and leaf-card artwork. Bark is a simple PBR
material instead of shipping the unused 4K bark diffuse/normal maps. Leaves are
opaque-cutout/double-sided as supplied. Does not assign botanical authenticity.
"""
from pathlib import Path
import argparse,copy,hashlib,json,struct,zipfile
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'kalends_3d/assets/foliage'

def write_glb(path,doc,blob):
 raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);blob=bytes(blob)+b'\0'*((-len(blob))%4)
 path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob)

def package(z,name,file):
 raw=z.read('glTF/'+name+'.gltf');doc=json.loads(raw);blob=bytearray(z.read('glTF/'+doc['buffers'][0]['uri']));oldtextures=copy.deepcopy(doc.get('textures',[]));oldimages=copy.deepcopy(doc.get('images',[]));clamped=0;max_excess=0;seen=set()
 for mesh in doc['meshes']:
  for prim in mesh['primitives']:
   index=prim['attributes'].get('COLOR_0')
   if index is None or index in seen:continue
   seen.add(index);accessor=doc['accessors'][index];assert accessor['componentType']==5126;view=doc['bufferViews'][accessor['bufferView']];components=4 if accessor['type']=='VEC4' else 3;stride=view.get('byteStride',components*4);offset=view.get('byteOffset',0)+accessor.get('byteOffset',0);minima=[float('inf')]*components;maxima=[float('-inf')]*components
   for row in range(accessor['count']):
    for component in range(components):
     at=offset+row*stride+component*4;v=struct.unpack_from('<f',blob,at)[0];fixed=max(0.,min(1.,v));max_excess=max(max_excess,abs(fixed-v));clamped+=int(v!=fixed);struct.pack_into('<f',blob,at,fixed);minima[component]=min(minima[component],fixed);maxima[component]=max(maxima[component],fixed)
   if 'min'in accessor:accessor['min']=minima
   if 'max'in accessor:accessor['max']=maxima
 doc['images']=[];doc['textures']=[];leafsources=[]
 for mat in doc['materials']:
  if 'Bark' in mat.get('name',''):
   mat.clear();mat.update({'name':'Quaternius_Bark_Simplified_PBR','pbrMetallicRoughness':{'baseColorFactor':[.08,.035,.012,1],'metallicFactor':0,'roughnessFactor':.95}})
  else:
   ref=mat['pbrMetallicRoughness']['baseColorTexture']['index'];image=oldimages[oldtextures[ref]['source']];imagebytes=z.read('glTF/'+image['uri']);blob.extend(b'\0'*((-len(blob))%4));view={'buffer':0,'byteOffset':len(blob),'byteLength':len(imagebytes)};blob.extend(imagebytes);doc['bufferViews'].append(view);doc['images'].append({'name':image.get('name','Leaves'),'mimeType':'image/png','bufferView':len(doc['bufferViews'])-1});doc['textures'].append({'source':len(doc['images'])-1,'sampler':0});nameold=mat['name'];mat.clear();mat.update({'name':nameold,'doubleSided':True,'alphaMode':'MASK','alphaCutoff':.5,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'baseColorTexture':{'index':len(doc['textures'])-1},'metallicFactor':0,'roughnessFactor':.9}});leafsources.append({'file':image['uri'],'sha256':hashlib.sha256(imagebytes).hexdigest(),'bytes':len(imagebytes)})
 doc['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}];doc['buffers']=[{'byteLength':len(blob)}];doc['asset'].setdefault('extras',{})['kalends_adaptation']='Original Quaternius Standard geometry and leaf texture; simplified untextured PBR bark. Vendor vertex colors clamped to the glTF0..1 range. General stylized foliage, not certified Mediterranean species.'
 output=DEST/file;write_glb(output,doc,blob);pos=[doc['accessors'][p['attributes']['POSITION']] for m in doc['meshes'] for p in m['primitives']];bounds={'min':[min(a['min'][i] for a in pos)for i in range(3)],'max':[max(a['max'][i]for a in pos)for i in range(3)]}
 return {'file':'foliage/'+file,'source_model':name,'source_gltf_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size,'triangles':sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes']for p in m['primitives']),'bounds':bounds,'leaf_artwork':leafsources,'clamped_vertex_color_components':clamped,'max_color_clamp_change':max_excess,'scope':'Original authored mesh and leaf-card texture; bark material simplified and vendor vertex colors range-clamped. Native rendering/placement remains to verify.'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('standard_archive',type=Path);a=p.parse_args();DEST.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(a.standard_archive) as z:
  rows=[package(z,'Pine_5','pine.glb'),package(z,'CommonTree_2','broadleaf.glb'),package(z,'Bush_Common','shrub.glb')];(ROOT/'kalends_3d/assets/licenses/Quaternius-Nature-CC0.txt').write_bytes(z.read('License_Standard.txt'))
 manifest={'schema':'kalends-foliage-assets-v1','artist':'Quaternius','source':'https://quaternius.itch.io/stylized-nature-megakit','license':'CC0-1.0','standard_upload_id':11055123,'archive_sha256':hashlib.sha256(a.standard_archive.read_bytes()).hexdigest(),'models':rows,'units':'meters; Y up; intended ground origin0; modeled roots/lower foliage extend ~0.24m below0. Scale pine~.45 for3.8m scene tree, broadleaf~.5 for3.7m, shrubs~.45 for.6m.','historical_scope':'Generic stylized pine, broadleaf tree and shrub; do not label them authenticated olive/cypress species or archaeological planting.','preparation':'scripts/immersion_assets_foliage.py with the artist\'s free Standard archive; no Pro/Source tier used.'};(DEST/'foliage.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(rows,indent=2))
