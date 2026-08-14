import { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { createTicket, fetchCategories, fetchAgents, classifyTicket } from '../services/api';
import { useToast } from '../components/Toast';

export default function CreateTicket() {
  const { currentAgent } = useOutletContext();
  const [categories, setCategories] = useState([]);
  const [agents, setAgents] = useState([]);
  const [form, setForm] = useState({ summary: '', description: '', priority: 'P3', category_id: '', assigned_agent_id: '' });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [classifying, setClassifying] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    Promise.all([fetchCategories(), fetchAgents()])
      .then(([cats, agts]) => { setCategories(cats); setAgents(agts); })
      .catch(() => {});
  }, []);

  const validate = () => {
    const e = {};
    if (!form.summary.trim()) e.summary = 'Title is required.';
    if (!form.description.trim()) e.description = 'Description is required.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      const data = {
        summary: form.summary.trim(),
        description: form.description.trim(),
        priority: form.priority,
        category_id: form.category_id ? parseInt(form.category_id) : null,
        assigned_agent_id: form.assigned_agent_id ? parseInt(form.assigned_agent_id) : null,
      };
      const ticket = await createTicket(data);
      toast.success(`Ticket #${ticket.id} created successfully.`);
      navigate(`/tickets/${ticket.id}`);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleClassify = async () => {
    if (!form.summary.trim() && !form.description.trim()) {
      toast.error('Enter a title or description before analyzing.');
      return;
    }
    setClassifying(true);
    setAiSuggestion(null);
    try {
      const result = await classifyTicket({ summary: form.summary, description: form.description });
      if (result.available && result.classification) {
        setAiSuggestion(result.classification);
      } else {
        toast.info(result.error || 'AI classification is unavailable.');
      }
    } catch (err) {
      toast.error(err.message);
    } finally {
      setClassifying(false);
    }
  };

  const acceptSuggestion = () => {
    if (!aiSuggestion) return;
    const updates = {};
    if (aiSuggestion.priority) updates.priority = aiSuggestion.priority;
    if (aiSuggestion.category) {
      const cat = categories.find(c => c.name.toLowerCase() === aiSuggestion.category.toLowerCase());
      if (cat) updates.category_id = String(cat.id);
    }
    setForm(prev => ({ ...prev, ...updates }));
    toast.success('AI suggestions applied.');
  };

  return (
    <div>
      <div className="page-header">
        <h1>Create New Ticket</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '24px' }}>
        <div className="card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Title *</label>
              <input type="text" value={form.summary} onChange={e => setForm(f => ({ ...f, summary: e.target.value }))} placeholder="Brief summary of the issue" />
              {errors.summary && <div className="form-error">{errors.summary}</div>}
            </div>
            <div className="form-group">
              <label>Description *</label>
              <textarea rows="6" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Detailed description of the issue..." />
              {errors.description && <div className="form-error">{errors.description}</div>}
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Priority</label>
                <select value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}>
                  <option value="P1">P1 - Critical</option>
                  <option value="P2">P2 - High</option>
                  <option value="P3">P3 - Medium</option>
                  <option value="P4">P4 - Low</option>
                </select>
              </div>
              <div className="form-group">
                <label>Category</label>
                <select value={form.category_id} onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}>
                  <option value="">Select category...</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>Assign To</label>
              <select value={form.assigned_agent_id} onChange={e => setForm(f => ({ ...f, assigned_agent_id: e.target.value }))}>
                <option value="">Unassigned</option>
                {agents.map(a => <option key={a.id} value={a.id}>{a.name} ({a.team})</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
              <button type="submit" className="btn btn-primary btn-lg" disabled={submitting}>
                {submitting ? 'Creating...' : 'Create Ticket'}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => navigate('/tickets')}>Cancel</button>
            </div>
          </form>
        </div>

        <div>
          <div className="card" style={{ marginBottom: '16px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>🤖 AI-Assisted Classification</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Enter a title and description, then click to get AI-suggested category and priority.
            </p>
            <button className="btn btn-primary btn-sm" onClick={handleClassify} disabled={classifying} style={{ width: '100%' }}>
              {classifying ? 'Analyzing...' : '✨ Analyze with AI'}
            </button>
          </div>

          {aiSuggestion && (
            <div className="ai-suggestion-card">
              <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--accent)', marginBottom: '12px' }}>AI Suggestion</h4>
              {aiSuggestion.category && (
                <div className="detail-field">
                  <div className="field-label">Category</div>
                  <div className="field-value">{aiSuggestion.category}</div>
                </div>
              )}
              {aiSuggestion.priority && (
                <div className="detail-field">
                  <div className="field-label">Priority</div>
                  <div className="field-value"><span className={`badge badge-priority-${aiSuggestion.priority}`}>{aiSuggestion.priority}</span></div>
                </div>
              )}
              {aiSuggestion.reasoning && (
                <div className="detail-field">
                  <div className="field-label">Reasoning</div>
                  <div className="field-value" style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{aiSuggestion.reasoning}</div>
                </div>
              )}
              {aiSuggestion.confidence && (
                <div className="detail-field">
                  <div className="field-label">Confidence</div>
                  <div className="field-value" style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{aiSuggestion.confidence}</div>
                </div>
              )}
              <button className="btn btn-success btn-sm" onClick={acceptSuggestion} style={{ width: '100%', marginTop: '12px' }}>
                ✓ Accept Suggestions
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
