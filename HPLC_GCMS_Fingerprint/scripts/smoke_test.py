import requests, json, time

url='http://127.0.0.1:8000'

# Ensure test_upload.csv exists
with open('test_upload.csv','w',encoding='utf-8') as f:
    f.write('sample_id,species,replicate,activity_MeOH\nS1,Chlorella vulgaris,1,0.7\nS2,Chlorella vulgaris,1,0.8\n')

files={'file':('test_upload.csv', open('test_upload.csv','rb'), 'text/csv')}
resp = requests.post(url + '/api/upload-file', files=files, data={'source_type':'HPLC'})
print('UPLOAD', resp.status_code, resp.text)
if resp.status_code != 200:
    raise SystemExit('Upload failed')

upload_id = resp.json().get('upload_id')
print('upload_id', upload_id)

resp2 = requests.post(url + '/api/prepare-dataset', json={'upload_id': upload_id, 'impute': 'median', 'scale': 'standard'})
print('PREPARE', resp2.status_code, resp2.text)

resp3 = requests.post(url + '/api/train', json={'kind':'ml', 'epochs':2, 'batch_size':4, 'dataset_id': upload_id})
print('TRAIN', resp3.status_code, resp3.text)

job = resp3.json()
job_id = job.get('job_id')
if job_id:
    time.sleep(1)
    s = requests.get(url + f'/api/train-status/{job_id}')
    print('STATUS', s.status_code, s.text)
else:
    print('No job id returned')
