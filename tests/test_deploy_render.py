import pytest
from scripts.deploy_render import payload,create_or_reuse,RenderAPI,REPO

def test_free_payload():
    p=payload('tea-example');assert p['branch']=='SU' and p['repo']==REPO
    d=p['serviceDetails'];assert d['plan']=='free' and d['runtime']=='python' and d['healthCheckPath']=='/health'
    assert '--workers 1' in d['envSpecificDetails']['startCommand']
    assert all('API_KEY' not in e['key'] for e in p['envVars'])

def test_missing_credential(monkeypatch):
    monkeypatch.delenv('RENDER_API_KEY',raising=False)
    with pytest.raises(RuntimeError,match='missing'):RenderAPI()

class FakeAPI:
    def __init__(self,services):self.services=services;self.calls=[]
    def listing(self,*args):return self.services
    def call(self,method,path,**kwargs):
        self.calls.append((method,path,kwargs));return {'service':{'id':'srv-new','name':'adidur','branch':'SU','serviceDetails':{'plan':'free','url':'https://example.onrender.com'}},'deployId':'dep-new'}

def existing(plan='free'):return {'id':'srv-existing','repo':REPO+'.git','branch':'SU','serviceDetails':{'plan':plan,'url':'https://example.onrender.com'}}
def test_reuse_no_create():
    api=FakeAPI([existing()]);r=create_or_reuse(api,'tea-example');assert r['service_id']=='srv-existing' and not api.calls

def test_create_explicit_free():
    api=FakeAPI([]);r=create_or_reuse(api,'tea-example');assert r['action']=='created_free_service' and r['deploy_id']=='dep-new'
    assert api.calls[0][2]['json']['serviceDetails']['plan']=='free'

@pytest.mark.parametrize('services',[[existing(),existing()],[existing('starter')]])
def test_no_duplicates_or_paid_plan(services):
    api=FakeAPI(services)
    with pytest.raises(RuntimeError):create_or_reuse(api,'tea-example')
    assert not api.calls
