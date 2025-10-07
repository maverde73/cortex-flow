/**
 * Main App component with routing
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { WorkflowsPage } from './pages/WorkflowsPage';
import { AgentsPage } from './pages/AgentsPage';
import { PromptsPage } from './pages/PromptsPage';
import { MCPPage } from './pages/MCPPage';
import { LLMConfigPage } from './pages/LLMConfigPage';
import { TestingPage } from './pages/TestingPage';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="workflows" element={<WorkflowsPage />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="prompts" element={<PromptsPage />} />
            <Route path="mcp" element={<MCPPage />} />
            <Route path="llm" element={<LLMConfigPage />} />
            <Route path="testing" element={<TestingPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
