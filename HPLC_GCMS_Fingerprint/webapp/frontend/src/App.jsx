import { useMemo, useState } from 'react';
import { useEffect } from 'react';

const initialForm = {
  sampleId: 'FTIR_S001',
  projectArea: 'marine-biotech',
  sourceType: 'FTIR',
  notes: 'Ocean-derived biomass screening',
};

const sourceHighlights = [
  {
    title: 'FTIR spectral insight',
    body: 'Rapid spectral profiling for biomolecule fingerprints and species-level trends.',
  },
  {
    title: 'HPLC chromatographic signals',
    body: 'Retention-time patterns that capture pigment and metabolite distributions.',
  },
  {
    title: 'GCMS metabolomic signatures',
    body: 'Mass-fragment evidence for compound identification and comparative chemistry.',
  },
];

const metrics = [
  { label: 'Sources', value: '3' },
  { label: 'Focus', value: 'Marine biotech' },
  { label: 'Mode', value: 'Low resource' },
];

function App() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadId, setUploadId] = useState(null);
  const [imputeMethod, setImputeMethod] = useState('median');
  const [scaleMethod, setScaleMethod] = useState('standard');
  const [preparedPreview, setPreparedPreview] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [trainingJob, setTrainingJob] = useState(null);
  const [trainingProgress, setTrainingProgress] = useState({ percent: 0, status: 'idle' });
  const apiBase = useMemo(() => import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000', []);

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const response = await fetch(`${apiBase}/api/pipeline-status`);
        if (!response.ok) {
          return;
        }
        const data = await response.json();
        setPipelineStatus(data);
      } catch {
        setPipelineStatus(null);
      }
    };

    loadStatus();
  }, [apiBase]);

  useEffect(() => {
    let es = null;
    if (trainingJob && trainingJob.job_id) {
      es = new EventSource(`${apiBase}/api/train-stream/${trainingJob.job_id}`);
      es.onmessage = (e) => {
        try {
          const d = JSON.parse(e.data);
          setTrainingProgress({ percent: d.percent || 0, status: d.status || 'running' });
        } catch {}
      };
      es.onerror = () => {
        // close on error
        try { es.close(); } catch {}
      };
    }
    return () => { if (es) try { es.close(); } catch {} };
  }, [apiBase, trainingJob]);

  const handlePredict = async (event) => {
    event.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${apiBase}/api/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sample_id: form.sampleId,
          project_area: form.projectArea,
          source_type: form.sourceType,
          payload: { notes: form.notes },
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({
        sample_id: form.sampleId,
        source_type: form.sourceType,
        project_area: form.projectArea,
        predicted_label: 'Backend unavailable',
        confidence: 0,
        summary: error.message,
        resource_mode: 'offline demo',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStartTraining = async (kind = 'dl') => {
    try {
      const body = { kind, epochs: 50, batch_size: 16 };
      if (uploadId && preparedPreview) body.dataset_id = uploadId;

      const resp = await fetch(`${apiBase}/api/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      if (data.job_id) {
        setTrainingJob(data);
        setTrainingProgress({ percent: 0, status: 'queued' });
      }
    } catch (err) {
      setTrainingProgress({ percent: 0, status: 'error' });
    }
  };

  const handleUpload = async (event) => {
    event.preventDefault();
    if (!selectedFile) {
      setUploadResult({ summary: 'Choose a CSV file first.' });
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('source_type', form.sourceType);

      const response = await fetch(`${apiBase}/api/upload-file`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const data = await response.json();
      setUploadResult(data);
      setUploadId(data.upload_id);
      setPreparedPreview(null);
    } catch (error) {
      setUploadResult({ summary: error.message });
    } finally {
      setUploading(false);
    }
  };

  const handlePrepare = async () => {
    if (!uploadId) return;
    setUploading(true);
    try {
      const resp = await fetch(`${apiBase}/api/prepare-dataset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ upload_id: uploadId, impute: imputeMethod, scale: scaleMethod }),
      });
      const data = await resp.json();
      if (!data.error) {
        setPreparedPreview(data.preview || null);
      }
    } catch (err) {
      // noop
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />

      <main className="app-grid">
        <section className="hero-card glass-card">
          <div className="eyebrow">Marine Biotechnology + Vision</div>
          <h1>Reveal bio-signatures with a calm, scientific interface.</h1>
          <p className="hero-copy">
            A polished starter for your prediction pipeline with a marine-inspired visual language,
            lightweight backend calls, and a future-ready React + FastAPI structure.
          </p>

          <div className="metric-row">
            {metrics.map((metric) => (
              <article className="metric-card" key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </article>
            ))}
          </div>

          <div className="highlight-grid">
            {sourceHighlights.map((item) => (
              <article className="feature-card" key={item.title}>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>

          <section className="upload-card">
            <h2>Step 1 — Upload: real sample sheet</h2>
            <p>
              Upload a CSV containing your HPLC / GC-MS / FTIR measurements. The backend will
              validate, report non-numeric/missing cells and let you prepare the data for training.
            </p>

            <form className="upload-form" onSubmit={handleUpload}>
              <label>
                <span>CSV file</span>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
                />
              </label>

              <button type="submit" disabled={uploading} className="secondary-button">
                {uploading ? 'Inspecting...' : 'Inspect upload'}
              </button>
            </form>

            {uploadId && (
              <div style={{ marginTop: 12 }}>
                <h4>Step 2 — Prepare dataset</h4>
                <label>
                  <span>Impute</span>
                  <select value={imputeMethod} onChange={(e) => setImputeMethod(e.target.value)}>
                    <option value="median">Median</option>
                    <option value="mean">Mean</option>
                    <option value="zero">Zero</option>
                  </select>
                </label>

                <label>
                  <span>Scale</span>
                  <select value={scaleMethod} onChange={(e) => setScaleMethod(e.target.value)}>
                    <option value="standard">Standard</option>
                    <option value="minmax">MinMax</option>
                    <option value="none">None</option>
                  </select>
                </label>

                <div style={{ marginTop: 8 }}>
                  <button onClick={handlePrepare} disabled={uploading} className="secondary-button">{uploading ? 'Preparing...' : 'Prepare dataset'}</button>
                </div>

                {preparedPreview && (
                  <div className="preview">
                    <h5>Prepared preview</h5>
                    <pre style={{ maxHeight: 160, overflow: 'auto' }}>{JSON.stringify(preparedPreview, null, 2)}</pre>
                    <p className="muted small">If this looks correct, start training in Step 3.</p>
                  </div>
                )}
              </div>
            )}

            {uploadResult && (
              <div className="upload-result">
                <div className="result-meta">
                  <span>{uploadResult.detected_source || 'Upload'}</span>
                  <span>{uploadResult.filename || 'No file'}</span>
                </div>
                <p>{uploadResult.summary}</p>
                {uploadResult.rows !== undefined && (
                  <div className="upload-stats">
                    <strong>{uploadResult.rows}</strong>
                    <span>rows</span>
                    <strong>{uploadResult.columns}</strong>
                    <span>columns</span>
                    <strong>{uploadResult.non_numeric_cells}</strong>
                    <span>non-numeric cells</span>
                  </div>
                )}
              </div>
            )}
          </section>
        </section>

        <section className="panel-card glass-card">
          <div className="panel-heading">
            <span className="panel-kicker">Prediction Console</span>
            <h2>Submit a sample</h2>
          </div>

          <form className="prediction-form" onSubmit={handlePredict}>
            <label>
              <span>Sample ID</span>
              <input
                value={form.sampleId}
                onChange={(event) => updateField('sampleId', event.target.value)}
                placeholder="FTIR_S001"
              />
            </label>

            <label>
              <span>Project area</span>
              <select
                value={form.projectArea}
                onChange={(event) => updateField('projectArea', event.target.value)}
              >
                <option value="marine-biotech">Marine biotech</option>
                <option value="vision">Vision</option>
                <option value="research-demo">Research demo</option>
              </select>
            </label>

            <label>
              <span>Source type</span>
              <select
                value={form.sourceType}
                onChange={(event) => updateField('sourceType', event.target.value)}
              >
                <option value="FTIR">FTIR</option>
                <option value="HPLC">HPLC</option>
                <option value="GCMS">GCMS</option>
              </select>
            </label>

            <label>
              <span>Notes</span>
              <textarea
                rows="4"
                value={form.notes}
                onChange={(event) => updateField('notes', event.target.value)}
                placeholder="Optional context for the sample"
              />
            </label>

            <button type="submit" disabled={loading}>
              {loading ? 'Analyzing...' : 'Run prediction'}
            </button>
          </form>

          {result && (
            <section className="result-card">
              <div className="result-meta">
                <span>{result.source_type}</span>
                <span>{result.resource_mode}</span>
              </div>
              <h3>{result.predicted_label}</h3>
              <p>{result.summary}</p>
              <div className="result-confidence">
                <strong>{Math.round((result.confidence || 0) * 100)}%</strong>
                <span>confidence</span>
              </div>
            </section>
          )}

          {pipelineStatus && pipelineStatus.available && (
            <section className="pipeline-card">
              <h3>Latest pipeline artifacts</h3>
              <p>{pipelineStatus.summary}</p>

              {pipelineStatus.latest_predictions?.length > 0 && (
                <div className="prediction-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Sample</th>
                        <th>Source</th>
                        <th>Species</th>
                        <th>Phylum</th>
                        <th>Confidence %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pipelineStatus.latest_predictions.map((row) => (
                        <tr key={`${row.sample_id}-${row.data_source}`}>
                          <td>{row.sample_id}</td>
                          <td>{row.data_source}</td>
                          <td>{row.predicted_species}</td>
                          <td>{row.predicted_phylum}</td>
                          <td>{row.confidence_pct?.toFixed ? row.confidence_pct.toFixed(2) : row.confidence_pct}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {pipelineStatus.insights_excerpt && (
                <pre className="insight-excerpt">{pipelineStatus.insights_excerpt}</pre>
              )}
            </section>
          )}

          <section className="training-card">
            <h3>Step 3 — Train model</h3>
            <p className="muted">Start training locally and watch live progress. Choose ML for quick baselines or DL for neural models.</p>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <button onClick={() => handleStartTraining('dl')}>Start DL training</button>
              <button onClick={() => handleStartTraining('ml')}>Start ML training</button>
            </div>

            <div style={{ marginTop: 8 }}>
              <div style={{ background: '#0b2630', borderRadius: 8, overflow: 'hidden', height: 18 }}>
                <div style={{ width: `${trainingProgress.percent}%`, height: '100%', background: 'linear-gradient(90deg,#62d0ff,#7ef0c2)' }} />
              </div>
              <div style={{ marginTop: 8 }} className="small">Status: {trainingProgress.status} — {trainingProgress.percent}%</div>
              {trainingJob && <div className="small">Job: {trainingJob.job_id}</div>}
            </div>
          </section>
        </section>
      </main>
    </div>
  );
}

export default App;
