"""Build Roman-inspired clothed humanoids from actual Quaternius CC0 assets.

Uses the artist's free Universal Base Characters + Universal Animation Library
Standard packs. Original surface meshes, skinning and motion curves remain;
local-rest transforms are retargeted by matching bone names. A project-authored
pleated linen tunic, belt and artist-authored hair are skinned to that rig.
This is a stylized costume interpretation, not an archaeological reconstruction.

Run with bundled Python 3.12 + NumPy. The two free downloaded ZIPs are optional
arguments for source import; after import all required sources are local.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,math,shutil,struct,zipfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'kalends_3d/assets'
SOURCES=ASSETS/'sources/quaternius'
CLIPS=['Idle_Loop','Walk_Loop','Jog_Fwd_Loop','Sprint_Loop','Idle_Talking_Loop','Interact','PickUp_Table','Fixing_Kneeling','Dance_Loop']
ROLE_CLIPS={'idle':'Idle_Loop','walk':'Walk_Loop','run':'Jog_Fwd_Loop','talk':'Idle_Talking_Loop','work':'PickUp_Table','pickup':'PickUp_Table','celebrate':'Interact'}
CT={5126:('<f4',4),5125:('<u4',4),5123:('<u2',2),5122:('<i2',2),5121:('u1',1),5120:('i1',1)}
COUNT={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def import_sources(base,animation):
 SOURCES.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(base) as z:
  required=['Superhero_Male_FullBody.gltf','Superhero_Male_FullBody.bin','Superhero_Female_FullBody.gltf','Superhero_Female_FullBody.bin','T_Eye_Brown.png']
  for name in required:
   match=next(n for n in z.namelist() if '/Base Characters/Godot - UE/' in n and n.endswith('/'+name));(SOURCES/name).write_bytes(z.read(match))
  for name in ['Hair_Buns','Hair_SimpleParted','Hair_Beard']:
   for ext in ['gltf','bin']:
    match=next(n for n in z.namelist() if '/Hairstyles/Origin at 0/glTF (Godot)/' in n and n.endswith('/'+name+'.'+ext));(SOURCES/(name+'.'+ext)).write_bytes(z.read(match))
  license=next(n for n in z.namelist() if n.endswith('/License_Standard.txt'));(ASSETS/'licenses/Quaternius-Base-CC0.txt').write_bytes(z.read(license))
 with zipfile.ZipFile(animation) as z:
  name=next(n for n in z.namelist() if n.endswith('/Unreal-Godot/UAL1_Standard.glb'));(SOURCES/'UAL1_Standard.glb').write_bytes(z.read(name))
  license=next(n for n in z.namelist() if n.endswith('/License.txt'));(ASSETS/'licenses/Quaternius-Animation-CC0.txt').write_bytes(z.read(license))
 (SOURCES/'IMPORT.json').write_text(json.dumps({'base_archive_sha256':sha(base),'animation_archive_sha256':sha(animation),'base_standard_upload_id':15861669,'animation_standard_upload_id':17958403,'official_sources':['https://quaternius.com/packs/universalbasecharacters.html','https://quaternius.itch.io/universal-base-characters','https://quaternius.itch.io/universal-animation-library'],'scope':'Selected source geometry/bin/eye texture/hair and animation Standard GLB only. Source body glTF includes references to maps not used by this preparation pipeline. Runtime outputs are complete self-contained GLBs. No Source/Pro paid tier.'},indent=2)+'\n')

def read_glb(path):
 b=path.read_bytes();assert b[:4]==b'glTF';at=12;chunks={}
 while at<len(b):
  n,t=struct.unpack_from('<II',b,at);chunks[t]=b[at+8:at+8+n];at+=8+n
 return json.loads(chunks[0x4e4f534a]),chunks[0x004e4942]

def data(doc,blob,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];dtype,size=CT[a['componentType']];count=COUNT[a['type']];stride=v.get('byteStride',size*count);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
 assert not a.get('sparse')
 return np.ndarray((a['count'],count),dtype=dtype,buffer=blob,offset=offset,strides=(stride,size)).copy()

def quat_mul(a,b):
 a=np.asarray(a);b=np.asarray(b);av=a[...,:3];bv=b[...,:3];aw=a[...,3:4];bw=b[...,3:4]
 return np.concatenate([aw*bv+bw*av+np.cross(av,bv),aw*bw-np.sum(av*bv,axis=-1,keepdims=True)],axis=-1)

def write_glb(path,doc,blob):
 raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);blob=bytes(blob)+b'\0'*((-len(blob))%4)
 path.write_bytes(struct.pack('<4sII',b'glTF',2,12+16+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob)

class Builder:
 def __init__(self,sex):
  self.sex=sex;self.source=SOURCES/f'Superhero_{sex}_FullBody.gltf';self.doc=json.loads(self.source.read_text());self.blob=bytearray((SOURCES/self.doc['buffers'][0]['uri']).read_bytes());self.doc['buffers']=[{'byteLength':len(self.blob)}]
  self.doc['images']=[];self.doc['textures']=[];self.doc['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}]
  for index,mat in enumerate(self.doc['materials']):
   name=mat['name'];base={'metallicFactor':0,'roughnessFactor':.8}
   if 'Eyes' in name:
    view=self.bytes((SOURCES/'T_Eye_Brown.png').read_bytes());self.doc['images'].append({'bufferView':view,'mimeType':'image/png','name':'Quaternius_Eye_Brown'});self.doc['textures'].append({'sampler':0,'source':0});base.update({'baseColorFactor':[1,1,1,1],'baseColorTexture':{'index':0},'roughnessFactor':.38});name='KALENDS_Eyes'
   elif 'Hair' in name:base['baseColorFactor']=[.07,.038,.022,1];name='KALENDS_Hair'
   else:base['baseColorFactor']=[.24,.10,.045,1];name='KALENDS_Skin'
   self.doc['materials'][index]={'name':name,'pbrMetallicRoughness':base}
  self.body=max(self.doc['meshes'],key=lambda m:sum(self.doc['accessors'][p['attributes']['POSITION']]['count'] for p in m['primitives']))
  prim=self.body['primitives'][0];self.body_positions=data(self.doc,self.blob,prim['attributes']['POSITION']);self.body_joints=data(self.doc,self.blob,prim['attributes']['JOINTS_0']);self.body_weights=data(self.doc,self.blob,prim['attributes']['WEIGHTS_0'])
  self.height=float(self.body_positions[:,1].max()-self.body_positions[:,1].min());self.ratio=self.height/1.8195864
  self.cloth=self.material('KALENDS_Cloth',[.56,.34,.12,1],.94)
  self.trim=self.material('KALENDS_Cloth_Trim',[.29,.12,.078,1],.9)
 def bytes(self,value,target=None):
  self.blob.extend(b'\0'*((-len(self.blob))%4));offset=len(self.blob);self.blob.extend(value);view={'buffer':0,'byteOffset':offset,'byteLength':len(value)}
  if target:view['target']=target
  self.doc['bufferViews'].append(view);return len(self.doc['bufferViews'])-1
 def accessor(self,array,kind,component=5126,target=None,bounds=False):
  array=np.asarray(array,dtype=CT[component][0]);array=array.reshape((-1,COUNT[kind]));view=self.bytes(array.tobytes(),target);a={'bufferView':view,'componentType':component,'count':len(array),'type':kind}
  if bounds:a.update({'min':array.min(axis=0).tolist(),'max':array.max(axis=0).tolist()})
  self.doc['accessors'].append(a);return len(self.doc['accessors'])-1
 def material(self,name,color,roughness):
  self.doc['materials'].append({'name':name,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':color,'metallicFactor':0,'roughnessFactor':roughness}});return len(self.doc['materials'])-1
 def nearest_weights(self,positions):
  positions=np.asarray(positions);delta=positions[:,None,:]-self.body_positions[None,:,:];nearest=np.argmin(np.sum(delta*delta,axis=2),axis=1)
  return self.body_joints[nearest],self.body_weights[nearest]
 def mesh(self,name,positions,normals,indices,material,joints=None,weights=None,uv=None):
  if joints is None:joints,weights=self.nearest_weights(positions)
  attrs={'POSITION':self.accessor(positions,'VEC3',target=34962,bounds=True),'NORMAL':self.accessor(normals,'VEC3',target=34962),'JOINTS_0':self.accessor(joints,'VEC4',5123,target=34962),'WEIGHTS_0':self.accessor(weights,'VEC4',target=34962)}
  if uv is not None:attrs['TEXCOORD_0']=self.accessor(uv,'VEC2',target=34962)
  prim={'attributes':attrs,'indices':self.accessor(indices,'SCALAR',5123,target=34963),'material':material};self.doc['meshes'].append({'name':name,'primitives':[prim]});node={'name':name,'mesh':len(self.doc['meshes'])-1,'skin':0};self.doc['nodes'].append(node);nodeidx=len(self.doc['nodes'])-1;armature=next(n for n in self.doc['nodes'] if n.get('name')=='Armature');armature['children'].append(nodeidx)
 def tunic(self):
  # A shaped pleated garment with side arm openings, shoulder bridges, an open
  # neckline and a knee-length hem. Not a primitive cylinder/body proxy.
  profiles=[(.56,.275,.175),(.67,.265,.17),(.79,.244,.16),(.90,.222,.15),(.98,.208,.142),(1.08,.216,.15),(1.20,.247,.17),(1.30,.277,.175),(1.39,.295,.164),(1.47,.282,.148),(1.525,.105,.09)]
  n=48;pos=[];norm=[];uv=[]
  for ri,(y,rx,rz) in enumerate(profiles):
   for j in range(n):
    a=2*math.pi*j/n;pleat=(.013 if y<.9 else .004)*math.cos(12*a+(.4 if self.sex=='Female' else 0));x=(rx+pleat)*math.cos(a);z=(rz+.02+pleat)*math.sin(a)-.015
    if y>1.47:y+=.008*math.sin(a)
    pos.append([x*self.ratio,y*self.ratio,z*self.ratio]);no=np.array([math.cos(a)/rx,0.05,math.sin(a)/rz]);norm.append((no/np.linalg.norm(no)).tolist());uv.append([j/n,y])
  ix=[]
  for ri in range(len(profiles)-1):
   for j in range(n):
    a=2*math.pi*(j+.5)/n
    if 7<=ri<=8 and abs(math.cos(a))>.85:continue
    a0=ri*n+j;b=ri*n+(j+1)%n;c=(ri+1)*n+j;d=(ri+1)*n+(j+1)%n;ix.extend([a0,b,c,b,d,c])
  self.mesh('Kalends_Pleated_Linen_Tunic',pos,norm,ix,self.cloth,uv=uv)
  # A woven belt, modeled around the waist, follows the same skin rig.
  pos=[];norm=[];ix=[];uv=[]
  for y in [.972,1.006]:
   for j in range(n):
    a=2*math.pi*j/n;pos.append([.218*math.cos(a)*self.ratio,y*self.ratio,(.178*math.sin(a)-.015)*self.ratio]);norm.append([math.cos(a),0,math.sin(a)]);uv.append([j/n,y])
  for j in range(n):a=j;b=(j+1)%n;c=n+j;d=n+(j+1)%n;ix.extend([a,b,c,b,d,c])
  self.mesh('Kalends_Woven_Belt',pos,norm,ix,self.trim,uv=uv)
  # Covered skin is omitted from the rendered body index list, as in normal
  # game clothing preparation. Keep the untouched vendor source and all body
  # vertices/weights; this prevents hips/torso breaking through posed cloth.
  primitive=self.body['primitives'][0]
  indices=data(self.doc,self.blob,primitive['indices']).reshape((-1,3))
  names=[self.doc['nodes'][i]['name'] for i in self.doc['skins'][0]['joints']]
  primary=self.body_joints[np.arange(len(self.body_positions)),np.argmax(self.body_weights,axis=1)]
  torso={names.index(name) for name in ['pelvis','spine_01','spine_02','spine_03','thigh_l','thigh_r']}
  covered=np.isin(primary,list(torso))&(self.body_positions[:,1]/self.ratio>.64)&(self.body_positions[:,1]/self.ratio<1.48)
  hidden=np.all(covered[indices],axis=1)
  self.hidden_body_triangles=int(hidden.sum())
  primitive['indices']=self.accessor(indices[~hidden].reshape(-1),'SCALAR',5123,target=34963)
 def hair(self,name):
  doc=json.loads((SOURCES/(name+'.gltf')).read_text());blob=(SOURCES/doc['buffers'][0]['uri']).read_bytes();prim=doc['meshes'][0]['primitives'][0];pos=data(doc,blob,prim['attributes']['POSITION']);norm=data(doc,blob,prim['attributes']['NORMAL']);ix=data(doc,blob,prim['indices']).ravel()
  if name=='Hair_Buns':
   pos=np.column_stack([pos[:,0],-pos[:,2],pos[:,1]])*.01;norm=np.column_stack([norm[:,0],-norm[:,2],norm[:,1]])
  headnode=next(i for i,n in enumerate(self.doc['nodes']) if n.get('name')=='Head');headjoint=self.doc['skins'][0]['joints'].index(headnode);joints=np.zeros((len(pos),4),dtype=np.uint16);joints[:,0]=headjoint;weights=np.zeros((len(pos),4));weights[:,0]=1
  mat=next(i for i,m in enumerate(self.doc['materials']) if m['name']=='KALENDS_Hair');self.mesh('Quaternius_'+name,pos,norm,ix,mat,joints,weights)
 def animations(self):
  source,blob=read_glb(SOURCES/'UAL1_Standard.glb');named={n.get('name'):i for i,n in enumerate(self.doc['nodes'])};self.doc['animations']=[];matches=0
  for animation in source['animations']:
   if animation['name'] not in CLIPS:continue
   out={'name':animation['name'],'samplers':[],'channels':[]};inputs={}
   for channel in animation['channels']:
    src=source['nodes'][channel['target']['node']];name=src.get('name');path=channel['target']['path']
    if name not in named:continue
    target=named[name];dst=self.doc['nodes'][target];sampler=animation['samplers'][channel['sampler']];values=data(source,blob,sampler['output']).astype(np.float64)
    if path=='rotation':
     q_src=np.array(src.get('rotation',[0,0,0,1]));q_dst=np.array(dst.get('rotation',[0,0,0,1]));inverse=q_src*np.array([-1,-1,-1,1]);prefix=quat_mul(q_dst,inverse);values=quat_mul(prefix,values);values/=np.linalg.norm(values,axis=1,keepdims=True)
    elif path=='translation':values=np.array(dst.get('translation',[0,0,0]))+(values-np.array(src.get('translation',[0,0,0])))*self.ratio
    elif path=='scale':values=values/np.array(src.get('scale',[1,1,1]))*np.array(dst.get('scale',[1,1,1]))
    else:continue
    assert np.isfinite(values).all()
    if sampler['input'] not in inputs:inputs[sampler['input']]=self.accessor(data(source,blob,sampler['input']),'SCALAR',bounds=True)
    out['samplers'].append({'input':inputs[sampler['input']],'output':self.accessor(values,'VEC4' if path=='rotation' else 'VEC3'),'interpolation':sampler.get('interpolation','LINEAR')});out['channels'].append({'sampler':len(out['samplers'])-1,'target':{'node':target,'path':path}});matches+=1
   self.doc['animations'].append(out)
  assert set(CLIPS)==set(a['name'] for a in self.doc['animations']);return matches
 def ground_clips(self):
  from immersion_assets_validate import bounds
  self.ground_offsets={}
  root=next(i for i,n in enumerate(self.doc['nodes']) if n.get('name')=='root')
  for animation in self.doc['animations']:
   duration=max(float(data(self.doc,self.blob,a['input'])[-1,0]) for a in animation['samplers'])
   floor=min(bounds(self.doc,self.blob,animation,float(t))['min'][1] for t in np.linspace(0,duration,21))
   channel=next(c for c in animation['channels'] if c['target']=={'node':root,'path':'translation'})
   accessor=animation['samplers'][channel['sampler']]['output'];values=data(self.doc,self.blob,accessor);values[:,1]-=floor
   a=self.doc['accessors'][accessor];v=self.doc['bufferViews'][a['bufferView']];at=v.get('byteOffset',0)+a.get('byteOffset',0);raw=values.astype('<f4').tobytes();self.blob[at:at+len(raw)]=raw;self.ground_offsets[animation['name']]=-floor
 def save(self,path):
  self.doc['buffers']=[{'byteLength':len(self.blob)}];self.doc['asset'].setdefault('extras',{})['kalends_provenance']='Quaternius Universal Base Characters Standard + Universal Animation Library Standard (CC0). Project-authored pleated linen tunic and belt; original mesh weights preserved. Clips retargeted by matched local rest transforms; no root-motion authority.'
  write_glb(path,self.doc,self.blob)
  return {'file':str(path.relative_to(ASSETS)),'bytes':path.stat().st_size,'sha256':sha(path),'source_body_sha256':sha(self.source),'source_animation_sha256':sha(SOURCES/'UAL1_Standard.glb'),'height':self.height,'scale_to_1_7m':1.7/self.height,'clips':CLIPS,'skins':len(self.doc['skins']),'triangles':sum(self.doc['accessors'][p['indices']]['count']//3 for m in self.doc['meshes'] for p in m['primitives']),'covered_body_triangles_omitted':self.hidden_body_triangles,'mesh_nodes':[n['name'] for n in self.doc['nodes'] if 'mesh'in n]}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--base-archive',type=Path);parser.add_argument('--animation-archive',type=Path);args=parser.parse_args()
 if args.base_archive and args.animation_archive:import_sources(args.base_archive,args.animation_archive)
 reports=[]
 for sex in ['Female','Male']:
  builder=Builder(sex);builder.tunic();builder.hair('Hair_Buns' if sex=='Female' else 'Hair_SimpleParted')
  if sex=='Male':builder.hair('Hair_Beard')
  channels=builder.animations();builder.ground_clips();path=ASSETS/'characters'/('roman_'+sex.lower()+'.glb');report=builder.save(path);report['retargeted_channels']=channels;report['clip_root_height_offsets_m']=builder.ground_offsets;reports.append(report)
 (ASSETS/'characters/quaternius_preparation.json').write_text(json.dumps({'schema':'kalends-quaternius-preparation-v1','models':reports,'roles':ROLE_CLIPS,'asset_sources':'sources/quaternius/IMPORT.json','scope':'Artist-authored body/hair/rig/skinning/motion; project-authored linen tunic and belt; stylistic Roman inspiration, not certified historical costume. Requires native visual QA before switching runtime variants.'},indent=2)+'\n')
 for name in ['quaternius_characters.json','characters.json']:
  manifest=ASSETS/'characters'/name
  if manifest.exists():
   payload=json.loads(manifest.read_text())
   if payload.get('schema')=='kalends-character-assets-v2':
    payload['models']=reports;manifest.write_text(json.dumps(payload,indent=2)+'\n')
 print(json.dumps(reports,indent=2))
