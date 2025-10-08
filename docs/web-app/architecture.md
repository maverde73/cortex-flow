# Cortex Flow Web Application - Architecture

## Overview

The Cortex Flow web application is a modern React-based single-page application (SPA) that provides a visual interface for managing AI agents and workflows. It follows best practices for maintainability, performance, and developer experience.

## Technology Stack

### Core Technologies

- **React 18**: UI framework with hooks and concurrent features
- **TypeScript**: Type-safe JavaScript for better developer experience
- **Vite**: Fast build tool with HMR (Hot Module Replacement)
- **TailwindCSS**: Utility-first CSS framework
- **React Router v6**: Client-side routing

### State Management

- **React Query (TanStack Query)**: Server state management
- **Zustand**: Client state management
- **Context API**: Theme and global settings

### UI Components

- **React Flow**: Visual workflow editor
- **Headless UI**: Accessible UI primitives
- **React Hook Form**: Form management
- **React Hot Toast**: Notifications

## Architecture Patterns

### Component Structure

```
src/
├── components/          # Reusable components
│   ├── common/         # Generic components
│   ├── workflow/       # Workflow-specific
│   ├── process/        # Process management
│   └── ui/             # UI primitives
├── pages/              # Route components
├── services/           # API layer
├── hooks/              # Custom hooks
├── store/              # State management
├── types/              # TypeScript types
└── utils/              # Utilities
```

### Component Design Principles

1. **Single Responsibility**: Each component has one clear purpose
2. **Composition over Inheritance**: Use component composition
3. **Props Interface**: Clear TypeScript interfaces for all props
4. **Separation of Concerns**: Logic separated from presentation

## State Management Strategy

### Server State (React Query)

Managed by React Query for all API data:

```typescript
// Example: Fetching projects
const { data: projects, isLoading } = useQuery({
  queryKey: ['projects'],
  queryFn: () => api.listProjects(),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

**Benefits:**
- Automatic caching and invalidation
- Background refetching
- Optimistic updates
- Request deduplication

### Client State (Zustand)

Local UI state managed by Zustand:

```typescript
// store/useStore.ts
interface AppStore {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  currentProject: Project | null;
  setCurrentProject: (project: Project) => void;
}

export const useStore = create<AppStore>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({
    sidebarOpen: !state.sidebarOpen
  })),
  currentProject: null,
  setCurrentProject: (project) => set({ currentProject: project }),
}));
```

## API Integration

### Service Layer

All API calls go through a centralized service layer:

```typescript
// services/api.ts
class ApiClient {
  private baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8002';

  async request<T>(
    path: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new ApiError(response);
    }

    return response.json();
  }

  // Typed API methods
  listProjects() {
    return this.request<Project[]>('/api/projects');
  }
}

export const api = new ApiClient();
```

### Error Handling

Centralized error handling with boundaries:

```typescript
// components/ErrorBoundary.tsx
class ErrorBoundary extends Component {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    logger.error('Component error:', error, errorInfo);
    // Send to error tracking service
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

## Routing Architecture

### Route Structure

```typescript
// App.tsx
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="workflows" element={<WorkflowsPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="testing" element={<TestingPage />} />
          <Route path="prompts" element={<PromptsPage />} />
          <Route path="mcp" element={<MCPPage />} />
          <Route path="llm" element={<LLMPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

### Code Splitting

Lazy loading for better performance:

```typescript
const WorkflowsPage = lazy(() => import('./pages/WorkflowsPage'));

// In routes
<Route
  path="workflows"
  element={
    <Suspense fallback={<Loading />}>
      <WorkflowsPage />
    </Suspense>
  }
/>
```

## Component Patterns

### Container/Presenter Pattern

```typescript
// Container (handles logic)
function ProcessManagerContainer() {
  const { data: processes } = useQuery({
    queryKey: ['processes'],
    queryFn: api.getProcesses,
  });

  const startProcess = useMutation({
    mutationFn: api.startProcess,
  });

  return (
    <ProcessManagerView
      processes={processes}
      onStart={startProcess.mutate}
    />
  );
}

// Presenter (pure UI)
function ProcessManagerView({
  processes,
  onStart
}: ProcessManagerViewProps) {
  return (
    <div>
      {processes.map(process => (
        <ProcessCard
          key={process.id}
          process={process}
          onStart={() => onStart(process.id)}
        />
      ))}
    </div>
  );
}
```

### Custom Hooks

Encapsulate complex logic in custom hooks:

```typescript
// hooks/useProcessControl.ts
function useProcessControl(processName: string) {
  const queryClient = useQueryClient();

  const start = useMutation({
    mutationFn: () => api.startProcess(processName),
    onSuccess: () => {
      queryClient.invalidateQueries(['processes']);
      toast.success(`Started ${processName}`);
    },
  });

  const stop = useMutation({
    mutationFn: () => api.stopProcess(processName),
    onSuccess: () => {
      queryClient.invalidateQueries(['processes']);
      toast.success(`Stopped ${processName}`);
    },
  });

  return { start, stop };
}
```

## Performance Optimization

### Memoization

```typescript
// Expensive computation memoized
const expensiveData = useMemo(() =>
  processLargeDataset(rawData),
  [rawData]
);

// Component memoization
const ExpensiveComponent = memo(({ data }) => {
  return <ComplexVisualization data={data} />;
});
```

### Virtual Scrolling

For large lists:

```typescript
import { FixedSizeList } from 'react-window';

function LargeList({ items }) {
  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={50}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>
          {items[index].name}
        </div>
      )}
    </FixedSizeList>
  );
}
```

### Bundle Optimization

Vite configuration for optimal bundles:

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@headlessui/react', 'react-flow-renderer'],
          'state-vendor': ['@tanstack/react-query', 'zustand'],
        },
      },
    },
  },
});
```

