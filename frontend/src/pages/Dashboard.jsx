import { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { fetchDashboard, fetchTickets } from '../services/api';

export default function Dashboard() {
  const { currentAgent } = useOutletContext();
  const [dashboard, setDashboard] = useState(null);
  const [recentTickets, setRecentTickets] = useState([]);
  const [myTickets, setMyTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchDashboard(),
      fetchTickets({ sort: 'newest', page_size: 5 }),
      currentAgent ? fetchTickets({ agent_id: currentAgent.id, status: 'in_progress', page_size: 5 }) : Promise.resolve({ tickets: [] }),
    ])
      .then(([dash, recent, my]) => {
        setDashboard(dash);
        setRecentTickets(recent.tickets);
        setMyTickets(my.tickets);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [currentAgent]);

  if (loading) return <div className="loading"><div className="loading-spinner"></div>Loading dashboard...</div>;
  if (error) return <div className="error-state"><p>⚠️ {error}</p></div>;
  if (!dashboard) return null;

  const maxByStatus = Math.max(...dashboard.by_status.map(s => s.count), 1);
  const maxByPriority = Math.max(...dashboard.by_priority.map(p => p.count), 1);
  const maxByCategory = Math.max(...dashboard.by_category.map(c => c.count), 1);

  const statusColor = { open: 'var(--status-open)', in_progress: 'var(--status-progress)', resolved: 'var(--status-resolved)' };
  const priorityColor = { P1: 'var(--p1-color)', P2: 'var(--p2-color)', P3: 'var(--p3-color)', P4: 'var(--p4-color)' };

  return (
    <div>
      <div className="page-header">
        <h1>Engineer Dashboard</h1>
        <button className="btn btn-primary" onClick={() => navigate('/tickets/new')}>+ New Ticket</button>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-value">{dashboard.total_tickets}</div>
          <div className="metric-label">Total Tickets</div>
        </div>
        <div className="metric-card">
          <div className="metric-value" style={{ color: 'var(--status-open)' }}>{dashboard.open_tickets}</div>
          <div className="metric-label">Open</div>
        </div>
        <div className="metric-card">
          <div className="metric-value" style={{ color: 'var(--status-progress)' }}>{dashboard.in_progress_tickets}</div>
          <div className="metric-label">In Progress</div>
        </div>
        <div className="metric-card">
          <div className="metric-value" style={{ color: 'var(--status-resolved)' }}>{dashboard.resolved_tickets}</div>
          <div className="metric-label">Resolved</div>
        </div>
        <div className="metric-card">
          <div className="metric-value" style={{ color: 'var(--warning)' }}>{dashboard.unassigned_tickets}</div>
          <div className="metric-label">Unassigned</div>
        </div>
        <div className="metric-card">
          <div className="metric-value" style={{ color: 'var(--danger)' }}>{dashboard.critical_high_tickets}</div>
          <div className="metric-label">Critical / High (P1+P2)</div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>Tickets by Status</h3>
          <div className="bar-chart">
            {dashboard.by_status.map(s => (
              <div key={s.status} className="bar-row">
                <span className="bar-label">{s.status.replace('_', ' ')}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(s.count / maxByStatus) * 100}%`, background: statusColor[s.status] || 'var(--accent)' }} />
                </div>
                <span className="bar-count">{s.count}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="chart-card">
          <h3>Tickets by Priority</h3>
          <div className="bar-chart">
            {dashboard.by_priority.sort((a, b) => a.priority.localeCompare(b.priority)).map(p => (
              <div key={p.priority} className="bar-row">
                <span className="bar-label">{p.priority}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(p.count / maxByPriority) * 100}%`, background: priorityColor[p.priority] || 'var(--accent)' }} />
                </div>
                <span className="bar-count">{p.count}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="chart-card">
          <h3>Tickets by Category</h3>
          <div className="bar-chart">
            {dashboard.by_category.map(c => (
              <div key={c.category} className="bar-row">
                <span className="bar-label">{c.category}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(c.count / maxByCategory) * 100}%`, background: 'var(--accent)' }} />
                </div>
                <span className="bar-count">{c.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="charts-grid">
        {myTickets.length > 0 && (
          <div className="card">
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>My Active Tickets</h3>
            <table className="ticket-table">
              <tbody>
                {myTickets.map(t => (
                  <tr key={t.id} onClick={() => navigate(`/tickets/${t.id}`)}>
                    <td className="ticket-id">#{t.id}</td>
                    <td className="ticket-summary">{t.summary}</td>
                    <td><span className={`badge badge-priority-${t.priority}`}>{t.priority}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="card">
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>Recent Tickets</h3>
          <table className="ticket-table">
            <tbody>
              {recentTickets.map(t => (
                <tr key={t.id} onClick={() => navigate(`/tickets/${t.id}`)}>
                  <td className="ticket-id">#{t.id}</td>
                  <td className="ticket-summary">{t.summary}</td>
                  <td><span className={`badge badge-status-${t.status}`}>{t.status.replace('_', ' ')}</span></td>
                  <td><span className={`badge badge-priority-${t.priority}`}>{t.priority}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
