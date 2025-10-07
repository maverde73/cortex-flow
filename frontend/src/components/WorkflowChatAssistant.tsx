/**
 * Workflow Chat Assistant
 * Interactive AI chat for modifying workflows through conversation
 */

import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Workflow, ChatMessage } from '../types/api';

interface WorkflowChatAssistantProps {
  workflow: Workflow | null;
  onWorkflowModified: (workflow: Workflow, explanation: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export function WorkflowChatAssistant({
  workflow,
  onWorkflowModified,
  isOpen,
  onClose,
}: WorkflowChatAssistantProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [pendingChanges, setPendingChanges] = useState<string[] | null>(null);
  const [pendingWorkflow, setPendingWorkflow] = useState<Workflow | null>(null);
  const [pendingExplanation, setPendingExplanation] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: (userMessage: string) => {
      if (!workflow) throw new Error('No workflow loaded');

      return api.chatModifyWorkflow({
        workflow: workflow as any,
        message: userMessage,
        history: messages,
        language: 'it',
      });
    },
    onSuccess: (response) => {
      // Add assistant response to messages
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.explanation,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Store pending changes for user to review
      setPendingChanges(response.changes);
      setPendingWorkflow(response.workflow as Workflow);
      setPendingExplanation(response.explanation);
    },
    onError: (error: any) => {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `❌ Errore: ${error.response?.data?.detail || error.message}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    },
  });

  const handleSend = () => {
    if (!input.trim() || chatMutation.isPending) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input.trim(),
    };

    // Add user message to conversation
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    // Clear any pending changes when sending new message
    setPendingChanges(null);
    setPendingWorkflow(null);
    setPendingExplanation('');

    // Send to AI
    chatMutation.mutate(input.trim());
  };

  const handleApplyChanges = () => {
    if (pendingWorkflow) {
      onWorkflowModified(pendingWorkflow, pendingExplanation);
      setPendingChanges(null);
      setPendingWorkflow(null);
      setPendingExplanation('');
    }
  };

  const handleDiscardChanges = () => {
    setPendingChanges(null);
    setPendingWorkflow(null);
    setPendingExplanation('');
  };

  const handleNewChat = () => {
    setMessages([]);
    setInput('');
    setPendingChanges(null);
    setPendingWorkflow(null);
    setPendingExplanation('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl h-[700px] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-lg">
          <div className="flex items-center gap-2">
            <span className="text-2xl">💬</span>
            <div>
              <h2 className="text-lg font-bold">Assistente AI Workflow</h2>
              <p className="text-xs opacity-90">Modifica il workflow tramite conversazione</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleNewChat}
              className="px-3 py-1.5 text-sm font-medium bg-white/20 hover:bg-white/30 rounded-md"
              title="Nuova conversazione"
            >
              🔄 Nuova Chat
            </button>
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-sm font-medium bg-white/20 hover:bg-white/30 rounded-md"
            >
              ✕ Chiudi
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-8">
              <div className="text-6xl mb-4">💬</div>
              <p className="text-lg font-medium">Benvenuto nell'Assistente AI!</p>
              <p className="text-sm mt-2">
                Scrivi un messaggio per modificare il workflow in linguaggio naturale.
              </p>
              <div className="mt-6 text-left max-w-md mx-auto bg-white p-4 rounded-lg border">
                <div className="font-medium text-gray-700 mb-2">Esempi di richieste:</div>
                <ul className="text-sm space-y-1 text-gray-600">
                  <li>• "aggiungi un timeout di 10 minuti al nodo di ricerca"</li>
                  <li>• "se la query fallisce, riprova massimo 3 volte"</li>
                  <li>• "esegui ricerca e analisi in parallelo"</li>
                  <li>• "aggiungi un nodo di validazione dopo l'analisi"</li>
                </ul>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}
              >
                <div className="text-xs font-medium mb-1 opacity-70">
                  {msg.role === 'user' ? '👤 Tu' : '🤖 Assistente AI'}
                </div>
                <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          ))}

          {chatMutation.isPending && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 max-w-[80%]">
                <div className="text-xs font-medium mb-1 opacity-70">🤖 Assistente AI</div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <div className="animate-pulse">⏳</div>
                  <span>Sto analizzando la richiesta...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Pending Changes Preview */}
        {pendingChanges && pendingChanges.length > 0 && (
          <div className="border-t bg-yellow-50 p-4">
            <div className="flex items-start gap-2">
              <span className="text-2xl">⚠️</span>
              <div className="flex-1">
                <div className="font-medium text-yellow-900">Modifiche proposte:</div>
                <ul className="text-sm text-yellow-800 mt-1 space-y-1">
                  {pendingChanges.map((change, idx) => (
                    <li key={idx}>• {change}</li>
                  ))}
                </ul>
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={handleApplyChanges}
                    className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700"
                  >
                    ✅ Applica Modifiche
                  </button>
                  <button
                    onClick={handleDiscardChanges}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    ❌ Scarta
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t bg-white rounded-b-lg">
          <div className="flex gap-2 items-end">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                // Send on Enter, new line on Shift+Enter
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Scrivi un messaggio... (Shift+Enter per andare a capo, Enter per inviare)"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[60px] max-h-[200px]"
              disabled={chatMutation.isPending || !workflow}
              rows={2}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || chatMutation.isPending || !workflow}
              className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {chatMutation.isPending ? (
                <>⏳ Invio...</>
              ) : (
                <>📤 Invia</>
              )}
            </button>
          </div>
          <div className="text-xs text-gray-500 mt-1">
            💡 Usa <kbd className="px-1 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs">Shift + Enter</kbd> per andare a capo
          </div>
        </div>
      </div>
    </div>
  );
}