## Testing Strategy

### Unit Tests

```typescript
// ProcessBadge.test.tsx
describe('ProcessBadge', () => {
  it('shows running status correctly', () => {
    render(
      <ProcessBadge
        process={{ status: 'running', name: 'test' }}
        onToggle={jest.fn()}
      />
    );

    expect(screen.getByText(/test/)).toBeInTheDocument();
    expect(screen.getByText(/🟢/)).toBeInTheDocument();
  });
});
```

### Integration Tests

```typescript
// WorkflowEditor.integration.test.tsx
describe('WorkflowEditor Integration', () => {
  it('creates workflow from natural language', async () => {
    render(<WorkflowEditor />);

    const input = screen.getByPlaceholderText('Describe workflow...');
    await userEvent.type(input, 'Research and analyze data');

    await userEvent.click(screen.getByText('Generate'));

    await waitFor(() => {
      expect(screen.getByText('Research Node')).toBeInTheDocument();
      expect(screen.getByText('Analyze Node')).toBeInTheDocument();
    });
  });
});
```

## Security Considerations

### XSS Protection

React automatically escapes values:

```typescript
// Safe by default
<div>{userInput}</div>

// Dangerous (avoided)
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

### CSRF Protection

```typescript
// API requests include CSRF token
const csrfToken = getCsrfToken();

fetch('/api/action', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrfToken,
  },
  body: JSON.stringify(data),
});
```

### Input Validation

```typescript
// Using zod for validation
import { z } from 'zod';

const WorkflowSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().optional(),
  nodes: z.array(NodeSchema),
});

function validateWorkflow(data: unknown) {
  return WorkflowSchema.parse(data);
}
```

## Deployment

### Build Process

```bash
# Production build
npm run build

# Output structure
dist/
├── index.html
├── assets/
│   ├── index-[hash].js
│   ├── vendor-[hash].js
│   └── index-[hash].css
└── favicon.ico
```

### Environment Configuration

```typescript
// Different configs per environment
const config = {
  development: {
    apiUrl: 'http://localhost:8002',
    enableDevTools: true,
  },
  production: {
    apiUrl: 'https://api.cortexflow.com',
    enableDevTools: false,
  },
}[import.meta.env.MODE];
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

## Monitoring & Analytics

### Performance Monitoring

```typescript
// Web Vitals tracking
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric: Metric) {
  // Send to analytics service
  analytics.track('web-vitals', {
    name: metric.name,
    value: metric.value,
  });
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

### Error Tracking

```typescript
// Sentry integration
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay(),
  ],
});
```

## Future Enhancements

### Planned Features

1. **Real-time Collaboration**: WebSocket-based collaborative editing
2. **Offline Support**: Service Worker for offline functionality
3. **Mobile App**: React Native companion app
4. **Plugin System**: Extensible architecture for custom components
5. **Advanced Analytics**: Detailed workflow performance metrics

### Technical Debt

1. Migrate remaining class components to hooks
2. Improve TypeScript coverage (target 100%)
3. Add E2E tests with Playwright
4. Implement proper i18n support
5. Optimize bundle size further

## Contributing

See main [Contributing Guide](../../CONTRIBUTING.md) for development setup and guidelines.