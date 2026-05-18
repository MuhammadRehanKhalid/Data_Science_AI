from fastapi.testclient import TestClient
from webapp.backend import main
import time

client = TestClient(main.app)

csv = 'sample_id,species,replicate,activity_MeOH\nS1,Chlorella vulgaris,1,0.7\nS2,Chlorella vulgaris,1,0.8\nS3,Prorocentrum lima,1,0.6\n'
resp = client.post('/api/upload-file', files={'file':('test.csv', csv, 'text/csv')}, data={'source_type':'HPLC'})
print('upload', resp.status_code, resp.json())
uid = resp.json().get('upload_id')

resp2 = client.post('/api/prepare-dataset', json={'upload_id': uid, 'impute': 'median', 'scale': 'standard'})
print('prepare', resp2.status_code, resp2.json())

resp3 = client.post('/api/train', json={'kind':'ml','epochs':5,'batch_size':4,'dataset_id': uid})
print('train', resp3.status_code, resp3.json())
job = resp3.json().get('job_id')

start = time.time()
while True:
    s = client.get(f'/api/train-status/{job}')
    print('status', s.status_code, s.json())
    if s.json().get('status') in ('finished','error'):
        break
    if time.time() - start > 60:
        print('timeout')
        break
    time.sleep(1.0)

print('done')
