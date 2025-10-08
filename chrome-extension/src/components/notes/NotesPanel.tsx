/**
 * NotesPanel Component
 * Sidebar panel for viewing and managing notes
 */

import { useState } from 'react';
import { useNotes } from '@/hooks/useNotes';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { Input } from '../ui/input';
import { NoteEditor } from './NoteEditor';
import { X, Plus, Search, StickyNote, Loader2, Trash2, Edit2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NotesPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NotesPanel({ isOpen, onClose }: NotesPanelProps) {
  const notes = useNotes();
  const [searchQuery, setSearchQuery] = useState('');
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);

  const filteredNotes = searchQuery
    ? notes.search(searchQuery)
    : notes.notes;

  const handleCreateNote = () => {
    setEditingNoteId(null);
    setIsEditorOpen(true);
  };

  const handleEditNote = (noteId: string) => {
    setEditingNoteId(noteId);
    setIsEditorOpen(true);
  };

  const handleDeleteNote = async (noteId: string) => {
    if (confirm('Are you sure you want to delete this note?')) {
      await notes.remove(noteId);
    }
  };

  return (
    <>
      {/* Panel Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 transition-opacity duration-300 animate-in fade-in"
          onClick={onClose}
        />
      )}

      {/* Panel */}
      <div
        className={cn(
          'fixed right-0 top-0 h-full w-80 bg-card border-l shadow-2xl z-50',
          'transform transition-transform duration-300 ease-out',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3 bg-card/80 backdrop-blur">
          <div className="flex items-center gap-2">
            <StickyNote className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold text-sm">Notes</h2>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCreateNote}
              className="h-8 w-8"
            >
              <Plus className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-8 w-8 hover:bg-destructive/10 hover:text-destructive"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="p-3 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search notes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9"
            />
          </div>
        </div>

        {/* Notes List */}
        <ScrollArea className="h-[calc(100vh-113px)]">
          <div className="p-4 space-y-2">
            {notes.isLoading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mb-2" />
                <p className="text-xs text-muted-foreground">Loading notes...</p>
              </div>
            ) : filteredNotes.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 p-4 mb-4">
                  <StickyNote className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-sm font-medium text-foreground">
                  {searchQuery ? 'No notes found' : 'No notes yet'}
                </p>
                <p className="text-xs text-muted-foreground mt-2 max-w-[200px]">
                  {searchQuery
                    ? 'Try a different search term'
                    : 'Create your first note by clicking the + button'}
                </p>
              </div>
            ) : (
              filteredNotes.map((note) => (
                <div
                  key={note.id}
                  className="group relative p-3 rounded-lg border bg-card hover:shadow-md transition-all duration-200"
                >
                  {/* Topic tag if present */}
                  {note.topic && (
                    <span className="text-xs font-medium text-primary mb-2 block">
                      {note.topic}
                    </span>
                  )}

                  {/* Content preview */}
                  <p className="text-sm line-clamp-3 mb-2 leading-relaxed">
                    {note.content}
                  </p>

                  {/* Timestamp */}
                  <p className="text-xs text-muted-foreground">
                    {new Date(note.updated_at).toLocaleDateString()} •{' '}
                    {new Date(note.updated_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>

                  {/* Actions (show on hover) */}
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleEditNote(note.id)}
                      className="h-6 w-6 bg-background/80 backdrop-blur"
                    >
                      <Edit2 className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteNote(note.id)}
                      className="h-6 w-6 bg-background/80 backdrop-blur hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))
            )}

            {/* Sync status */}
            {notes.isSyncing && (
              <div className="flex items-center justify-center gap-2 py-2 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Syncing...</span>
              </div>
            )}

            {notes.error && (
              <div className="text-xs text-orange-600 dark:text-orange-400 p-2 rounded bg-orange-50 dark:bg-orange-900/10">
                {notes.error}
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Note Editor Dialog */}
      <NoteEditor
        isOpen={isEditorOpen}
        onClose={() => {
          setIsEditorOpen(false);
          setEditingNoteId(null);
        }}
        noteId={editingNoteId}
      />
    </>
  );
}

