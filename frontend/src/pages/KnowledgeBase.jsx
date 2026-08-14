import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchKnowledgeBase, fetchCategories } from '../services/api';

export default function KnowledgeBase() {
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const pageSize = 20;

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = { page, page_size: pageSize };
    if (search) params.search = search;
    if (categoryId) params.category_id = categoryId;

    fetchKnowledgeBase(params)
      .then(data => { setEntries(data.entries); setTotal(data.total); setError(null); })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [search, categoryId, page]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <div className="page-header">
        <h1>Knowledge Base ({total})</h1>
      </div>

      <div className="filter-bar">
        <input
          type="text"
          placeholder="Search resolved incidents..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
        />
        <select value={categoryId} onChange={e => { setCategoryId(e.target.value); setPage(1); }}>
          <option value="">All Categories</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      {error && <div className="error-state"><p>⚠️ {error}</p></div>}
      {loading ? (
        <div className="loading"><div className="loading-spinner"></div>Loading knowledge base...</div>
      ) : entries.length === 0 ? (
        <div className="empty-state"><p>No resolved incidents found matching your search.</p></div>
      ) : (
        <>
          {entries.map(e => (
            <div key={e.ticket_id} className="kb-entry" onClick={() => navigate(`/tickets/${e.ticket_id}`)} style={{ cursor: 'pointer' }}>
              <h4>
                <span style={{ color: 'var(--accent)', marginRight: '8px' }}>#{e.ticket_id}</span>
                {e.summary}
              </h4>
              <div className="kb-meta">
                {e.category_name && <span>{e.category_name}</span>}
              </div>
              <div className="kb-description">{e.description?.substring(0, 200)}{e.description?.length > 200 ? '...' : ''}</div>
              {e.resolution && (
                <div className="kb-resolution">
                  <strong>Resolution:</strong> {e.resolution}
                </div>
              )}
              {e.comment_highlights?.length > 0 && (
                <div className="kb-comments">
                  {e.comment_highlights.slice(0, 2).map((ch, i) => (
                    <div key={i} className="kb-comment">💬 {ch}</div>
                  ))}
                </div>
              )}
            </div>
          ))}
          {totalPages > 1 && (
            <div className="pagination">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
              <span>Page {page} of {totalPages}</span>
              <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next →</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
