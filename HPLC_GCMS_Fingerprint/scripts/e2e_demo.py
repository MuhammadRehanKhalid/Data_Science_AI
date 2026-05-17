import requests, time, json, os

BASE='http://127.0.0.1:8000'
CSV='test_upload.csv'

# create a small CSV
with open(CSV,'w',encoding='utf-8') as f:
    f.write('sample_id,species,replicate,activity_MeOH\n')
    f.write('S1,Chlorella vulgaris,1,0.7\n')
    f.write('S2,Chlorella vulgaris,1,0.8\n')
    f.write('S3,Prorocentrum lima,1,0.6\n')

print('Uploading', CSV)
with open(CSV,'rb') as fh:
    files={'file':(CSV, fh, 'text/csv')}
    r = requests.post(BASE + '/api/upload-file', files=files, data={'source_type':'HPLC'})
print('upload status', r.status_code)
print(r.text)
if r.status_code != 200:
    raise SystemExit('upload failed')
uid = r.json().get('upload_id')

print('Preparing dataset', uid)
r2 = requests.post(BASE + '/api/prepare-dataset', json={'upload_id': uid, 'impute':'median', 'scale':'standard'})
print('prepare', r2.status_code)
print(r2.text)
if r2.status_code != 200:
    raise SystemExit('prepare failed')

print('Starting ML training using prepared dataset')
r3 = requests.post(BASE + '/api/train', json={'kind':'ml','epochs':5,'batch_size':4,'dataset_id':uid})
print('train start', r3.status_code, r3.text)
if r3.status_code != 200:
    raise SystemExit('train start failed')
job = r3.json().get('job_id')
print('job id', job)

# Poll status until finished
start = time.time()
while True:
    s = requests.get(BASE + f'/api/train-status/{job}')
    if s.status_code != 200:
        print('status err', s.status_code, s.text)
        break
    data = s.json()
    print('status:', data)
    if data.get('status') in ('finished','error'):
        break
    if time.time() - start > 120:
        print('timeout waiting for job')
        break
    time.sleep(1.0)

print('Done. Fetching stream summary...')
stream = requests.get(BASE + f'/api/train-stream/{job}', stream=True)
for line in stream.iter_lines():
    if line:
        try:
            text = line.decode('utf-8')
        except Exception:
            text = str(line)
        print('sse:', text)

print('E2E demo complete')
