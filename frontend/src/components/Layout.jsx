import { NavLink, Outlet } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { fetchAgents } from '../services/api';

export default function Layout() {
  const [agents, setAgents] = useState([]);
  const [currentAgent, setCurrentAgent] = useState(null);

  useEffect(() => {
    fetchAgents()
      .then(data => {
        setAgents(data);
        const saved = localStorage.getItem('currentAgentId');
        if (saved && data.find(a => a.id === parseInt(saved))) {
          setCurrentAgent(data.find(a => a.id === parseInt(saved)));
        } else if (data.length > 0) {
          setCurrentAgent(data[0]);
          localStorage.setItem('currentAgentId', data[0].id);
        }
      })
      .catch(() => {});
  }, []);

  const handleAgentChange = (e) => {
    const id = parseInt(e.target.value);
    const agent = agents.find(a => a.id === id);
    setCurrentAgent(agent);
    localStorage.setItem('currentAgentId', id);
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h2>⚡ ServiceDesk</h2>
          <p>Engineer Console</p>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
            📊 Dashboard
          </NavLink>
          <NavLink to="/tickets" className={({ isActive }) => isActive ? 'active' : ''}>
            🎫 Tickets
          </NavLink>
          <NavLink to="/knowledge" className={({ isActive }) => isActive ? 'active' : ''}>
            📚 Knowledge Base
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <div className="engineer-selector">
            <label>Current Engineer</label>
            <select
              value={currentAgent?.id || ''}
              onChange={handleAgentChange}
            >
              {agents.map(a => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
          </div>
        </div>
      </aside>
      <main className="main-content">
        <Outlet context={{ currentAgent, agents }} />
      </main>
    </div>
  );
}
