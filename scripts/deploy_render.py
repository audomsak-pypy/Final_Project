"""Render free-service deployment. Credentials come from secure environment bindings only.
API schema: render-oss/cli ccd220c88de25433f1e77fe1e66a64adefa41c43,
pkg/client/types_gen.go (ServicePOST, ServiceAndDeploy, WebServiceDetailsPOST).
No automatic paid plan, destructive update, credential output or duplicate creation.
"""
from pathlib import Path
import argparse,json,os,re,sys
import requests
API='https://api.render.com/v1'
REPO='https://github.com/audomsak-pypy/Final_Project'
BUILD='pip install -r requirements.txt && python scripts/build_db.py --input Datasets --output data/adidur.db'
START='gunicorn app.app:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120'

def payload(owner):
    return {'type':'web_service','name':'adidur','ownerId':owner,'repo':REPO,'branch':'SU','autoDeployTrigger':'commit','envVars':[{'key':'PYTHON_VERSION','value':'3.12.14'}],'serviceDetails':{'runtime':'python','plan':'free','region':'singapore','healthCheckPath':'/health','envSpecificDetails':{'buildCommand':BUILD,'startCommand':START}}}

class RenderAPI:
    def __init__(self):
        token=os.environ.get('RENDER_API_KEY')
        if not token:raise RuntimeError('RENDER_API_KEY is missing. Add it securely in Environment settings; never send its value in chat.')
        self.session=requests.Session();self.session.headers.update({'Authorization':'Bearer '+token,'Accept':'application/json'})
    def call(self,method,path,**kwargs):
        try:response=self.session.request(method,API+path,timeout=45,**kwargs)
        except requests.RequestException as e:
            # Do not echo request headers or credential-bearing exception details.
            raise RuntimeError(f'Render API connection failed ({type(e).__name__}); check API network policy and secure binding.') from None
        if not response.ok:
            guidance={401:'Check Render API key binding.',403:'Check workspace authorization or network destination policy.',409:'Check existing services before retrying.',429:'Render rate limit; retry later.'}
            raise RuntimeError(f'Render API HTTP {response.status_code}. '+guidance.get(response.status_code,'Inspect the Render account deployment logs; no raw response is printed to protect credentials.'))
        return response.json()
    def listing(self,path,item,params=None):
        params={**(params or {}),'limit':100};found=[];seen=set()
        while True:
            entries=self.call('GET',path,params=params)
            if not isinstance(entries,list):raise RuntimeError('Unexpected Render list response; stopping before mutation.')
            found.extend(row[item] for row in entries if isinstance(row,dict) and item in row)
            if len(entries)<100:return found
            cursor=entries[-1].get('cursor')
            if not cursor or cursor in seen:raise RuntimeError('Incomplete Render pagination; refusing to create a possible duplicate.')
            seen.add(cursor);params['cursor']=cursor

def service_summary(service,deploy_id=None):
    details=service.get('serviceDetails') or {}
    return {'service_id':service.get('id'),'name':service.get('name'),'branch':service.get('branch'),'plan':details.get('plan'),'url':details.get('url'),'deploy_id':deploy_id}

def create_or_reuse(api,owner):
    services=api.listing('/services','service',{'ownerId':owner,'includePreviews':'false'})
    matches=[s for s in services if str(s.get('repo','')).removesuffix('.git').rstrip('/')==REPO and s.get('branch')=='SU']
    if len(matches)>1:raise RuntimeError('Multiple services already deploy this repository and branch; choose one in Render before continuing.')
    if matches:
        if (matches[0].get('serviceDetails') or {}).get('plan')!='free':raise RuntimeError('An existing matching service is not on the free plan. No duplicate or paid update was created.')
        return {'action':'reused_existing_service',**service_summary(matches[0])}
    result=api.call('POST','/services',json=payload(owner))
    if not isinstance(result,dict) or not isinstance(result.get('service'),dict):raise RuntimeError('Create response was unexpected. Inspect Render before retrying; do not create again blindly.')
    return {'action':'created_free_service',**service_summary(result['service'],result.get('deployId'))}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--plan',action='store_true',help='Print intended request without using credentials or creating a service')
    m.add_argument('--list-owners',action='store_true');m.add_argument('--create',action='store_true');m.add_argument('--status',metavar='SERVICE_ID')
    p.add_argument('--owner-id');args=p.parse_args(argv)
    if args.plan:print(json.dumps(payload(args.owner_id or '<Render workspace ID>'),ensure_ascii=False,indent=2));return 0
    try:
        api=RenderAPI()
        if args.status:
            if not re.fullmatch(r'srv-[A-Za-z0-9]+',args.status):raise RuntimeError('Invalid Render service ID.')
            service=api.call('GET','/services/'+args.status)
            deploys=api.call('GET','/services/'+args.status+'/deploys',params={'limit':1})
            latest=deploys[0].get('deploy',{}) if isinstance(deploys,list) and deploys else {}
            result={**service_summary(service),'deploy_id':latest.get('id'),'deploy_status':latest.get('status'),'public_health_verified':False}
        else:
            owners=api.listing('/owners','owner')
            if args.list_owners:result={'owners':[{'id':o['id'],'name':o.get('name'),'type':o.get('type')} for o in owners]}
            else:
                owner=args.owner_id
                if owner is None:
                    if len(owners)!=1:raise RuntimeError('Choose the Render workspace with --list-owners, then provide --owner-id. No service created.')
                    owner=owners[0]['id']
                if owner not in {o['id'] for o in owners}:raise RuntimeError('Selected workspace is not accessible with the current key.')
                result=create_or_reuse(api,owner)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except RuntimeError as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':sys.exit(main())
