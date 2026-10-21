"""Prepare documented civilian prototypes from official CC0 KayKit GLBs.

The source artist's rig, skinning, character mesh and selected animation curves
are retained. Weapon meshes, fantasy hats and capes are not rendered. This is
an adaptation of stylized fantasy clothing, not Roman archaeological evidence.
Run from repository root. Input source files and original license are local.
"""
from pathlib import Path
import hashlib,json,struct

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'kalends_3d/assets'
CLIPS={'Idle','Walking_A','Running_A','Interact','PickUp','Use_Item','Cheer'}

def read_glb(path):
 data=path.read_bytes();assert data[:4]==b'glTF';assert struct.unpack_from('<I',data,4)[0]==2
 chunks=[];at=12
 while at<len(data):
  length,kind=struct.unpack_from('<II',data,at);chunks.append((kind,data[at+8:at+8+length]));at+=8+length
 return json.loads(chunks[0][1]),next(c for k,c in chunks if k==0x004e4942)

def write_glb(path,doc,blob):
 raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);blob+=b'\0'*((-len(blob))%4)
 data=struct.pack('<4sII',b'glTF',2,12+8+len(raw)+8+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob
 path.write_bytes(data)

def prepare(source,destination):
 doc,blob=read_glb(source);removed=[]
 for node in doc['nodes']:
  if 'mesh' in node and 'skin' not in node:
   removed.append(node['name']);del node['mesh']
 doc['animations']=[a for a in doc['animations'] if a['name'] in CLIPS]
 doc.setdefault('asset',{}).setdefault('extras',{})['kalends_adaptation']='KayKit CC0 rig/mesh/curves; unskinned weapons, fantasy hats and cape meshes disabled; seven retained civilian locomotion/gesture clips. Costume remains stylized, not authenticated Roman dress.'
 # Repack accessors/buffer views so excluded animation data is not downloaded.
 used=set()
 for mesh in doc['meshes']:
  for prim in mesh['primitives']:
   used.update(prim['attributes'].values())
   if 'indices' in prim:used.add(prim['indices'])
   for target in prim.get('targets',[]):used.update(target.values())
 for skin in doc.get('skins',[]):
  if 'inverseBindMatrices' in skin:used.add(skin['inverseBindMatrices'])
 for animation in doc['animations']:
  for sampler in animation['samplers']:used.update([sampler['input'],sampler['output']])
 mapping={old:new for new,old in enumerate(sorted(used))}
 doc['accessors']=[doc['accessors'][i] for i in sorted(used)]
 for mesh in doc['meshes']:
  for prim in mesh['primitives']:
   prim['attributes']={k:mapping[v] for k,v in prim['attributes'].items()}
   if 'indices' in prim:prim['indices']=mapping[prim['indices']]
   for target in prim.get('targets',[]):
    for key in target:target[key]=mapping[target[key]]
 for skin in doc.get('skins',[]):
  if 'inverseBindMatrices' in skin:skin['inverseBindMatrices']=mapping[skin['inverseBindMatrices']]
 for animation in doc['animations']:
  for sampler in animation['samplers']:
   for key in ['input','output']:sampler[key]=mapping[sampler[key]]
 views=set()
 for accessor in doc['accessors']:
  assert 'sparse' not in accessor,'Sparse accessor requires separate preservation'
  if 'bufferView' in accessor:views.add(accessor['bufferView'])
 for image in doc.get('images',[]):
  if 'bufferView' in image:views.add(image['bufferView'])
 vmapping={old:new for new,old in enumerate(sorted(views))};newviews=[];newblob=bytearray()
 for index in sorted(views):
  view=dict(doc['bufferViews'][index]);assert view['buffer']==0
  offset=view.get('byteOffset',0);n=view['byteLength'];newblob.extend(b'\0'*((-len(newblob))%4));view['byteOffset']=len(newblob);newblob.extend(blob[offset:offset+n]);newviews.append(view)
 doc['bufferViews']=newviews;doc['buffers']=[{'byteLength':len(newblob)}]
 for accessor in doc['accessors']:
  if 'bufferView' in accessor:accessor['bufferView']=vmapping[accessor['bufferView']]
 for image in doc.get('images',[]):
  if 'bufferView' in image:image['bufferView']=vmapping[image['bufferView']]
 write_glb(destination,doc,bytes(newblob))
 bounds=[]
 for node in doc['nodes']:
  if 'mesh' in node:
   for primitive in doc['meshes'][node['mesh']]['primitives']:
    accessor=doc['accessors'][primitive['attributes']['POSITION']];bounds.append((accessor['min'],accessor['max']))
 minimum=[min(a[i] for a,b in bounds) for i in range(3)];maximum=[max(b[i] for a,b in bounds) for i in range(3)]
 return {'file':str(destination.relative_to(ASSETS)),'source':str(source.relative_to(ASSETS)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'bytes':destination.stat().st_size,'removed_meshes':removed,'clips':[a['name'] for a in doc['animations']],'bind_pose_bounds':{'min':minimum,'max':maximum},'skins':len(doc['skins']),'scale_to_1_7m':1.7/(maximum[1]-minimum[1])}

if __name__=='__main__':
 female=prepare(ASSETS/'characters/kaykit_rogue.glb',ASSETS/'characters/civilian_female.glb')
 male=prepare(ASSETS/'characters/kaykit_barbarian.glb',ASSETS/'characters/civilian_male.glb')
 roles={'idle':'Idle','walk':'Walking_A','run':'Running_A','talk':'Interact','work':'Use_Item','pickup':'PickUp','celebrate':'Cheer'}
 colors={'Player':'#cba076','Felix':'#d4ba8e','Sabina':'#b26e58','Marcus':'#b9a477','Chreste':'#9dafa1','Dama':'#9f778a','Lucius':'#bdb6a1'}
 variants={}
 for name in colors:
  model=female if name in ['Player','Sabina','Chreste'] else male
  variants[name]={'file':model['file'],'scale':model['scale_to_1_7m'],'yaw':0,'height':1.7,'tint':colors[name],'clips':roles}
 result={'schema':'kalends-character-assets-v1','units':'glTF meters, Y up, +Z character facing in bind pose; scale .777 yields 1.7m','clips':roles,'variants':variants,'models':[female,male],'license':'CC0-1.0; see assets/licenses/KayKit-CC0.txt','artist':'Kay Lousberg / KayKit','historical_scope':'Stylized fantasy meshes adapted by disabling weapon/hat/cape meshes. Clothing and body proportions are not authenticated Roman dress; purpose-built Roman wardrobe remains an art task.'}
 (ASSETS/'characters/kaykit_characters.json').write_text(json.dumps(result,indent=2)+'\n')
 runtime=ASSETS/'characters/characters.json'
 if not runtime.exists():runtime.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
