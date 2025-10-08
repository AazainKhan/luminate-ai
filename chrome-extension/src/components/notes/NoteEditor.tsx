/**
 * NoteEditor Component
 * Modal for creating and editing notes
 */

import { useState, useEffect } from 'react';
import { useNotes } from '@/hooks/useNotes';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { Loader2, Save } from 'lucide-react';

interface NoteEditorProps {
  isOpen: boolean;
  onClose: () => void;
  noteId?: string | null;
  initialTopic?: string;
  initialContext?: any;
}

export function NoteEditor({
  isOpen,
  onClose,
  noteId,
  initialTopic,
  initialContext,
}: NoteEditorProps) {
  const notes = useNotes();
  const [topic, setTopic] = useState('');
  const [content, setContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Load existing note
  useEffect(() => {
    if (isOpen && noteId) {
      const note = notes.notes.find((n) => n.id === noteId);
      if (note) {
        setTopic(note.topic || '');
        setContent(note.content);
      }
    } else if (isOpen && !noteId) {
      // New note with optional initial values
      setTopic(initialTopic || '');
      setContent('');
    }
  }, [isOpen, noteId, notes.notes, initialTopic]);

  const handleSave = async () => {
    if (!content.trim()) return;

    setIsSaving(true);
    try {
      if (noteId) {
        // Update existing note
        await notes.update(noteId, content, topic || undefined);
      } else {
        // Create new note
        await notes.create(content, topic || undefined, initialContext);
      }
      onClose();
      setTopic('');
      setContent('');
    } catch (error) {
      console.error('Failed to save note:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    setTopic('');
    setContent('');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{noteId ? 'Edit Note' : 'Create Note'}</DialogTitle>
          <DialogDescription>
            {noteId ? 'Update your note' : 'Save important information for later'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Topic */}
          <div className="space-y-2">
            <Label htmlFor="topic">Topic (optional)</Label>
            <Input
              id="topic"
              placeholder="e.g. Machine Learning, Neural Networks"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>

          {/* Content */}
          <div className="space-y-2">
            <Label htmlFor="content">Content</Label>
            <Textarea
              id="content"
              placeholder="Write your note here..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={8}
              className="resize-none"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={handleClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!content.trim() || isSaving}
            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
          >
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Note
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

