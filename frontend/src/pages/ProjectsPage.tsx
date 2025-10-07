/**
 * Projects list page with CRUD operations
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import type { ProjectInfo, ProjectCreate } from '../types/api';

type ViewMode = 'list' | 'create' | 'edit';

export function ProjectsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedProject, setSelectedProject] = useState<ProjectInfo | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    version: '1.0.0',
  });

  const { currentProject, setCurrentProject } = useStore();
  const queryClient = useQueryClient();

  // Queries
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.listProjects(),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (project: ProjectCreate) => api.createProject(project),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setViewMode('list');
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ name, data }: { name: string; data: any }) =>
      api.updateProject(name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setViewMode('list');
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (name: string) => api.deleteProject(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const activateMutation = useMutation({
    mutationFn: (name: string) => api.activateProject(name),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setCurrentProject(data);
    },
  });

  // Handlers
  const resetForm = () => {
    setFormData({ name: '', description: '', version: '1.0.0' });
    setSelectedProject(null);
  };

  const handleCreate = () => {
    setViewMode('create');
    resetForm();
  };

  const handleEdit = (project: ProjectInfo) => {
    setSelectedProject(project);
    setFormData({
      name: project.name,
      description: project.description || '',
      version: project.version,
    });
    setViewMode('edit');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (viewMode === 'create') {
      createMutation.mutate(formData);
    } else if (viewMode === 'edit' && selectedProject) {
      updateMutation.mutate({
        name: selectedProject.name,
        data: formData,
      });
    }
  };

  const handleDelete = (project: ProjectInfo) => {
    if (confirm(`Delete project "${project.name}"? This action cannot be undone.`)) {
      deleteMutation.mutate(project.name);
    }
  };

  const handleActivate = (project: ProjectInfo) => {
    activateMutation.mutate(project.name);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-600">Loading projects...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-600">
          Error loading projects: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      </div>
    );
  }

  // List View
  if (viewMode === 'list') {
    return (
      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
            <p className="mt-2 text-gray-600">Manage your Cortex Flow projects</p>
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            + New Project
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects?.map((project) => (
            <div
              key={project.name}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
                  <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                    {project.description || 'No description'}
                  </p>
                </div>
                {project.active && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Active
                  </span>
                )}
              </div>

              <div className="mb-4 text-xs text-gray-500">
                Version: {project.version} • Created: {new Date(project.created_at).toLocaleDateString()}
              </div>

              <div className="flex gap-2">
                {!project.active && (
                  <button
                    onClick={() => handleActivate(project)}
                    disabled={activateMutation.isPending}
                    className="flex-1 px-3 py-1.5 text-sm text-green-600 border border-green-300 rounded hover:bg-green-50 disabled:opacity-50"
                  >
                    {activateMutation.isPending ? 'Activating...' : 'Activate'}
                  </button>
                )}
                <button
                  onClick={() => handleEdit(project)}
                  className="flex-1 px-3 py-1.5 text-sm text-blue-600 border border-blue-300 rounded hover:bg-blue-50"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(project)}
                  disabled={deleteMutation.isPending || project.active}
                  className="px-3 py-1.5 text-sm text-red-600 border border-red-300 rounded hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  title={project.active ? 'Cannot delete active project' : 'Delete project'}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>

        {projects?.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <svg
              className="w-16 h-16 mx-auto mb-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="text-gray-600 mb-4">No projects yet. Create your first project!</p>
            <button
              onClick={handleCreate}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              + New Project
            </button>
          </div>
        )}
      </div>
    );
  }

  // Create/Edit Form View
  return (
    <div className="p-6">
      <div className="mb-6">
        <button
          onClick={() => {
            setViewMode('list');
            resetForm();
          }}
          className="text-blue-600 hover:text-blue-700 mb-4 flex items-center gap-2"
        >
          ← Back to Projects
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          {viewMode === 'create' ? 'Create New Project' : 'Edit Project'}
        </h1>
        <p className="mt-2 text-gray-600">
          {viewMode === 'create'
            ? 'Set up a new Cortex Flow project'
            : `Editing project: ${selectedProject?.name}`}
        </p>
      </div>

      <div className="max-w-2xl">
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="my-project"
              required
              disabled={viewMode === 'edit'}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            {viewMode === 'edit' && (
              <p className="mt-1 text-xs text-gray-500">Project name cannot be changed</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Brief description of this project"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Version */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
            <input
              type="text"
              value={formData.version}
              onChange={(e) => setFormData({ ...formData, version: e.target.value })}
              placeholder="1.0.0"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={createMutation.isPending || updateMutation.isPending || !formData.name}
              className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createMutation.isPending || updateMutation.isPending
                ? 'Saving...'
                : viewMode === 'create'
                ? 'Create Project'
                : 'Update Project'}
            </button>
            <button
              type="button"
              onClick={() => {
                setViewMode('list');
                resetForm();
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>

          {/* Error Display */}
          {(createMutation.isError || updateMutation.isError) && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">
                Error: {createMutation.error?.message || updateMutation.error?.message}
              </p>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
