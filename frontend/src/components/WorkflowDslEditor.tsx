/**
 * DSL Editor for workflows using Monaco Editor with YAML syntax
 */

import { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Workflow } from '../types/api';

interface WorkflowDslEditorProps {
  workflow: Workflow | null;
  onChange: (workflow: Workflow) => void;
  onSave: () => void;
  onCancel: () => void;
  onValidate: () => void;
  isLoading?: boolean;
  isSaving?: boolean;
  isValidating?: boolean;
}

export function WorkflowDslEditor({
  workflow,
  onChange,
  onSave,
  onCancel,
  onValidate,
  isLoading = false,
  isSaving = false,
  isValidating = false,
}: WorkflowDslEditorProps) {
  const [dslContent, setDslContent] = useState<string>('');
  const [conversionError, setConversionError] = useState<string | null>(null);
  const [lastConvertedWorkflowHash, setLastConvertedWorkflowHash] = useState<string>('');

  // Convert workflow JSON to DSL on load
  const convertToDslMutation = useMutation({
    mutationFn: (wf: Workflow) =>
      api.convertWorkflowToDsl({ workflow: wf as any, format: 'yaml' }),
    onSuccess: (response, wf) => {
      setDslContent(response.dsl);
      setConversionError(null);
      setLastConvertedWorkflowHash(JSON.stringify(wf));
    },
    onError: (error: any) => {
      setConversionError(error.response?.data?.detail || error.message);
    },
  });

  // Parse DSL back to JSON
  const parseDslMutation = useMutation({
    mutationFn: (dsl: string) =>
      api.parseDslToWorkflow({ dsl, format: 'yaml' }),
    onSuccess: (response) => {
      onChange(response.workflow as Workflow);
      setConversionError(null);
    },
    onError: (error: any) => {
      setConversionError(error.response?.data?.detail || error.message);
    },
  });

  // Convert workflow to DSL when it loads or changes from other editors
  useEffect(() => {
    if (workflow) {
      const workflowHash = JSON.stringify(workflow);
      // Only convert if workflow actually changed (avoid loop)
      if (workflowHash !== lastConvertedWorkflowHash) {
        convertToDslMutation.mutate(workflow);
      }
    }
  }, [workflow, lastConvertedWorkflowHash]);

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setDslContent(value);
      // Auto-parse DSL to keep workflow in sync
      parseDslMutation.mutate(value);
    }
  };

  const handleFormat = () => {
    // Re-convert current workflow to DSL to format it
    if (workflow) {
      convertToDslMutation.mutate(workflow);
    }
  };

  if (isLoading || convertToDslMutation.isPending) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-gray-600">Loading workflow DSL...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Error Display */}
      {conversionError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <span className="text-red-600 text-xl">❌</span>
            <div>
              <div className="font-medium text-red-800">DSL Error</div>
              <div className="text-sm text-red-600 mt-1">{conversionError}</div>
            </div>
          </div>
        </div>
      )}

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <span className="text-blue-600 text-xl">ℹ️</span>
          <div className="flex-1">
            <div className="font-medium text-blue-800">YAML DSL Editor</div>
            <div className="text-sm text-blue-600 mt-1">
              Edit workflow using human-readable YAML syntax. Changes are automatically converted to
              JSON. Syntax: <code className="bg-blue-100 px-1 rounded">workflow</code>, <code className="bg-blue-100 px-1 rounded">nodes</code>, <code className="bg-blue-100 px-1 rounded">conditions</code>
            </div>
          </div>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="border rounded-lg overflow-hidden">
        <Editor
          height="500px"
          language="yaml"
          theme="vs-light"
          value={dslContent}
          onChange={handleEditorChange}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            readOnly: false,
            automaticLayout: true,
            tabSize: 2,
            wordWrap: 'on',
          }}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-2 border-t">
        <div className="flex gap-2">
          <button
            onClick={handleFormat}
            disabled={convertToDslMutation.isPending}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Re-format DSL"
          >
            🎨 Format
          </button>
          <button
            onClick={onValidate}
            disabled={isValidating || parseDslMutation.isPending}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isValidating ? '⏳ Validating...' : '✓ Validate'}
          </button>
        </div>

        <div className="flex gap-2">
          <button
            onClick={onCancel}
            disabled={isSaving}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={onSave}
            disabled={isSaving || parseDslMutation.isPending || !!conversionError}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
