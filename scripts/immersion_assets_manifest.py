"""Fingerprint locally shipped Immersion assets and their license provenance.

Run after any asset rebuild. This inventory does not make a new public-domain
dedication of project-authored code/art. Third-party CC0 sources remain credited.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'kalends_3d/assets'

def source_group(path):
 name=str(path.relative_to(ASSETS))
 if name.startswith('materials/'):return 'poly_haven'
 if name.startswith('sources/quaternius/'):return 'quaternius_humans'
 if name.startswith('foliage/'):return 'quaternius_nature'
 if name.startswith('characters/'):
  if path.name=='environment_khronos_validation.json':return 'original_district_with_cc0_materials'
  return 'kaykit_fallback' if any(x in path.name for x in ['kaykit','civilian']) else 'quaternius_humans'
 if name.startswith('environment/'):return 'original_district_with_cc0_materials'
 if name.startswith('licenses/'):
  if 'PolyHaven'in name:return 'poly_haven'
  if 'KayKit'in name:return 'kaykit_fallback'
  if 'Nature'in name:return 'quaternius_nature'
  return 'quaternius_humans'
 return 'project_generated'

if __name__=='__main__':
 current=json.loads((ASSETS/'characters/characters.json').read_text());runtime=sorted({v['file'] for v in current['variants'].values()});imported=json.loads((ASSETS/'sources/quaternius/IMPORT.json').read_text());nature=json.loads((ASSETS/'foliage/foliage.json').read_text()) if (ASSETS/'foliage/foliage.json').exists() else None
 groups={
 'quaternius_humans':{'authors':['Quaternius'],'license':'CC0-1.0 for artist body/hair/rig/motion. Project-created tunic/belt and transformations retain projectowner rights.','official_sources':imported['official_sources'],'base_archive_sha256':imported['base_archive_sha256'],'animation_archive_sha256':imported['animation_archive_sha256'],'standard_upload_ids':{'body':15861669,'animation':17958403},'license_files':['assets/licenses/Quaternius-Base-CC0.txt','assets/licenses/Quaternius-Animation-CC0.txt'],'modifications':['Original body vertices, skin weights and vendor sources preserved; clothed runtime omits covered torso/hip triangles to prevent garment intersections.','Selected original hair geometry weighted rigidly to the original Head joint.','Project-authored pleated linen tunic and belt weighted to the body rig.','Nine of43 free Standard source clips selected, matched by bone name and retargeted via local rest-transform deltas.','Per-clip constant visual root-height calibration from21 sampled CPU-skinned poses.','Untextured PBR skin/linen plus original brown-eye texture; high-resolution source body maps intentionally unused.','Exact skin/cloth/trim material names support per-identity palette.'],'source_subset_note':'Preserved source body glTF JSON references unused vendor maps absent from this selected source subset. The preparation script intentionally replaces those materials. Runtime outputs are complete self-contained GLBs. Official complete ZIP fingerprints and free import paths are retained.','validation':'assets/characters/quaternius_validation.json:2models x9clips x5sampledposes; numericchecks, notbrowserqualitycertificate. OfficialKhronos schema reports in assets/characters/khronos_validation.json:0errors onall5 newcharacter/foliageGLBs; unchangedidentityArmatureparentwarnings oncharacters.'},
 'kaykit_fallback':{'authors':['Kay Lousberg / KayKit'],'license':'CC0-1.0','source':'https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0','source_revision':'672074b73ba276876a19e8816ecdc5241817ab47','license_files':['assets/licenses/KayKit-CC0.txt'],'runtime_status':'Earlier engine-spike mapping retained; currentcharacters.json uses Quaternius humans.','modifications':['Original Rogue/Barbarian GLBs preserved.','Civilian derivatives disable weapon, fantasyhat and cape meshes; seven source clips retained and unused animation buffers repacked.'],'historical_scope':'Stylized fantasy costume bases, not authentic Roman clothes.'},
 'poly_haven':{'authors':['Rob Tuytel','Stephan Seeliger','Dimitrios Savva','Rico Cilliers'],'license':'CC0-1.0','license_url':'https://polyhaven.com/license','license_files':['assets/licenses/PolyHaven-CC0.txt'],'individual_sources':'assets/materials/materials.json','modifications':'All12 downloaded1K JPGmaps unchanged and verified against upstreamMD5. Model materials may apply project palette factors.','channel_conventions':'Diffuse sRGB; OpenGL normal and ARM linear; ARM =Rao/Groughness/Bmetallic.','historical_scope':'Modern photographed material references; not photographs of Pompeii.'},
 'original_district_with_cc0_materials':{'authors':['Kalends project','Poly Haven material artists'],'license':'Original environment geometry/layout belongs to projectowner; embedded PolyHaven maps remainCC0.','license_files':['assets/environment/LICENSE.txt','assets/licenses/PolyHaven-CC0.txt'],'detail':'assets/environment/scene_manifest.json','independent_validation':'assets/characters/environment_khronos_validation.json; official Khronos validator: zero errors, generated tangent-space warnings because PlayCanvas supplies tangents at load.','historical_scope':'Roman-inspired original reconstruction, not a survey or a medieval asset represented as historical Roman architecture.'},
 'project_generated':{'authors':['Kalends project'],'license':'Projectowner rights; no new general dedication.'}
 }
 if nature:groups['quaternius_nature']={'authors':['Quaternius'],'license':'CC0-1.0','source':nature['source'],'standard_upload_id':nature['standard_upload_id'],'archive_sha256':nature['archive_sha256'],'license_files':['assets/licenses/Quaternius-Nature-CC0.txt'],'detail':'assets/foliage/foliage.json','modifications':'Three original mesh/leaf-card models repackaged as self-contained GLBs; bark uses a scalar PBRmaterial instead of unused4Kmaps. LeafPNG bytes unchanged; vendor vertex colors range-clamped toglTF0..1 (exactcounts in detailmanifest).','historical_scope':nature['historical_scope']}
 files=[]
 for p in sorted(ASSETS.rglob('*')):
  if not p.is_file():continue
  raw=p.read_bytes();files.append({'file':str(p.relative_to(ROOT/'kalends_3d')),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'source_group':source_group(p)})
 result={'schema':'kalends-immersion-asset-provenance-v1','created_utc':datetime.now(timezone.utc).isoformat(),'asset_cost_usd':0,'paid_tiers_used':False,'runtime_asset_account_required':False,'current_character_mapping':'assets/characters/characters.json','runtime_character_glbs':runtime,'preserved_earlier_mapping':'assets/characters/kaykit_characters.json','source_groups':groups,'files':files,'total_local_asset_bytes':sum(f['bytes']for f in files),'inventory_scope':'Asset files only; engine/npm licenses and application source are documented separately. Rerun scripts/immersion_assets_manifest.py after asset rebuilds to refresh exact fingerprints.'}
 (ROOT/'kalends_3d/ASSET_PROVENANCE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'files':len(files),'total_bytes':result['total_local_asset_bytes'],'runtime_models':runtime,'source_groups':len(groups)},indent=2))
