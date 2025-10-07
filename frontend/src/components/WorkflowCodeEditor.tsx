/**
 * Monaco-based JSON editor for workflows
 */

import { Editor } from '@monaco-editor/react';
import { useState, useEffect } from 'react';
import type { Workflow } from '../types/api';

interface WorkflowCodeEditorProps {
  workflow: Workflow | null;
  onChange: (workflow: Workflow | null) => void;
  onSave: () => void;
  onCancel: () => void;
  onValidate: () => void;
  onPreview: () => void;
  isLoading?: boolean;
  isSaving?: boolean;
  isValidating?: boolean;
}

export function WorkflowCodeEditor({
  workflow,
  onChange,
  onSave,
  onCancel,
  onValidate,
  onPreview,
  isLoading = false,
  isSaving = false,
  isValidating = false,
}: WorkflowCodeEditorProps) {
  const [jsonText, setJsonText] = useState(
    workflow ? JSON.stringify(workflow, null, 2) : ''
  );
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  // Update jsonText when workflow prop changes
  useEffect(() => {
    if (workflow) {
      setJsonText(JSON.stringify(workflow, null, 2));
      setJsonError(null);
      setHasChanges(false);
    }
  }, [workflow]);

  const handleEditorChange = (value: string | undefined) => {
    const text = value || '';
    setJsonText(text);
    setHasChanges(true);

    // Try to parse JSON
    try {
      if (text.trim() === '') {
        onChange(null);
        setJsonError(null);
        return;
      }

      const parsed = JSON.parse(text);
      onChange(parsed as Workflow);
      setJsonError(null);
    } catch (error) {
      onChange(null);
      setJsonError(error instanceof Error ? error.message : 'Invalid JSON');
    }
  };

  const handleFormat = () => {
    try {
      const parsed = JSON.parse(jsonText);
      const formatted = JSON.stringify(parsed, null, 2);
      setJsonText(formatted);
      onChange(parsed as Workflow);
      setJsonError(null);
    } catch (error) {
      // Keep current text if invalid
    }
  };

  const handleSave = () => {
    if (!jsonError && workflow) {
      onSave();
      setHasChanges(false);
    }
  };

  const handleCancel = () => {
    if (workflow) {
      setJsonText(JSON.stringify(workflow, null, 2));
    }
    setHasChanges(false);
    setJsonError(null);
    onCancel();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-gray-600">Loading workflow...</div>
      </div>
    );
  }

  const lineCount = jsonText.split('\n').length;

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between bg-gray-50 p-3 rounded-lg border">
        <div className="flex items-center gap-2">
          <button
            onClick={handleFormat}
            disabled={!!jsonError}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Format JSON (Prettier)"
          >
            ✨ Format
          </button>
          <button
            onClick={onValidate}
            disabled={!!jsonError || !workflow || isValidating}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Validate workflow structure"
          >
            {isValidating ? '⏳ Validating...' : '✓ Validate'}
          </button>
          <button
            onClick={onPreview}
            disabled={!!jsonError || !workflow}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Preview workflow execution"
          >
            👁️ Preview
          </button>
        </div>

        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>{lineCount} lines</span>
          {jsonError && (
            <span className="text-red-600 font-medium">
              ⚠️ JSON Error
            </span>
          )}
        </div>
      </div>

      {/* Editor */}
      <div className="border rounded-lg overflow-hidden">
        <Editor
          height="500px"
          defaultLanguage="json"
          value={jsonText}
          onChange={handleEditorChange}
          theme="vs-light"
          options={{
            minimap: { enabled: false },
            lineNumbers: 'on',
            wordWrap: 'off',
            fontSize: 13,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            formatOnPaste: true,
            formatOnType: false,
            renderWhitespace: 'selection',
            bracketPairColorization: { enabled: true },
          }}
        />
      </div>

      {/* Error Message */}
      {jsonError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <div>
              <div className="font-medium text-red-800">JSON Parse Error</div>
              <div className="text-sm text-red-600 mt-1">{jsonError}</div>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-2 border-t">
        <div className="text-sm text-gray-500">
          {hasChanges && !jsonError && '⚡ Unsaved changes'}
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleCancel}
            disabled={!hasChanges || isSaving}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges || !!jsonError || !workflow || isSaving}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? 'Saving...' : 'Save Workflow'}
          </button>
        </div>
      </div>
    </div>
  );
}
