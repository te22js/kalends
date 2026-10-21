"""Independent numeric integrity checks of shipped skinned character GLBs.

This folds glTF transforms and linear-blend skinning without a renderer. It is
not a substitute for browser inspection, visual clothing/foot contact or GPU QA.
"""
from pathlib import Path
import json,struct,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def load(path):
 raw=path.read_bytes();assert raw[:4]==b'glTF';at=12;chunks={}
 while at<len(raw):
  size,kind=struct.unpack_from('<II',raw,at);chunks[kind]=raw[at+8:at+8+size];at+=8+size
 return json.loads(chunks[0x4e4f534a]),chunks[0x004e4942]

def array(doc,blob,index):
 a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']];types={5120:('i1',1),5121:('u1',1),5122:('<i2',2),5123:('<u2',2),5125:('<u4',4),5126:('<f4',4)};kind,size=types[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 result=np.ndarray((a['count'],n),dtype=kind,buffer=blob,offset=view.get('byteOffset',0)+a.get('byteOffset',0),strides=(view.get('byteStride',n*size),size)).copy()
 if a.get('normalized') and a['componentType']!=5126:result=result.astype(float)/(255 if a['componentType']==5121 else 65535)
 return result

def matrix(t,q,s):
 x,y,z,w=q;out=np.eye(4);out[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(s);out[:3,3]=t;return out

def pose(doc,blob,animation,time):
 trs=[{'translation':n.get('translation',[0,0,0]),'rotation':n.get('rotation',[0,0,0,1]),'scale':n.get('scale',[1,1,1])} for n in doc['nodes']]
 if animation:
  for channel in animation['channels']:
   sampler=animation['samplers'][channel['sampler']];times=array(doc,blob,sampler['input']).ravel();values=array(doc,blob,sampler['output']);after=min(len(times)-1,int(np.searchsorted(times,time,'right')));before=max(0,after-1);denom=times[after]-times[before];mix=0 if denom==0 else np.clip((time-times[before])/denom,0,1);a=values[before];b=values[after]
   if channel['target']['path']=='rotation' and np.dot(a,b)<0:b=-b
   value=a+(b-a)*mix
   if channel['target']['path']=='rotation':value/=np.linalg.norm(value)
   trs[channel['target']['node']][channel['target']['path']]=value
 parents={child:i for i,n in enumerate(doc['nodes']) for child in n.get('children',[])};world={}
 def get(index):
  if index not in world:
   n=doc['nodes'][index];local=np.array(n['matrix']).reshape(4,4).T if 'matrix'in n else matrix(trs[index]['translation'],trs[index]['rotation'],trs[index]['scale']);world[index]=get(parents[index])@local if index in parents else local
  return world[index]
 return np.array([get(i) for i in range(len(doc['nodes']))])

def bounds(doc,blob,animation=None,time=0):
 transforms=pose(doc,blob,animation,time);positions=[];weights_bad=0
 for node in doc['nodes']:
  if 'mesh' not in node:continue
  skin=doc['skins'][node['skin']];inverse=array(doc,blob,skin['inverseBindMatrices']).reshape((-1,4,4)).transpose(0,2,1);joint_matrices=transforms[skin['joints']]@inverse
  for prim in doc['meshes'][node['mesh']]['primitives']:
   p=array(doc,blob,prim['attributes']['POSITION']);j=array(doc,blob,prim['attributes']['JOINTS_0']);w=array(doc,blob,prim['attributes']['WEIGHTS_0']);weights_bad=max(weights_bad,float(np.max(np.abs(w.sum(axis=1)-1))));assert np.max(j)<len(skin['joints']);h=np.column_stack([p,np.ones(len(p))]);v=np.einsum('nvij,nj->nvi',joint_matrices[j],h);v=(v*w[:,:,None]).sum(axis=1)[:,:3];assert np.isfinite(v).all();positions.append(v)
 p=np.concatenate(positions);return {'min':p.min(axis=0).round(6).tolist(),'max':p.max(axis=0).round(6).tolist(),'max_weight_sum_error':weights_bad}

def verify(path):
 doc,blob=load(path);assert all('uri' not in b for b in doc['buffers']);assert all('uri' not in i for i in doc.get('images',[]));assert len(doc['skins'])==1
 rows=[]
 for animation in doc['animations']:
  duration=max(float(array(doc,blob,s['input'])[-1,0]) for s in animation['samplers']);samples=[]
  for fraction in [0,.25,.5,.75,1]:
   b=bounds(doc,blob,animation,duration*fraction);assert max(abs(v) for v in b['min']+b['max'])<4,'Exploding skin or transform';assert b['max_weight_sum_error']<1e-4;samples.append({'time':round(duration*fraction,6),**b})
  rows.append({'clip':animation['name'],'duration':round(duration,6),'samples':samples})
 return {'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bind_pose':bounds(doc,blob),'clips':rows,'passed':True,'scope':'Numeric finite transforms, bounded skinned positions, normalizedweights, validjointrefs, self-containedbuffer/images; five CPU-skinned samples perclip. BrowservisualQArequired.'}

if __name__=='__main__':
 result={'schema':'kalends-character-numeric-validation-v1','models':[verify(ROOT/'kalends_3d/assets/characters'/name) for name in ['roman_female.glb','roman_male.glb']]};p=ROOT/'kalends_3d/assets/characters/quaternius_validation.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':all(m['passed'] for m in result['models']),'models':len(result['models']),'clips':sum(len(m['clips']) for m in result['models']),'sampled_poses':sum(len(c['samples']) for m in result['models'] for c in m['clips'])},indent=2))
