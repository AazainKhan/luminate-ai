/**
 * useNotes Hook
 * Manages notes with local and cloud sync
 */

import { useState, useEffect, useCallback } from 'react';
import { createNote, fetchNotes, updateNote, deleteNote, Note } from '@/services/api';
import { getStudentId } from '@/utils/studentId';

const LOCAL_STORAGE_KEY = 'luminate_notes';

interface NotesState {
  notes: Note[];
  isLoading: boolean;
  isSyncing: boolean;
  error: string | null;
}

export function useNotes() {
  const [state, setState] = useState<NotesState>({
    notes: [],
    isLoading: true,
    isSyncing: false,
    error: null,
  });

  /**
   * Load notes from local storage
   */
  const loadLocalNotes = useCallback((): Note[] => {
    try {
      const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('Failed to load local notes:', error);
      return [];
    }
  }, []);

  /**
   * Save notes to local storage
   */
  const saveLocalNotes = useCallback((notes: Note[]) => {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(notes));
    } catch (error) {
      console.error('Failed to save local notes:', error);
    }
  }, []);

  /**
   * Sync notes with backend
   */
  const syncNotes = useCallback(async () => {
    setState(prev => ({ ...prev, isSyncing: true }));

    try {
      const studentId = await getStudentId();
      const cloudNotes = await fetchNotes(studentId);

      // Merge local and cloud notes (cloud takes precedence)
      const localNotes = loadLocalNotes();
      const mergedNotes = [...cloudNotes];

      // Add local notes that don't exist in cloud
      localNotes.forEach(localNote => {
        if (!cloudNotes.find(cn => cn.id === localNote.id)) {
          mergedNotes.push(localNote);
        }
      });

      // Sort by updated_at descending
      mergedNotes.sort((a, b) => 
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );

      setState(prev => ({
        ...prev,
        notes: mergedNotes,
        isSyncing: false,
        error: null,
      }));

      saveLocalNotes(mergedNotes);
    } catch (error) {
      // On sync failure, use local notes
      const localNotes = loadLocalNotes();
      setState(prev => ({
        ...prev,
        notes: localNotes,
        isSyncing: false,
        error: error instanceof Error ? error.message : 'Sync failed',
      }));
    }
  }, [loadLocalNotes, saveLocalNotes]);

  /**
   * Initial load
   */
  useEffect(() => {
    const init = async () => {
      // Load local notes immediately
      const localNotes = loadLocalNotes();
      setState(prev => ({
        ...prev,
        notes: localNotes,
        isLoading: false,
      }));

      // Then sync with backend
      await syncNotes();
    };

    init();
  }, [loadLocalNotes, syncNotes]);

  /**
   * Create a new note
   */
  const create = async (content: string, topic?: string, context?: any): Promise<Note | null> => {
    try {
      const studentId = await getStudentId();
      
      // Create note on backend
      const newNote = await createNote(studentId, content, topic, context);

      // Update local state
      setState(prev => {
        const updatedNotes = [newNote, ...prev.notes];
        saveLocalNotes(updatedNotes);
        return {
          ...prev,
          notes: updatedNotes,
          error: null,
        };
      });

      return newNote;
    } catch (error) {
      // On failure, create local-only note
      const localNote: Note = {
        id: `local_${Date.now()}`,
        student_id: await getStudentId(),
        content,
        topic,
        context,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      setState(prev => {
        const updatedNotes = [localNote, ...prev.notes];
        saveLocalNotes(updatedNotes);
        return {
          ...prev,
          notes: updatedNotes,
          error: 'Note saved locally only',
        };
      });

      return localNote;
    }
  };

  /**
   * Update an existing note
   */
  const update = async (noteId: string, content?: string, topic?: string): Promise<void> => {
    try {
      // Update on backend
      await updateNote(noteId, content, topic);

      // Update local state
      setState(prev => {
        const updatedNotes = prev.notes.map(note =>
          note.id === noteId
            ? {
                ...note,
                content: content ?? note.content,
                topic: topic ?? note.topic,
                updated_at: new Date().toISOString(),
              }
            : note
        );
        saveLocalNotes(updatedNotes);
        return {
          ...prev,
          notes: updatedNotes,
          error: null,
        };
      });
    } catch (error) {
      // Update locally even if backend fails
      setState(prev => {
        const updatedNotes = prev.notes.map(note =>
          note.id === noteId
            ? {
                ...note,
                content: content ?? note.content,
                topic: topic ?? note.topic,
                updated_at: new Date().toISOString(),
              }
            : note
        );
        saveLocalNotes(updatedNotes);
        return {
          ...prev,
          notes: updatedNotes,
          error: 'Note updated locally only',
        };
      });
    }
  };

  /**
   * Delete a note
   */
  const remove = async (noteId: string): Promise<void> => {
    try {
      // Delete from backend
      await deleteNote(noteId);

      // Update local state
      setState(prev => {
        const updatedNotes = prev.notes.filter(note => note.id !== noteId);
        saveLocalNotes(updatedNotes);
        return {
          ...prev,
          notes: updatedNotes,
          error: null,
        };
      });
    } catch (error) {
      // Delete locally even if backend fails
      setState(prev => {
        const updatedNotes = prev.notes.filter(note => note.id !== noteId);
        saveLocalNotes(updatedNotes);
        return {
          ...prev,
          notes: updatedNotes,
          error: 'Note deleted locally only',
        };
      });
    }
  };

  /**
   * Search notes
   */
  const search = (query: string): Note[] => {
    const lowerQuery = query.toLowerCase();
    return state.notes.filter(
      note =>
        note.content.toLowerCase().includes(lowerQuery) ||
        note.topic?.toLowerCase().includes(lowerQuery)
    );
  };

  /**
   * Filter by topic
   */
  const filterByTopic = (topic: string): Note[] => {
    return state.notes.filter(note => note.topic === topic);
  };

  /**
   * Get unique topics
   */
  const getTopics = (): string[] => {
    const topics = state.notes
      .map(note => note.topic)
      .filter((topic): topic is string => !!topic);
    return Array.from(new Set(topics));
  };

  return {
    // State
    notes: state.notes,
    isLoading: state.isLoading,
    isSyncing: state.isSyncing,
    error: state.error,

    // Actions
    create,
    update,
    remove,
    sync: syncNotes,

    // Utilities
    search,
    filterByTopic,
    getTopics,
  };
}

