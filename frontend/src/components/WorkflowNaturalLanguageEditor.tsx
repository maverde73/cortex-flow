/**
 * Natural Language Editor for workflows
 * Uses AI to convert between workflow JSON and human-readable descriptions
 */

import { useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Workflow } from '../types/api';
import { WorkflowChatAssistant } from './WorkflowChatAssistant';

interface WorkflowNaturalLanguageEditorProps {
  workflow: Workflow | null;
  onChange: (workflow: Workflow) => void;
  onSave: () => void;
  onCancel: () => void;
  onValidate: () => void;
  prompt: string;
  onPromptChange: (prompt: string) => void;
  isLoading?: boolean;
  isSaving?: boolean;
  isValidating?: boolean;
}

export function WorkflowNaturalLanguageEditor({
  workflow,
  onChange,
  onSave,
  onCancel,
  onValidate,
  prompt,
  onPromptChange,
  isLoading = false,
  isSaving = false,
  isValidating = false,
}: WorkflowNaturalLanguageEditorProps) {
  const [isModified, setIsModified] = useState(false);
  const [conversionError, setConversionError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showChat, setShowChat] = useState(false);


  // Parse natural language to workflow and update editors
  const fromNLMutation = useMutation({
    mutationFn: (promptText: string) =>
      api.parseNaturalLanguageToWorkflow({ prompt: promptText, language: 'it' }),
    onSuccess: (response) => {
      onChange(response.workflow as Workflow);
      setIsModified(false);
      setConversionError(null);
      setSuccessMessage('✅ Workflow aggiornato! Verifica nei tab Code/Visual/DSL.');
      setTimeout(() => setSuccessMessage(null), 5000);
    },
    onError: (error: any) => {
      setConversionError(error.response?.data?.detail || error.message);
    },
  });

  // Convert description to workflow (generate preview)
  const handleConvertToWorkflow = () => {
    if (prompt.trim()) {
      fromNLMutation.mutate(prompt);
    }
  };

  const handlePromptChange = (value: string) => {
    onPromptChange(value);
    setIsModified(true);
    setSuccessMessage(null);
  };

  // Handle workflow modification from chat
  const handleChatModification = (modifiedWorkflow: Workflow, explanation: string) => {
    onChange(modifiedWorkflow);
    setSuccessMessage(`✅ ${explanation}`);
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-gray-600">Caricamento workflow...</div>
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
              <div className="font-medium text-red-800">Errore AI</div>
              <div className="text-sm text-red-600 mt-1">{conversionError}</div>
            </div>
          </div>
        </div>
      )}

      {/* Success Message */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <span className="text-green-600 text-xl">✅</span>
            <div className="font-medium text-green-800">{successMessage}</div>
          </div>
        </div>
      )}

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <span className="text-blue-600 text-xl">💬</span>
          <div className="flex-1">
            <div className="font-medium text-blue-800">Editor Linguaggio Naturale (Italiano)</div>
            <div className="text-sm text-blue-600 mt-1">
              Descrivi il workflow in italiano oppure genera la descrizione dal JSON esistente.
              L'AI convertirà automaticamente tra testo e workflow strutturato.
            </div>
          </div>
          <button
            onClick={() => setShowChat(true)}
            disabled={!workflow}
            className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-600 to-pink-600 rounded-md hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-md flex items-center gap-2"
          >
            💬 Apri Chat AI
          </button>
        </div>
      </div>

      {/* Textarea Editor */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Descrizione Workflow
        </label>

        <textarea
          value={prompt}
          onChange={(e) => handlePromptChange(e.target.value)}
          placeholder="Scrivi qui la descrizione del workflow in italiano...&#10;&#10;Esempio:&#10;Questo workflow genera una newsletter settimanale:&#10;&#10;1. RICERCA&#10;   - Cerca informazioni recenti su {topic}&#10;   - Timeout: 5 minuti&#10;&#10;2. SCRITTURA&#10;   - Scrive la newsletter per {audience}&#10;   - Dipende da: ricerca completata"
          className="w-full h-96 p-4 text-sm font-mono border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          disabled={fromNLMutation.isPending}
        />

        <div className="flex items-center justify-between text-xs text-gray-500">
          <div>
            {prompt.length} caratteri
            {isModified && <span className="ml-2 text-yellow-600">● Non salvato</span>}
          </div>
          <div>
            {fromNLMutation.isPending && '⏳ Conversione a JSON...'}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-2 border-t">
        <div className="flex gap-2">
          {prompt && (
            <button
              onClick={handleConvertToWorkflow}
              disabled={fromNLMutation.isPending || !prompt.trim()}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="text-lg">✨</span>
              {fromNLMutation.isPending ? 'Conversione...' : '👁️ Converti e Anteprima'}
            </button>
          )}
          <button
            onClick={onValidate}
            disabled={isValidating || fromNLMutation.isPending || !workflow}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isValidating ? '⏳ Validazione...' : '✓ Valida'}
          </button>
        </div>

        <div className="flex gap-2">
          <button
            onClick={onCancel}
            disabled={isSaving}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Annulla
          </button>
          <button
            onClick={onSave}
            disabled={isSaving || fromNLMutation.isPending || !!conversionError || isModified}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            title={isModified ? 'Prima converti e accetta l\'anteprima' : 'Salva le modifiche nel database'}
          >
            {isSaving ? 'Salvataggio...' : 'Salva Modifiche'}
          </button>
        </div>
      </div>

      {/* Tips */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="text-sm text-gray-700">
          <div className="font-medium mb-2">💡 Suggerimenti:</div>
          <ul className="list-disc list-inside space-y-1 text-gray-600">
            <li>La descrizione viene generata automaticamente quando apri questo tab</li>
            <li>Modifica liberamente il testo per cambiare la logica del workflow</li>
            <li>Clicca <strong>"👁️ Converti e Anteprima"</strong> per aggiornare i tab Code/Visual/DSL</li>
            <li>Verifica le modifiche nei vari formati, poi usa il pulsante <strong>"✅ Salva"</strong> globale</li>
            <li>Oppure usa <strong>"💬 Chat AI"</strong> per modifiche guidate dalla conversazione</li>
            <li>Specifica dipendenze con <em>"Dipende da: nome_step"</em></li>
            <li>Per routing condizionale usa <em>"se... allora..."</em> o <em>"in caso di errore riprova"</em></li>
          </ul>
        </div>
      </div>

      {/* Chat Assistant Modal */}
      <WorkflowChatAssistant
        workflow={workflow}
        onWorkflowModified={handleChatModification}
        isOpen={showChat}
        onClose={() => setShowChat(false)}
      />
    </div>
  );
}
