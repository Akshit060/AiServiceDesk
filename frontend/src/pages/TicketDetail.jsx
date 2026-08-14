import { useState, useEffect } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import { fetchTicket, updateTicket, addComment, analyzeTicket, fetchRelatedTickets, fetchCategories, fetchAgents, generateResolutionDraft, chatAboutTicket } from '../services/api';
import { useToast } from '../components/Toast';

export default function TicketDetail() {
  const { id } = useParams();
  const { currentAgent } = useOutletContext();
  const navigate = useNavigate();
  const toast = useToast();

  const [ticket, setTicket] = useState(null);
  const [categories, setCategories] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Comments
  const [commentBody, setCommentBody] = useState('');
  const [addingComment, setAddingComment] = useState(false);

  // AI Copilot
  const [aiResult, setAiResult] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [draftResult, setDraftResult] = useState(null);
  const [draftLoading, setDraftLoading] = useState(false);
  const [chatQuestion, setChatQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  // Related
  const [relatedTickets, setRelatedTickets] = useState([]);
  const [relatedLoading, setRelatedLoading] = useState(false);

  // Resolution
  const [resolution, setResolution] = useState('');
  const [resolving, setResolving] = useState(false);

  // Updates
  const [updating, setUpdating] = useState(false);

  const loadTicket = () => {
    setLoading(true);
    Promise.all([fetchTicket(id), fetchCategories(), fetchAgents()])
      .then(([t, cats, agts]) => {
        setTicket(t);
        setResolution(t.resolution || '');
        setCategories(cats);
        setAgents(agts);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadTicket(); }, [id]);

  useEffect(() => {
    if (ticket) {
      setRelatedLoading(true);
      fetchRelatedTickets(id)
        .then(setRelatedTickets)
        .catch(() => setRelatedTickets([]))
        .finally(() => setRelatedLoading(false));
    }
  }, [ticket?.id]);

  const handleUpdate = async (data) => {
    setUpdating(true);
    try {
      const updated = await updateTicket(id, data);
      setTicket(updated);
      setResolution(updated.resolution || '');
      toast.success('Ticket updated.');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setUpdating(false);
    }
  };

  const handleAssignToMe = () => {
    if (!currentAgent) { toast.error('No engineer selected.'); return; }
    handleUpdate({ assigned_agent_id: currentAgent.id });
  };

  const handleAddComment = async () => {
    if (!commentBody.trim()) return;
    if (!currentAgent) { toast.error('No engineer selected.'); return; }
    setAddingComment(true);
    try {
      await addComment(id, { agent_id: currentAgent.id, body: commentBody.trim() });
      setCommentBody('');
      loadTicket();
      toast.success('Comment added.');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setAddingComment(false);
    }
  };

  const handleAnalyze = async () => {
    setAiLoading(true);
    setAiResult(null);
    try {
      const result = await analyzeTicket(id);
      setAiResult(result);
    } catch (err) {
      setAiResult({ available: false, error: err.message });
    } finally {
      setAiLoading(false);
    }
  };

  const handleGenerateDraft = async () => {
    setDraftLoading(true);
    setDraftResult(null);
    try {
      const result = await generateResolutionDraft(id);
      setDraftResult(result);
    } catch (err) {
      setDraftResult({ available: false, error: err.message });
    } finally {
      setDraftLoading(false);
    }
  };

  const handleChat = async () => {
    if (!chatQuestion.trim()) return;
    const q = chatQuestion.trim();
    setChatQuestion('');
    const newHistory = [...chatHistory, { role: 'user', content: q }];
    setChatHistory(newHistory);
    setChatLoading(true);
    
    try {
      const result = await chatAboutTicket(id, { question: q, history: newHistory });
      if (result.available) {
        setChatHistory([...newHistory, { role: 'assistant', content: result.answer }]);
      } else {
        setChatHistory([...newHistory, { role: 'system', content: `Error: ${result.error}` }]);
      }
    } catch (err) {
      setChatHistory([...newHistory, { role: 'system', content: `Error: ${err.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!resolution.trim()) { toast.error('Please enter a resolution before resolving.'); return; }
    setResolving(true);
    try {
      const updated = await updateTicket(id, { status: 'resolved', resolution: resolution.trim() });
      setTicket(updated);
      toast.success('Ticket resolved!');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setResolving(false);
    }
  };

  const formatDate = (d) => {
    if (!d) return '-';
    return new Date(d).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  if (loading) return <div className="loading"><div className="loading-spinner"></div>Loading ticket...</div>;
  if (error) return <div className="error-state"><p>⚠️ {error}</p><button className="btn btn-secondary" style={{ marginTop: '12px' }} onClick={() => navigate('/tickets')}>Back to Queue</button></div>;
  if (!ticket) return null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ color: 'var(--accent)' }}>#{ticket.id}</span>
            {ticket.summary}
          </h1>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/tickets')}>← Back</button>
      </div>

      <div className="ticket-detail">
        {/* ─── Main Content ─── */}
        <div className="ticket-detail-main">
          {/* Ticket Info */}
          <div className="card detail-section">
            <h3>Ticket Information</h3>
            <div className="info-grid">
              <div className="detail-field"><div className="field-label">Status</div><div className="field-value"><span className={`badge badge-status-${ticket.status}`}>{ticket.status.replace('_', ' ')}</span></div></div>
              <div className="detail-field"><div className="field-label">Priority</div><div className="field-value"><span className={`badge badge-priority-${ticket.priority}`}>{ticket.priority}</span></div></div>
              <div className="detail-field"><div className="field-label">Category</div><div className="field-value">{ticket.category_name || 'Uncategorized'}</div></div>
              <div className="detail-field"><div className="field-label">Assigned To</div><div className="field-value">{ticket.assigned_agent_name || <span style={{ color: 'var(--warning)' }}>Unassigned</span>}</div></div>
              <div className="detail-field"><div className="field-label">Created</div><div className="field-value">{formatDate(ticket.created_at)}</div></div>
              <div className="detail-field"><div className="field-label">Updated</div><div className="field-value">{formatDate(ticket.updated_at)}</div></div>
              {ticket.channel && <div className="detail-field"><div className="field-label">Channel</div><div className="field-value">{ticket.channel}</div></div>}
              {ticket.requester_department && <div className="detail-field"><div className="field-label">Department</div><div className="field-value">{ticket.requester_department}</div></div>}
            </div>
            <div className="detail-field" style={{ marginTop: '12px' }}>
              <div className="field-label">Description</div>
              <div className="field-value" style={{ whiteSpace: 'pre-wrap' }}>{ticket.description}</div>
            </div>
          </div>

          {/* Comments / Activity */}
          <div className="card detail-section">
            <h3>Investigation Activity ({ticket.comments?.length || 0})</h3>
            {ticket.comments?.length > 0 ? (
              <div className="comment-timeline">
                {ticket.comments.map(c => (
                  <div key={c.id} className="comment-item">
                    <div className="comment-header">
                      <span className="comment-author">{c.agent_name || 'System'}<span className="comment-visibility">{c.visibility}</span></span>
                      <span className="comment-time">{formatDate(c.created_at)}</span>
                    </div>
                    <div className="comment-body">{c.body}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state"><p>No investigation notes yet.</p></div>
            )}
            <div className="add-comment">
              <textarea
                placeholder="Add investigation note..."
                value={commentBody}
                onChange={e => setCommentBody(e.target.value)}
              />
              <button className="btn btn-primary" onClick={handleAddComment} disabled={addingComment || !commentBody.trim()}>
                {addingComment ? '...' : 'Add'}
              </button>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="card detail-section">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>🤖 AI Investigation Copilot</h3>
            
            <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
              <button className="btn btn-primary" onClick={handleAnalyze} disabled={aiLoading}>
                {aiLoading ? 'Analyzing...' : '✨ Analyze Incident'}
              </button>
              <button className="btn btn-secondary" onClick={handleGenerateDraft} disabled={draftLoading || ticket.status === 'resolved'}>
                {draftLoading ? 'Drafting...' : '📝 Generate Resolution Draft'}
              </button>
            </div>

            {/* AI Analysis Result */}
            {aiResult && (
              aiResult.available === false ? (
                <div className="ai-unavailable">{aiResult.error}</div>
              ) : (
                <div className="ai-panel">
                  <div className="ai-section"><h4>Summary</h4><p>{aiResult.analysis?.summary}</p></div>
                  <div className="ai-section"><h4>Possible Cause</h4><p>{aiResult.analysis?.possible_cause}</p></div>
                  {aiResult.analysis?.investigation_steps?.length > 0 && (
                    <div className="ai-section">
                      <h4>Investigation Steps</h4>
                      <ul>{aiResult.analysis.investigation_steps.map((s, i) => <li key={i}>{s}</li>)}</ul>
                    </div>
                  )}
                  <div className="ai-section"><h4>Recommended Resolution</h4><p>{aiResult.analysis?.recommended_resolution}</p></div>
                  <div className="ai-section"><h4>Confidence</h4><p>{aiResult.analysis?.confidence}</p></div>
                  {(aiResult.analysis?.suggested_category || aiResult.analysis?.suggested_priority) && (
                    <div className="ai-section">
                      <h4>Suggestions</h4>
                      {aiResult.analysis.suggested_category && <p>Category: {aiResult.analysis.suggested_category}</p>}
                      {aiResult.analysis.suggested_priority && <p>Priority: <span className={`badge badge-priority-${aiResult.analysis.suggested_priority}`}>{aiResult.analysis.suggested_priority}</span></p>}
                    </div>
                  )}
                </div>
              )
            )}

            {/* AI Draft Result */}
            {draftResult && (
              draftResult.available === false ? (
                <div className="ai-unavailable" style={{ marginTop: '16px' }}>{draftResult.error}</div>
              ) : (
                <div className="ai-panel" style={{ marginTop: '16px', borderLeftColor: 'var(--success)' }}>
                  <div className="ai-section">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <h4 style={{ margin: 0 }}>Resolution Draft</h4>
                      <button 
                        className="btn btn-sm btn-success" 
                        onClick={() => setResolution(draftResult.draft)}
                      >
                        Use Draft
                      </button>
                    </div>
                    <p style={{ whiteSpace: 'pre-wrap' }}>{draftResult.draft}</p>
                  </div>
                </div>
              )
            )}

            {/* AI Chat */}
            <div className="ai-panel" style={{ marginTop: '16px', borderLeftColor: '#3b82f6', background: 'transparent', padding: 0 }}>
              <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)', background: 'var(--bg-secondary)' }}>
                <h4 style={{ margin: 0 }}>Chat with Copilot</h4>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>Ask questions about this ticket and its historical evidence.</p>
              </div>
              
              {chatHistory.length > 0 && (
                <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '300px', overflowY: 'auto' }}>
                  {chatHistory.map((msg, idx) => (
                    <div key={idx} style={{ 
                      alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                      background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg-tertiary)',
                      color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      maxWidth: '85%',
                      fontSize: '13px',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {msg.role === 'system' ? `⚠️ ${msg.content}` : msg.content}
                    </div>
                  ))}
                  {chatLoading && (
                    <div style={{ alignSelf: 'flex-start', color: 'var(--text-muted)', fontSize: '13px' }}>Copilot is typing...</div>
                  )}
                </div>
              )}
              
              <div style={{ padding: '12px', display: 'flex', gap: '8px', borderTop: '1px solid var(--border-color)' }}>
                <input 
                  type="text" 
                  placeholder="Ask a question..." 
                  value={chatQuestion}
                  onChange={e => setChatQuestion(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleChat()}
                  style={{ flex: 1, padding: '8px 12px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius)', color: 'var(--text-primary)' }}
                  disabled={chatLoading}
                />
                <button className="btn btn-secondary" onClick={handleChat} disabled={chatLoading || !chatQuestion.trim()}>
                  Send
                </button>
              </div>
            </div>
          </div>

          {/* Related Historical Tickets */}
          <div className="card detail-section">
            <h3>Related Historical Incidents</h3>
            {relatedLoading ? (
              <div className="loading"><div className="loading-spinner"></div>Finding related incidents...</div>
            ) : relatedTickets.length > 0 ? (
              relatedTickets.map(rt => (
                <div key={rt.id} className="related-ticket-item" onClick={() => navigate(`/tickets/${rt.id}`)}>
                  <div className="rt-header">
                    <span className="rt-id">#{rt.id}</span>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span className={`badge badge-status-${rt.status}`}>{rt.status}</span>
                      <span className={`badge badge-priority-${rt.priority}`}>{rt.priority}</span>
                      {rt.relevance_score && <span className="rt-score">{Math.round(rt.relevance_score * 100)}%</span>}
                    </div>
                  </div>
                  <div className="rt-title">{rt.summary}</div>
                  {rt.category_name && <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>{rt.category_name}</div>}
                  {rt.resolution && <div className="rt-resolution">Resolution: {rt.resolution}</div>}
                </div>
              ))
            ) : (
              <div className="empty-state"><p>No related incidents found.</p></div>
            )}
          </div>
        </div>

        {/* ─── Sidebar ─── */}
        <div className="ticket-detail-sidebar">
          {/* Actions */}
          <div className="card">
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>Engineer Controls</h3>
            
            {(!ticket.assigned_agent_id || ticket.assigned_agent_id !== currentAgent?.id) && (
              <button className="btn btn-primary" style={{ width: '100%', marginBottom: '10px' }} onClick={handleAssignToMe} disabled={updating}>
                👤 Assign to Me
              </button>
            )}

            <div className="form-group">
              <label>Status</label>
              <select value={ticket.status} onChange={e => handleUpdate({ status: e.target.value })} disabled={updating}>
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved" disabled={!ticket.resolution}>Resolved</option>
              </select>
            </div>
            <div className="form-group">
              <label>Priority</label>
              <select value={ticket.priority} onChange={e => handleUpdate({ priority: e.target.value })} disabled={updating}>
                <option value="P1">P1 - Critical</option>
                <option value="P2">P2 - High</option>
                <option value="P3">P3 - Medium</option>
                <option value="P4">P4 - Low</option>
              </select>
            </div>
            <div className="form-group">
              <label>Category</label>
              <select value={ticket.category_id || ''} onChange={e => handleUpdate({ category_id: parseInt(e.target.value) || null })} disabled={updating}>
                <option value="">Uncategorized</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Assigned To</label>
              <select value={ticket.assigned_agent_id || ''} onChange={e => handleUpdate({ assigned_agent_id: parseInt(e.target.value) || null })} disabled={updating}>
                <option value="">Unassigned</option>
                {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
          </div>

          {/* Resolution */}
          <div className={ticket.status === 'resolved' ? 'resolution-panel' : 'card'}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: ticket.status === 'resolved' ? 'var(--success)' : 'var(--text-secondary)', marginBottom: '12px' }}>
              {ticket.status === 'resolved' ? '✓ Resolution' : 'Resolution'}
            </h3>
            {ticket.status === 'resolved' && ticket.resolution ? (
              <div className="resolution-display">{ticket.resolution}</div>
            ) : (
              <>
                <textarea
                  style={{ width: '100%', padding: '10px', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius)', fontSize: '13px', fontFamily: 'inherit', minHeight: '80px', resize: 'vertical' }}
                  placeholder="Enter the resolution / outcome..."
                  value={resolution}
                  onChange={e => setResolution(e.target.value)}
                />
                <button
                  className="btn btn-success"
                  style={{ width: '100%', marginTop: '10px' }}
                  onClick={handleResolve}
                  disabled={resolving || !resolution.trim()}
                >
                  {resolving ? 'Resolving...' : '✓ Resolve Ticket'}
                </button>
              </>
            )}
            {ticket.resolved_at && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
                Resolved: {formatDate(ticket.resolved_at)}
              </div>
            )}
          </div>

          {/* Metadata */}
          <div className="card">
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>Metadata</h3>
            {ticket.affected_service && <div className="detail-field"><div className="field-label">Affected Service</div><div className="field-value">{ticket.affected_service}</div></div>}
            {ticket.escalated && <div className="detail-field"><div className="field-value"><span className="badge badge-priority-P2">Escalated</span></div></div>}
            {ticket.outage_related && <div className="detail-field"><div className="field-value"><span className="badge badge-priority-P1">Outage Related</span></div></div>}
            {ticket.source_status && <div className="detail-field"><div className="field-label">Original Status</div><div className="field-value">{ticket.source_status}</div></div>}
          </div>
        </div>
      </div>
    </div>
  );
}
