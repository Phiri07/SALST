"""Idempotent CSV importer. Never deletes reports/events or overwrites passwords for existing accounts."""
import csv,sys,hashlib,secrets
from pathlib import Path
from server import conn,init,valid_password
ROOT=Path(__file__).resolve().parents[1]
def rows(name):
 with (ROOT/'data'/name).open(newline='') as f:return list(csv.DictReader(f))
def hashed(password):
 salt=secrets.token_hex(16)
 return salt+':'+hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),250000).hex()
def main():
 init();farms=rows('farms.csv');users=rows('users.csv');tags=rows('tags.csv')
 if not farms or not users:raise ValueError('Missing farm or users')
 for u in users:
  if not valid_password(u['password']):raise ValueError('Invalid password for '+u['email'])
 with conn() as c:
  owners={}
  for farm in farms:
   code=farm['farm_code'];members=[u for u in users if u['farm_code']==code]
   owner=next((u for u in members if u['role']=='owner'),None)
   if not owner:raise ValueError('No owner for '+code)
   existing=c.execute('SELECT id,role FROM owners WHERE email=%s',(owner['email'],)).fetchone()
   if existing:
    oid=existing['id']
    if existing['role']!='owner':raise ValueError('Existing owner role mismatch')
   else:
    oid=c.execute('INSERT INTO owners(email,name,pw,role) VALUES(%s,%s,%s,%s) RETURNING id',(owner['email'],owner['name'],hashed(owner['password']),'owner')).fetchone()['id']
   owners[code]=oid
   c.execute('INSERT INTO geofences(owner,shape,lat,lon,radius) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(owner) DO NOTHING',(oid,farm['boundary_shape'],float(farm['latitude']),float(farm['longitude']),float(farm['radius_m'])))
   for u in members:
    if u['role']=='owner':continue
    if u['role'] not in ('manager','worker'):raise ValueError('Invalid role')
    found=c.execute('SELECT id,farm_owner FROM owners WHERE email=%s',(u['email'],)).fetchone()
    if found:
     if found['farm_owner']!=oid:raise ValueError('Employee belongs to different farm: '+u['email'])
     continue
    c.execute('INSERT INTO owners(email,name,pw,role,farm_owner) VALUES(%s,%s,%s,%s,%s)',(u['email'],u['name'],hashed(u['password']),u['role'],oid))
  for t in tags:
   oid=owners[t['farm_code']]
   found=c.execute('SELECT owner FROM tags WHERE id=%s',(t['tag_id'],)).fetchone()
   if found:
    if found['owner']!=oid:raise ValueError('Tag belongs to another farm: '+t['tag_id'])
    continue
   c.execute('INSERT INTO tags(id,owner,name,lat,lon,battery,peace_sec,emergency_sec) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(t['tag_id'],oid,t['animal_number'],float(t['latitude']),float(t['longitude']),float(t['battery']),int(t['peace_sec']),int(t['emergency_sec'])))
 print('Imported CSV data: farms, owner, employees, and four tags. Existing telemetry preserved.')
if __name__=='__main__':main()
