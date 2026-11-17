import { useEffect, useRef, useState } from 'react';
import { api, openDocumentFile } from './api.js';

// ─── Icons (inline SVG, no deps) ──────────────────────────────────────────────
const Icon = {
  Logo: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
    </svg>
  ),
  Search: () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
  ),
  Upload: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
    </svg>
  ),
  Trash: () => (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
    </svg>
  ),
  ArrowLeft: () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
    </svg>
  ),
  FileText: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
    </svg>
  ),
  Send: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  ),
  Close: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  ),
  Globe: () => (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>
  ),
  Lock: () => (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
  ),
  Sparkles: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5z"/><path d="M5 3l.75 2.25L8 6l-2.25.75L5 9l-.75-2.25L2 6l2.25-.75z"/><path d="M19 15l.75 2.25L22 18l-2.25.75L19 21l-.75-2.25L16 18l2.25-.75z"/>
    </svg>
  ),
  Chat: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
};

// ─── Auth ──────────────────────────────────────────────────────────────────────
function Auth({ onAuthenticated }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await api(`/auth/${mode}`, { method: 'POST', body: form });
      onAuthenticated(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function fillDemo(email, pass) {
    setForm({ ...form, email, password: pass });
  }

  return (
    <main className="auth-layout">
      <div className="auth-left">
        <div className="auth-brand">
          <span className="auth-brand-icon"><Icon.Logo /></span>
          <span className="auth-brand-name">TemaniResearch</span>
        </div>
        <h1 className="auth-headline">
          Eksplorasi Jurnal Ilmiah<br />dengan Kecerdasan Buatan
        </h1>
        <p className="auth-body">
          Platform riset berbasis <strong>Retrieval-Augmented Generation (RAG)</strong> yang memungkinkan Anda bertanya langsung kepada dokumen penelitian dan mendapatkan jawaban dengan sitasi halaman yang akurat.
        </p>
        <div className="auth-features">
          <div className="auth-feature-item">
            <span className="feature-dot" />
            <span>Gemini Flash Lite — Respons cepat &amp; hemat kuota</span>
          </div>
          <div className="auth-feature-item">
            <span className="feature-dot" />
            <span>Embedding semantik gemini-embedding-001</span>
          </div>
          <div className="auth-feature-item">
            <span className="feature-dot" />
            <span>Sitasi halaman akurat dari isi PDF</span>
          </div>
          <div className="auth-feature-item">
            <span className="feature-dot" />
            <span>Repository publik &amp; perpustakaan pribadi</span>
          </div>
        </div>
        <p className="auth-course-tag">SIBK 2026 · Sistem Informasi · Semester 3</p>
      </div>

      <div className="auth-right">
        <form className="auth-form" onSubmit={submit}>
          <div className="auth-form-header">
            <h2>{mode === 'login' ? 'Masuk ke Akun' : 'Buat Akun Baru'}</h2>
            <p>{mode === 'login' ? 'Lanjutkan sesi penelitian Anda.' : 'Daftar untuk mulai mengunggah jurnal.'}</p>
          </div>

          {mode === 'register' && (
            <div className="form-field">
              <label>Nama Lengkap</label>
              <input
                required
                placeholder="Contoh: Mohamad Ardiatama"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
          )}

          <div className="form-field">
            <label>Email</label>
            <input
              type="email"
              required
              placeholder="nama@temaniresearch.ac.id"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </div>

          <div className="form-field">
            <label>Password</label>
            <input
              type="password"
              minLength="6"
              required
              placeholder="Minimal 6 karakter"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>

          {error && <div className="form-error">{error}</div>}

          <button className="btn-primary" disabled={loading}>
            {loading ? 'Memproses...' : mode === 'login' ? 'Masuk' : 'Daftar'}
          </button>

          <button
            type="button"
            className="btn-link"
            onClick={() => { setError(''); setMode(mode === 'login' ? 'register' : 'login'); }}
          >
            {mode === 'login' ? 'Belum punya akun? Daftar di sini' : 'Sudah punya akun? Masuk'}
          </button>

          <div className="demo-section">
            <span className="demo-label">Akun demo</span>
            <div className="demo-row">
              <button type="button" className="btn-demo" onClick={() => fillDemo('admin@temaniresearch.ac.id', 'Admin123!')}>
                Admin
              </button>
              <button type="button" className="btn-demo" onClick={() => fillDemo('mahasiswa@temaniresearch.ac.id', 'User123!')}>
                Mahasiswa
              </button>
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}

// ─── Upload Modal ──────────────────────────────────────────────────────────────
function UploadModal({ token, user, onClose, onUploaded }) {
  const [form, setForm] = useState({
    title: '',
    authors: '',
    year: new Date().getFullYear(),
    category: 'Informatika',
    description: '',
    keywords: '',
    visibility: user.role === 'admin' ? 'public' : 'private',
  });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    if (!file) { setError('Pilih file PDF terlebih dahulu.'); return; }
    setLoading(true);
    setError('');
    const data = new FormData();
    Object.entries(form).forEach(([key, val]) => data.append(key, val));
    data.append('file', file);
    try {
      await api('/documents/upload', { token, method: 'POST', formData: data });
      onUploaded();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <h3>{user.role === 'admin' ? 'Unggah Dokumen Publik' : 'Unggah Jurnal Pribadi'}</h3>
            <p>{user.role === 'admin' ? 'Dokumen publik dapat diakses seluruh pengguna.' : 'Dokumen privat hanya bisa diakses oleh Anda.'}</p>
          </div>
          <button className="btn-icon-close" onClick={onClose}><Icon.Close /></button>
        </div>

        <form onSubmit={submit} className="modal-form">
          <div className="form-field">
            <label>Judul Dokumen <span className="req">*</span></label>
            <input
              required
              placeholder="Contoh: Analisis Kinerja Algoritma RAG pada PDF Multilingual"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </div>

          <div className="form-row-2">
            <div className="form-field">
              <label>Penulis</label>
              <input placeholder="Contoh: Hibrizi, dkk." value={form.authors} onChange={(e) => setForm({ ...form, authors: e.target.value })} />
            </div>
            <div className="form-field">
              <label>Tahun Terbit</label>
              <input type="number" min="1950" max="2030" value={form.year} onChange={(e) => setForm({ ...form, year: e.target.value })} />
            </div>
          </div>

          <div className="form-row-2">
            <div className="form-field">
              <label>Kategori</label>
              <input placeholder="AI, Sistem Informasi, NLP..." value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
            </div>
            {user.role === 'admin' ? (
              <div className="form-field">
                <label>Visibilitas</label>
                <select value={form.visibility} onChange={(e) => setForm({ ...form, visibility: e.target.value })}>
                  <option value="public">Publik</option>
                  <option value="private">Privat</option>
                </select>
              </div>
            ) : (
              <div className="form-field">
                <label>Kepemilikan</label>
                <input disabled value="Personal Library (Privat)" />
              </div>
            )}
          </div>

          <div className="form-field">
            <label>Deskripsi / Abstrak Singkat</label>
            <textarea rows="3" placeholder="Ringkasan singkat mengenai cakupan dokumen..." value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>

          <div className="form-field">
            <label>File PDF <span className="req">*</span></label>
            <input type="file" accept="application/pdf,.pdf" required onChange={(e) => setFile(e.target.files[0])} />
          </div>

          {error && <div className="form-error">{error}</div>}

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Batal</button>
            <button className="btn-primary" disabled={loading}>
              <Icon.Upload />
              {loading ? 'Mengindeks...' : 'Unggah & Indeks'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Library ───────────────────────────────────────────────────────────────────
function Library({ token, user, selected, setSelected, refreshFlag, onTriggerUpload, onRefresh }) {
  const [documents, setDocuments] = useState([]);
  const [query, setQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    let url = `/documents?q=${encodeURIComponent(query)}`;
    if (activeTab === 'public') url += '&visibility=public';
    if (activeTab === 'private') url += '&visibility=private';
    api(url, { token })
      .then((res) => { setDocuments(res.documents || []); setError(''); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token, query, activeTab, refreshFlag]);

  async function handleDelete(docId, title, e) {
    e.stopPropagation();
    if (!window.confirm(`Hapus dokumen "${title}" beserta indeks vektornya?`)) return;
    try {
      await api(`/documents/${docId}`, { token, method: 'DELETE' });
      onRefresh();
    } catch (err) {
      alert(`Gagal menghapus: ${err.message}`);
    }
  }

  const TABS = [
    { key: 'all', label: 'Semua' },
    { key: 'public', label: 'Publik' },
    { key: 'private', label: 'Pribadi' },
  ];

  return (
    <section className="library">
      <div className="library-header">
        <div className="library-title-block">
          <span className="section-label">REPOSITORY</span>
          <h1>Koleksi Dokumen</h1>
        </div>
        <div className="library-actions">
          <div className="search-box">
            <Icon.Search />
            <input
              placeholder="Cari judul, penulis, kategori..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <button className="btn-primary" onClick={onTriggerUpload}>
            <Icon.Upload />
            {user.role === 'admin' ? 'Unggah Dokumen' : 'Unggah Jurnal'}
          </button>
        </div>
      </div>

      <div className="tab-bar">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`tab-item ${activeTab === t.key ? 'active' : ''}`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
            {t.key === 'all' && <span className="tab-count">{documents.length}</span>}
          </button>
        ))}
      </div>

      {error && <div className="form-error">{error}</div>}

      {loading ? (
        <div className="state-box">
          <p>Memuat koleksi...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="state-box">
          <p>Belum ada dokumen yang sesuai filter.</p>
          <button className="btn-secondary" onClick={onTriggerUpload}>Unggah Dokumen PDF</button>
        </div>
      ) : (
        <div className="doc-grid">
          {documents.map((doc) => {
            const canDelete = user.role === 'admin' || doc.uploaded_by === user.id;
            return (
              <div
                key={doc.id}
                className={`doc-card ${selected?.id === doc.id ? 'is-selected' : ''} ${doc.status !== 'ready' ? 'is-disabled' : ''}`}
                onClick={() => doc.status === 'ready' && setSelected(doc)}
              >
                <div className="doc-card-top">
                  <span className={`badge badge-vis-${doc.visibility}`}>
                    {doc.visibility === 'public' ? <><Icon.Globe /> Publik</> : <><Icon.Lock /> Pribadi</>}
                  </span>
                  <span className={`badge badge-status-${doc.status}`}>
                    {doc.status === 'ready' ? 'Siap' : doc.status === 'processing' ? 'Proses' : 'Gagal'}
                  </span>
                </div>

                <h3 className="doc-card-title">{doc.title}</h3>
                <p className="doc-card-authors">
                  {doc.authors || 'Penulis tidak dicantumkan'}{doc.year ? ` · ${doc.year}` : ''}
                </p>

                <div className="doc-card-footer">
                  <span className="doc-card-meta">
                    {doc.category || 'Umum'} · {doc.page_count || '?'} hlm
                  </span>
                  {canDelete && (
                    <button className="btn-icon-trash" title="Hapus dokumen" onClick={(e) => handleDelete(doc.id, doc.title, e)}>
                      <Icon.Trash />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

// ─── Document Workspace ────────────────────────────────────────────────────────
function DocumentWorkspace({ token, user, document, onClose }) {
  const [summary, setSummary] = useState('');
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loadingAction, setLoadingAction] = useState('');
  const [error, setError] = useState('');
  const chatEndRef = useRef(null);

  useEffect(() => {
    setSummary('');
    setMessages([]);
    setError('');
    api(`/documents/${document.id}/chats`, { token })
      .then((res) => setMessages(res.messages || []))
      .catch((err) => setError(err.message));
    api(`/documents/${document.id}`, { token })
      .then((res) => { if (res.document?.summary) setSummary(res.document.summary); })
      .catch(() => {});
  }, [token, document.id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loadingAction]);

  async function requestSummary() {
    setLoadingAction('summary');
    setError('');
    try {
      const res = await api(`/documents/${document.id}/summary`, { token });
      setSummary(res.summary);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingAction('');
    }
  }

  async function askQuestion(event) {
    event.preventDefault();
    if (!question.trim()) return;
    const q = question;
    setQuestion('');
    setLoadingAction('chat');
    setError('');
    try {
      const res = await api(`/documents/${document.id}/chat`, {
        token, method: 'POST', body: { question: q },
      });
      setMessages((prev) => [
        ...prev,
        { id: res.chat_id, question: q, answer: res.answer, sources: res.sources, created_at: new Date().toISOString() },
      ]);
    } catch (err) {
      setError(err.message);
      setQuestion(q);
    } finally {
      setLoadingAction('');
    }
  }

  async function openPdf() {
    try {
      await openDocumentFile(document.id, token);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="workspace">
      {/* Top bar */}
      <div className="workspace-topbar">
        <button className="btn-back" onClick={onClose}>
          <Icon.ArrowLeft /> Kembali
        </button>
        <div className="workspace-topbar-right">
          <span className={`badge badge-vis-${document.visibility}`}>
            {document.visibility === 'public' ? <><Icon.Globe /> Publik</> : <><Icon.Lock /> Pribadi</>}
          </span>
          <span className="badge badge-cat">{document.category || 'Umum'}</span>
          {document.year && <span className="badge badge-cat">{document.year}</span>}
          <button className="btn-secondary" onClick={openPdf}>
            <Icon.FileText /> Buka PDF
          </button>
        </div>
      </div>

      {/* Document title block */}
      <div className="workspace-title-block">
        <h1>{document.title}</h1>
        <p>Oleh: {document.authors || 'Penulis tidak dicantumkan'}</p>
      </div>

      {error && <div className="form-error">{error}</div>}

      {/* Two-panel layout */}
      <div className="workspace-panels">
        {/* Left — Summary */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-header-title">
              <Icon.Sparkles />
              <span>Ringkasan AI</span>
            </div>
            <button
              className="btn-action"
              onClick={requestSummary}
              disabled={loadingAction === 'summary'}
            >
              {loadingAction === 'summary' ? 'Menganalisis...' : summary ? 'Perbarui' : 'Buat Ringkasan'}
            </button>
          </div>

          <div className="panel-body summary-body">
            {summary ? (
              <div className="summary-text">
                {summary.split('\n').map((line, i) => <p key={i}>{line}</p>)}
              </div>
            ) : (
              <div className="panel-empty">
                <p>Ringkasan belum dibuat.</p>
                <button className="btn-secondary" onClick={requestSummary} disabled={loadingAction === 'summary'}>
                  Generate Ringkasan
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right — Chat */}
        <div className="panel panel-chat">
          <div className="panel-header">
            <div className="panel-header-title">
              <Icon.Chat />
              <span>Tanya Jawab RAG</span>
            </div>
            <span className="panel-header-hint">Jawaban merujuk isi dokumen</span>
          </div>

          <div className="chat-history">
            {messages.length === 0 ? (
              <div className="panel-empty">
                <p>Belum ada diskusi.</p>
                <small>Ketik pertanyaan tentang metodologi, hasil, atau konsep dalam dokumen.</small>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="chat-message">
                  <div className="bubble-user">{msg.question}</div>
                  <div className="bubble-ai">
                    <div className="bubble-ai-label">TemaniResearch AI</div>
                    <div className="bubble-ai-content">
                      {msg.answer.split('\n').map((l, idx) => <p key={idx}>{l}</p>)}
                    </div>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="citations">
                        <span className="citations-label">Sumber halaman</span>
                        <div className="citations-badges">
                          {msg.sources.map((s, idx) => (
                            <span key={idx} className="citation-badge" title={s.snippet || ''}>
                              Hlm. {s.page_number}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {loadingAction === 'chat' && (
              <div className="chat-typing">Mencari referensi &amp; menyusun jawaban...</div>
            )}
            <div ref={chatEndRef} />
          </div>

          <form className="chat-input" onSubmit={askQuestion}>
            <input
              placeholder="Ajukan pertanyaan tentang dokumen ini..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loadingAction === 'chat'}
            />
            <button className="btn-send" disabled={loadingAction === 'chat' || !question.trim()}>
              <Icon.Send />
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}

// ─── App Shell ─────────────────────────────────────────────────────────────────
export default function App() {
  const [session, setSession] = useState(() => {
    try { return JSON.parse(localStorage.getItem('temaniresearch-session')); }
    catch { return null; }
  });
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [refreshFlag, setRefreshFlag] = useState(0);

  function handleAuthenticated(data) {
    const next = { token: data.token, user: data.user };
    localStorage.setItem('temaniresearch-session', JSON.stringify(next));
    setSession(next);
  }

  function handleLogout() {
    localStorage.removeItem('temaniresearch-session');
    setSession(null);
    setSelectedDoc(null);
  }

  if (!session) return <Auth onAuthenticated={handleAuthenticated} />;

  return (
    <div className="shell">
      <header className="topnav">
        <div className="topnav-brand">
          <span className="topnav-icon"><Icon.Logo /></span>
          <span className="topnav-name">TemaniResearch</span>
        </div>
        <div className="topnav-right">
          <span className="topnav-user">
            {session.user.name}
            <span className={`role-pill role-${session.user.role}`}>
              {session.user.role === 'admin' ? 'Admin' : 'Mahasiswa'}
            </span>
          </span>
          <button className="btn-logout" onClick={handleLogout}>Keluar</button>
        </div>
      </header>

      <main className="main">
        {selectedDoc ? (
          <DocumentWorkspace
            token={session.token}
            user={session.user}
            document={selectedDoc}
            onClose={() => setSelectedDoc(null)}
          />
        ) : (
          <Library
            token={session.token}
            user={session.user}
            selected={selectedDoc}
            setSelected={setSelectedDoc}
            refreshFlag={refreshFlag}
            onTriggerUpload={() => setShowUpload(true)}
            onRefresh={() => setRefreshFlag((v) => v + 1)}
          />
        )}
      </main>

      {showUpload && (
        <UploadModal
          token={session.token}
          user={session.user}
          onClose={() => setShowUpload(false)}
          onUploaded={() => setRefreshFlag((v) => v + 1)}
        />
      )}
    </div>
  );
}
