/**
 * Main layout component with sidebar and project selector
 */

import { useEffect, useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useStore } from '../store/useStore';
import { api } from '../services/api';

interface NavItem {
  name: string;
  path: string;
  icon: string;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/', icon: '📊' },
  { name: 'Projects', path: '/projects', icon: '📁' },
  { name: 'Workflows', path: '/workflows', icon: '🔄' },
  { name: 'Agents', path: '/agents', icon: '🤖' },
  { name: 'Testing', path: '/testing', icon: '🧪' },
  { name: 'Prompts', path: '/prompts', icon: '💬' },
  { name: 'MCP', path: '/mcp', icon: '🔌' },
  { name: 'LLM', path: '/llm', icon: '🧠' },
];

export function Layout() {
  const location = useLocation();
  const { sidebarOpen, toggleSidebar, currentProject, setCurrentProject } = useStore();
  const [showProjectSelector, setShowProjectSelector] = useState(false);
  const queryClient = useQueryClient();

  // Fetch all projects
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.listProjects(),
  });

  // Load active project on mount
  useEffect(() => {
    if (projects && !currentProject) {
      const activeProject = projects.find((p) => p.active);
      if (activeProject) {
        setCurrentProject(activeProject);
      }
    }
  }, [projects, currentProject, setCurrentProject]);

  // Activate project mutation
  const activateMutation = useMutation({
    mutationFn: (name: string) => api.activateProject(name),
    onSuccess: (data) => {
      setCurrentProject(data);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowProjectSelector(false);
    },
  });

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside
        className={`bg-gray-900 text-white transition-all duration-300 ${
          sidebarOpen ? 'w-64' : 'w-16'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-800">
            {sidebarOpen && (
              <h1 className="text-xl font-bold">Cortex Flow</h1>
            )}
            <button
              onClick={toggleSidebar}
              className="p-2 rounded hover:bg-gray-800 transition-colors"
            >
              {sidebarOpen ? '←' : '→'}
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4">
            <ul className="space-y-2">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      className={`flex items-center gap-3 px-3 py-2 rounded transition-colors ${
                        isActive
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                      }`}
                    >
                      <span className="text-xl">{item.icon}</span>
                      {sidebarOpen && <span>{item.name}</span>}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Current Project Display */}
          <div className="p-4 border-t border-gray-800">
            {sidebarOpen && currentProject && (
              <div className="mb-3">
                <div className="text-xs text-gray-400 mb-1">Current Project</div>
                <button
                  onClick={() => setShowProjectSelector(!showProjectSelector)}
                  className="w-full text-left px-2 py-1.5 bg-gray-800 rounded hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-green-500"></span>
                      <span className="text-sm text-white font-medium truncate">
                        {currentProject.name}
                      </span>
                    </div>
                    <span className="text-gray-400">{showProjectSelector ? '▲' : '▼'}</span>
                  </div>
                </button>

                {/* Project Selector Dropdown */}
                {showProjectSelector && (
                  <div className="mt-2 bg-gray-800 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {projects?.map((project) => (
                      <button
                        key={project.name}
                        onClick={() => activateMutation.mutate(project.name)}
                        disabled={activateMutation.isPending || project.name === currentProject.name}
                        className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                          project.name === currentProject.name
                            ? 'bg-blue-600 text-white'
                            : 'text-gray-300 hover:bg-gray-700'
                        } ${
                          activateMutation.isPending ? 'opacity-50 cursor-not-allowed' : ''
                        } first:rounded-t-lg last:rounded-b-lg`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span
                              className={`w-2 h-2 rounded-full ${
                                project.active ? 'bg-green-500' : 'bg-gray-500'
                              }`}
                            ></span>
                            <span className="truncate">{project.name}</span>
                          </div>
                          {project.name === currentProject.name && (
                            <span className="text-xs">✓</span>
                          )}
                        </div>
                        {project.description && (
                          <div className="mt-0.5 text-xs text-gray-400 truncate ml-4">
                            {project.description}
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {sidebarOpen && !currentProject && (
              <div className="mb-3">
                <div className="text-xs text-gray-400 mb-1">No Active Project</div>
                <Link
                  to="/projects"
                  className="block w-full text-center px-2 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                >
                  Select Project
                </Link>
              </div>
            )}

            {/* Footer */}
            {sidebarOpen ? (
              <div className="text-xs text-gray-400">
                <div>Cortex Flow Editor</div>
                <div>v1.0.0</div>
              </div>
            ) : (
              <div className="text-center text-xs text-gray-400">v1.0</div>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
