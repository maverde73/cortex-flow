/**
 * Monaco Editor component for editing prompts
 */

import { Editor } from '@monaco-editor/react';
import { useState } from 'react';

interface PromptEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSave: () => void;
  onCancel: () => void;
  isLoading?: boolean;
  isSaving?: boolean;
  placeholder?: string;
}

export function PromptEditor({
  value,
  onChange,
  onSave,
  onCancel,
  isLoading = false,
  isSaving = false,
  placeholder = 'Enter your prompt here...',
}: PromptEditorProps) {
  const [localValue, setLocalValue] = useState(value);
  const hasChanges = localValue !== value;

  const handleEditorChange = (newValue: string | undefined) => {
    const text = newValue || '';
    setLocalValue(text);
    onChange(text);
  };

  const handleSave = () => {
    onSave();
  };

  const handleCancel = () => {
    setLocalValue(value);
    onChange(value);
    onCancel();
  };

  const characterCount = localValue.length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-gray-600">Loading prompt...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Editor */}
      <div className="border rounded-lg overflow-hidden">
        <Editor
          height="400px"
          defaultLanguage="markdown"
          value={localValue}
          onChange={handleEditorChange}
          theme="vs-light"
          options={{
            minimap: { enabled: false },
            lineNumbers: 'on',
            wordWrap: 'on',
            fontSize: 14,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            renderWhitespace: 'none',
          }}
        />
      </div>

      {/* Footer: Stats & Actions */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          <span className="font-medium">{characterCount}</span> characters
          {characterCount > 1000 && (
            <span className="ml-2 text-orange-600">
              • Long prompt (consider splitting)
            </span>
          )}
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
            disabled={!hasChanges || isSaving}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {/* Help text */}
      {localValue === '' && (
        <div className="text-sm text-gray-500 italic">{placeholder}</div>
      )}
    </div>
  );
}
