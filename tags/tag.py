#!/usr/bin/env python3
"""SALST virtual cattle robot. Wi-Fi/HTTP simulation ONLY; not physical hardware control."""
import argparse,os,time,random,math,csv,requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1]/"backend"/".env", override=False)
p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--seed',type=int,default=1);p.add_argument('--reset-position',action='store_true');a=p.parse_args()
base=os.getenv('SALST_URL','http://127.0.0.1:5000');key=os.getenv('SALST_INGEST_KEY','');headers={'X-Tag-Key':key}
if not key:raise SystemExit('Missing SALST_INGEST_KEY')
rng=random.Random(a.seed);state=Path(__file__).resolve().parent/f'.{a.tag}.position';heading=rng.uniform(0,360)
with (Path(__file__).resolve().parents[1]/'data'/'tags.csv').open(newline='') as f: row=next((r for r in csv.DictReader(f) if r['tag_id']==a.tag),None)
if not row:raise SystemExit('Unknown tag '+a.tag)
lat,lon=float(row['latitude']),float(row['longitude'])
if state.exists() and not a.reset_position:
 try:lat,lon,heading=map(float,state.read_text().split(','))
 except Exception:pass
revision=-1;instruction={'action':'wander'};path=[];last_report=0;last_tick=time.monotonic();last_farm=None

def distance(a,b,c,d):
 return math.hypot((c-a)*111195,(d-b)*111195*max(.01,math.cos(math.radians(a))))
def bearing(a,b,c,d):
 return math.degrees(math.atan2((d-b)*math.cos(math.radians(a)),c-a))%360

def move(lat,lon,heading,meters):
 rad=math.radians(heading)
 return lat+math.cos(rad)*meters/111195,lon+math.sin(rad)*meters/(111195*max(.01,math.cos(math.radians(lat))))
print(a.tag,'virtual robot started',flush=True)
while True:
 try:
  now=time.monotonic();dt=min(2,max(0,now-last_tick));last_tick=now
  control=requests.get(base+'/api/simulator/'+a.tag,headers=headers,timeout=5);control.raise_for_status();payload=control.json()
  if payload['revision']!=revision:
   revision=payload['revision'];instruction=payload['instruction'];path=list(instruction.get('points',[]))
  status=requests.get(base+'/api/ingest-status/'+a.tag,headers=headers,timeout=5);status.raise_for_status();s=status.json()
  farm=requests.get(base+'/api/tag-farm/'+a.tag,headers=headers,timeout=5);farm.raise_for_status();f=farm.json()
  if not f.get('configured'):
   print(a.tag,'waiting for grazing boundary',flush=True);time.sleep(2);continue
  if s['seq']==0 and not state.exists():lat,lon=f['lat'],f['lon']
  action=instruction.get('action','wander');speed=0
  if action=='wander':
   heading=(heading+rng.gauss(0,12)*dt)%360
   dist=distance(lat,lon,f['lat'],f['lon'])
   # Usually remain near the farm, but sometimes deliberately wander across the boundary.
   if dist>f['radius']*.65 and rng.random()<.65:heading=bearing(lat,lon,f['lat'],f['lon'])
   if rng.random()<.008:heading=(heading+180)%360
   speed=1.8 if rng.random()>.12 else 0
  elif action=='escape':
   # Point away from farm centre, then continue straight until explicitly stopped.
   if revision!=locals().get('escape_revision'):
    heading=bearing(f['lat'],f['lon'],lat,lon) if distance(lat,lon,f['lat'],f['lon'])>1 else rng.uniform(0,360)
    escape_revision=revision
   speed=5
  elif action=='drive':heading=float(instruction['heading']);speed=4
  elif action=='return':heading=bearing(lat,lon,f['lat'],f['lon']);speed=5
  elif action=='path':
   while path and distance(lat,lon,*path[0])<3:path.pop(0)
   if path:heading=bearing(lat,lon,*path[0]);speed=min(4,max(.4,distance(lat,lon,*path[0])/max(dt,.1)))
   else:
    # A path is one-shot: don't repeat it; wait for the next instruction.
    instruction={'action':'stop'}
  lat,lon=move(lat,lon,heading,speed*dt)
  state.write_text(f'{lat},{lon},{heading}')
  interval=max(1,int(s['emergency_sec'] if s['mode']=='emergency' else s['peace_sec']))
  # Fast visual feedback during manual demos, otherwise configured telemetry interval.
  if now-last_report>= (1 if action in ('escape','drive','return','path') else interval):
   seq=s['seq']+1;battery=max(5,float(s['battery'])-.003)
   result=requests.post(base+'/api/ingest/'+a.tag,json={'seq':seq,'lat':lat,'lon':lon,'battery':round(battery,2)},headers=headers,timeout=5);result.raise_for_status()
   last_report=now
   print(f'{a.tag} #{seq} {result.json()["mode"]} {action} {lat:.6f},{lon:.6f}',flush=True)
  time.sleep(1)
 except (requests.RequestException,KeyError,ValueError,TypeError) as e:
  print(a.tag,'retry:',e,flush=True);time.sleep(3)
