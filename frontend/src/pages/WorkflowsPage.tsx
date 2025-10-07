/**
 * Workflows management page with list and editor
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import { WorkflowList } from '../components/WorkflowList';
import { WorkflowCodeEditor } from '../components/WorkflowCodeEditor';
import { WorkflowVisualEditor } from '../components/WorkflowVisualEditor';
import { WorkflowDslEditor } from '../components/WorkflowDslEditor';
import { WorkflowNaturalLanguageEditor } from '../components/WorkflowNaturalLanguageEditor';
import { WorkflowPreview } from '../components/WorkflowPreview';
import { WorkflowGenerateModal } from '../components/WorkflowGenerateModal';
import type { Workflow, WorkflowInfo, WorkflowPreview as WorkflowPreviewType } from '../types/api';

type ViewMode = 'list' | 'edit' | 'create';
type EditorMode = 'code' | 'visual' | 'dsl' | 'natural';

export function WorkflowsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [editorMode, setEditorMode] = useState<EditorMode>('code');
  const [selectedWorkflowName, setSelectedWorkflowName] = useState<string | null>(null);
  const [editedWorkflow, setEditedWorkflow] = useState<Workflow | null>(null);
  const [originalWorkflow, setOriginalWorkflow] = useState<Workflow | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [naturalLanguagePrompt, setNaturalLanguagePrompt] = useState('');
  const [lastNLWorkflowHash, setLastNLWorkflowHash] = useState('');

  const { currentProject } = useStore();
  const queryClient = useQueryClient();

  const projectName = currentProject?.name || 'default';

  // Fetch workflows list
  const { data: workflows, isLoading: isLoadingList } = useQuery({
    queryKey: ['workflows', projectName],
    queryFn: () => api.listWorkflows(projectName),
  });

  // Fetch selected workflow
  const { data: selectedWorkflow, isLoading: isLoadingWorkflow } = useQuery({
    queryKey: ['workflow', projectName, selectedWorkflowName],
    queryFn: () => api.getWorkflow(projectName, selectedWorkflowName!),
    enabled: !!selectedWorkflowName && viewMode === 'edit',
  });

  // Fetch workflow preview
  const { data: previewData, isLoading: isLoadingPreview } = useQuery({
    queryKey: ['workflow-preview', projectName, selectedWorkflowName],
    queryFn: () => api.previewWorkflow(projectName, selectedWorkflowName!),
    enabled: showPreview && !!selectedWorkflowName,
  });

  // Mutations
  const updateWorkflowMutation = useMutation({
    mutationFn: (workflow: Workflow) =>
      api.updateWorkflow(projectName, selectedWorkflowName!, workflow),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows', projectName] });
      queryClient.invalidateQueries({ queryKey: ['workflow', projectName, selectedWorkflowName] });
      setViewMode('list');
      setSelectedWorkflowName(null);
    },
  });

  const deleteWorkflowMutation = useMutation({
    mutationFn: (workflowName: string) => api.deleteWorkflow(projectName, workflowName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows', projectName] });
    },
  });

  const validateWorkflowMutation = useMutation({
    mutationFn: (workflow: Workflow) =>
      api.validateWorkflow(projectName, { workflow }),
    onSuccess: (result) => {
      setValidationResult(result);
      setTimeout(() => setValidationResult(null), 5000);
    },
  });

  const createWorkflowMutation = useMutation({
    mutationFn: ({ name, workflow }: { name: string; workflow: Workflow }) =>
      api.createWorkflow(projectName, name, workflow),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows', projectName] });
      setShowGenerateModal(false);
    },
  });

  // Natural Language generation
  const generateNLMutation = useMutation({
    mutationFn: (workflow: Workflow) =>
      api.convertWorkflowToNaturalLanguage({ workflow: workflow as any, language: 'it' }),
    onSuccess: (response) => {
      setNaturalLanguagePrompt(response.prompt);
      if (editedWorkflow) {
        setLastNLWorkflowHash(JSON.stringify(editedWorkflow));
      }
    },
  });

  // Handlers
  const handleSelectWorkflow = (workflow: WorkflowInfo) => {
    // Reset state when selecting a new workflow
    setEditedWorkflow(null);
    setEditorMode('code'); // Reset to code mode
    setSelectedWorkflowName(workflow.name);
    setViewMode('edit');
  };

  const handleDeleteWorkflow = (workflowName: string) => {
    if (confirm(`Delete workflow "${workflowName}"?`)) {
      deleteWorkflowMutation.mutate(workflowName);
    }
  };

  const handleSave = () => {
    if (editedWorkflow && selectedWorkflowName) {
      updateWorkflowMutation.mutate(editedWorkflow);
    }
  };

  const handleCancel = () => {
    if (hasUnsavedChanges && originalWorkflow) {
      // Restore original workflow
      setEditedWorkflow(JSON.parse(JSON.stringify(originalWorkflow)));
      setHasUnsavedChanges(false);
    } else {
      // Go back to list
      setViewMode('list');
      setSelectedWorkflowName(null);
      setEditedWorkflow(null);
      setOriginalWorkflow(null);
      setHasUnsavedChanges(false);
    }
  };

  const handleValidate = () => {
    if (editedWorkflow) {
      validateWorkflowMutation.mutate(editedWorkflow);
    }
  };

  const handlePreview = () => {
    setShowPreview(true);
  };

  const handleGenerateWorkflow = (workflow: Workflow) => {
    createWorkflowMutation.mutate({ name: workflow.name, workflow });
  };

  // Update edited workflow when selected workflow loads or changes
  useEffect(() => {
    if (selectedWorkflow && viewMode === 'edit') {
      // Only update if workflow name changed or editedWorkflow is null
      if (!editedWorkflow || editedWorkflow.name !== selectedWorkflow.name) {
        setEditedWorkflow(selectedWorkflow);
        setOriginalWorkflow(JSON.parse(JSON.stringify(selectedWorkflow))); // Deep copy
        setHasUnsavedChanges(false);
      }
    }
  }, [selectedWorkflow, viewMode, editedWorkflow]);

  // Track changes to editedWorkflow
  useEffect(() => {
    if (editedWorkflow && originalWorkflow) {
      const hasChanges = JSON.stringify(editedWorkflow) !== JSON.stringify(originalWorkflow);
      setHasUnsavedChanges(hasChanges);
    }
  }, [editedWorkflow, originalWorkflow]);

  // Auto-generate NL description when switching to Natural tab
  useEffect(() => {
    if (editorMode === 'natural' && editedWorkflow) {
      const currentHash = JSON.stringify(editedWorkflow);

      // Generate if no prompt yet OR workflow has changed since last generation
      if (!naturalLanguagePrompt || currentHash !== lastNLWorkflowHash) {
        generateNLMutation.mutate(editedWorkflow);
      }
    }
  }, [editorMode, editedWorkflow]);

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Workflows</h1>
            <p className="mt-2 text-gray-600">
              Manage workflows for project: <span className="font-semibold">{projectName}</span>
            </p>
          </div>

          {viewMode === 'list' && (
            <button
              onClick={() => setShowGenerateModal(true)}
              className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-md hover:from-blue-700 hover:to-purple-700 shadow-md flex items-center gap-2"
            >
              ✨ Generate with AI
            </button>
          )}

          {viewMode === 'edit' && (
            <button
              onClick={() => setViewMode('list')}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              ← Back to List
            </button>
          )}
        </div>
      </div>

      {/* Validation Result */}
      {validationResult && (
        <div
          className={`mb-4 p-4 rounded-lg border ${
            validationResult.valid
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}
        >
          <div className="flex items-start gap-2">
            <span className="text-xl">
              {validationResult.valid ? '✅' : '❌'}
            </span>
            <div>
              <div
                className={`font-medium ${
                  validationResult.valid ? 'text-green-800' : 'text-red-800'
                }`}
              >
                {validationResult.valid ? 'Workflow Valid' : 'Workflow Invalid'}
              </div>
              {validationResult.message && (
                <div
                  className={`text-sm mt-1 ${
                    validationResult.valid ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {validationResult.message}
                </div>
              )}
              {validationResult.errors && (
                <ul className="mt-2 text-sm text-red-600 list-disc list-inside">
                  {validationResult.errors.map((error: string, index: number) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Unsaved Changes Banner */}
      {viewMode === 'edit' && hasUnsavedChanges && (
        <div className="mb-4 bg-yellow-50 border-2 border-yellow-400 rounded-lg p-4 shadow-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">⚠️</span>
              <div>
                <div className="font-bold text-yellow-900 text-lg">Modifiche non salvate</div>
                <div className="text-sm text-yellow-700 mt-0.5">
                  Il workflow è stato modificato. Salva le modifiche o annullale per tornare alla versione originale.
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleCancel}
                className="px-5 py-2.5 text-sm font-medium text-gray-700 bg-white border-2 border-gray-300 rounded-md hover:bg-gray-50 hover:border-gray-400 shadow-sm flex items-center gap-2"
              >
                <span className="text-lg">❌</span>
                Annulla Modifiche
              </button>
              <button
                onClick={handleSave}
                disabled={updateWorkflowMutation.isPending}
                className="px-5 py-2.5 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center gap-2"
              >
                <span className="text-lg">✅</span>
                {updateWorkflowMutation.isPending ? 'Salvataggio...' : 'Salva Workflow'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {viewMode === 'list' && (
        <div>
          {isLoadingList ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-gray-600">Loading workflows...</div>
            </div>
          ) : (
            <WorkflowList
              workflows={workflows || []}
              onSelect={handleSelectWorkflow}
              onDelete={handleDeleteWorkflow}
              selectedWorkflow={selectedWorkflowName || undefined}
              isDeleting={deleteWorkflowMutation.isPending}
            />
          )}
        </div>
      )}

      {viewMode === 'edit' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Edit Workflow: {selectedWorkflowName}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {editorMode === 'code'
                  ? 'Modify the workflow JSON structure'
                  : editorMode === 'visual'
                  ? 'Arrange workflow nodes visually'
                  : editorMode === 'dsl'
                  ? 'Edit workflow using human-readable YAML DSL'
                  : 'Describe workflow in natural language (Italian)'}
              </p>
            </div>

            {/* Editor Mode Switcher */}
            <div className="flex rounded-lg border border-gray-300 bg-gray-50 p-1">
              <button
                onClick={() => setEditorMode('code')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
                  editorMode === 'code'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                📝 Code
              </button>
              <button
                onClick={() => setEditorMode('visual')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
                  editorMode === 'visual'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🎨 Visual
              </button>
              <button
                onClick={() => setEditorMode('dsl')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
                  editorMode === 'dsl'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                📄 DSL
              </button>
              <button
                onClick={() => setEditorMode('natural')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
                  editorMode === 'natural'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                ✨ Natural
              </button>
            </div>
          </div>

          {editorMode === 'code' ? (
            <WorkflowCodeEditor
              workflow={editedWorkflow}
              onChange={setEditedWorkflow}
              onSave={handleSave}
              onCancel={handleCancel}
              onValidate={handleValidate}
              onPreview={handlePreview}
              isLoading={isLoadingWorkflow}
              isSaving={updateWorkflowMutation.isPending}
              isValidating={validateWorkflowMutation.isPending}
            />
          ) : editorMode === 'visual' ? (
            <WorkflowVisualEditor
              workflow={editedWorkflow}
              onChange={setEditedWorkflow}
              onSave={handleSave}
              onCancel={handleCancel}
              isLoading={isLoadingWorkflow}
              isSaving={updateWorkflowMutation.isPending}
            />
          ) : editorMode === 'dsl' ? (
            <WorkflowDslEditor
              workflow={editedWorkflow}
              onChange={setEditedWorkflow}
              onSave={handleSave}
              onCancel={handleCancel}
              onValidate={handleValidate}
              isLoading={isLoadingWorkflow}
              isSaving={updateWorkflowMutation.isPending}
              isValidating={validateWorkflowMutation.isPending}
            />
          ) : (
            <WorkflowNaturalLanguageEditor
              workflow={editedWorkflow}
              onChange={setEditedWorkflow}
              onSave={handleSave}
              onCancel={handleCancel}
              onValidate={handleValidate}
              prompt={naturalLanguagePrompt}
              onPromptChange={setNaturalLanguagePrompt}
              isLoading={isLoadingWorkflow}
              isSaving={updateWorkflowMutation.isPending}
              isValidating={validateWorkflowMutation.isPending}
            />
          )}
        </div>
      )}

      {/* Preview Modal */}
      {showPreview && (
        <WorkflowPreview
          preview={previewData || null}
          isLoading={isLoadingPreview}
          onClose={() => setShowPreview(false)}
        />
      )}

      {/* Generate Modal */}
      {showGenerateModal && (
        <WorkflowGenerateModal
          projectName={projectName}
          onClose={() => setShowGenerateModal(false)}
          onAccept={handleGenerateWorkflow}
        />
      )}
    </div>
  );
}
