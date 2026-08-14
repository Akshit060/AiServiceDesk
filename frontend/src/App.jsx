import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ToastProvider } from './components/Toast';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import TicketQueue from './pages/TicketQueue';
import TicketDetail from './pages/TicketDetail';
import CreateTicket from './pages/CreateTicket';
import KnowledgeBase from './pages/KnowledgeBase';

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tickets" element={<TicketQueue />} />
            <Route path="/tickets/new" element={<CreateTicket />} />
            <Route path="/tickets/:id" element={<TicketDetail />} />
            <Route path="/knowledge" element={<KnowledgeBase />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}

export default App;
