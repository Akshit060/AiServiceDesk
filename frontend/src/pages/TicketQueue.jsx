import { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { fetchTickets, fetchCategories, fetchAgents } from '../services/api';

export default function TicketQueue() {
  const { currentAgent } = useOutletContext();
  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categories, setCategories] = useState([]);
  const [agents, setAgents] = useState([]);
  const navigate = useNavigate();

  // Filters
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [agentId, setAgentId] = useState('');
  const [unassigned, setUnassigned] = useState(false);
  const [sort, setSort] = useState('newest');
  const pageSize = 25;

  useEffect(() => {
    Promise.all([fetchCategories(), fetchAgents()])
      .then(([cats, agts]) => { setCategories(cats); setAgents(agts); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = { page, page_size: pageSize, sort };
    if (search) params.search = search;
    if (status) params.status = status;
    if (priority) params.priority = priority;
    if (categoryId) params.category_id = categoryId;
    if (agentId) params.agent_id = agentId;
    if (unassigned) params.unassigned = true;

    fetchTickets(params)
      .then(data => { setTickets(data.tickets); setTotal(data.total); setError(null); })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [search, status, priority, categoryId, agentId, unassigned, sort, page]);

  const totalPages = Math.ceil(total / pageSize);

  const formatDate = (d) => {
    if (!d) return '-';
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div>
      <div className="page-header">
        <h1>Ticket Queue ({total})</h1>
        <button className="btn btn-primary" onClick={() => navigate('/tickets/new')}>+ New Ticket</button>
      </div>

      <div className="filter-bar">
        <input
          type="text"
          placeholder="Search tickets..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
        />
        <select value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
        </select>
        <select value={priority} onChange={e => { setPriority(e.target.value); setPage(1); }}>
          <option value="">All Priorities</option>
          <option value="P1">P1 - Critical</option>
          <option value="P2">P2 - High</option>
          <option value="P3">P3 - Medium</option>
          <option value="P4">P4 - Low</option>
        </select>
        <select value={categoryId} onChange={e => { setCategoryId(e.target.value); setPage(1); }}>
          <option value="">All Categories</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={agentId} onChange={e => { setAgentId(e.target.value); setUnassigned(false); setPage(1); }}>
          <option value="">All Agents</option>
          {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
          <input type="checkbox" checked={unassigned} onChange={e => { setUnassigned(e.target.checked); if (e.target.checked) setAgentId(''); setPage(1); }} />
          Unassigned
        </label>
        <select value={sort} onChange={e => { setSort(e.target.value); setPage(1); }}>
          <option value="newest">Newest First</option>
          <option value="oldest">Oldest First</option>
          <option value="priority">By Priority</option>
        </select>
        {currentAgent && (
          <button className="btn btn-sm btn-secondary" onClick={() => { setAgentId(currentAgent.id); setUnassigned(false); setPage(1); }}>
            My Tickets
          </button>
        )}
      </div>

      {error && <div className="error-state"><p>⚠️ {error}</p></div>}
      {loading ? (
        <div className="loading"><div className="loading-spinner"></div>Loading tickets...</div>
      ) : tickets.length === 0 ? (
        <div className="empty-state"><p>No tickets found matching your filters.</p></div>
      ) : (
        <>
          <div className="card" style={{ overflow: 'auto' }}>
            <table className="ticket-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Category</th>
                  <th>Assigned To</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map(t => (
                  <tr key={t.id} onClick={() => navigate(`/tickets/${t.id}`)}>
                    <td className="ticket-id">#{t.id}</td>
                    <td className="ticket-summary">{t.summary}</td>
                    <td><span className={`badge badge-priority-${t.priority}`}>{t.priority}</span></td>
                    <td><span className={`badge badge-status-${t.status}`}>{t.status.replace('_', ' ')}</span></td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{t.category_name || '-'}</td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{t.assigned_agent_name || <span style={{ color: 'var(--warning)' }}>Unassigned</span>}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{formatDate(t.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
