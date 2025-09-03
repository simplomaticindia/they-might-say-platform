'use client'

import { useState, useEffect } from 'react'
import { Plus, Play, Pause, Square, Calendar, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/components/ui/use-toast'
import { apiClient } from '@/lib/api-client'

interface Episode {
  id: string
  title: string
  description?: string
  status: string
  created_at: string
  beat_count: number
  total_citations: number
  metadata?: any
}

interface EpisodeSelectorProps {
  currentEpisode: Episode | null
  onEpisodeChange: (episode: Episode | null) => void
}

export function EpisodeSelector({ currentEpisode, onEpisodeChange }: EpisodeSelectorProps) {
  const [episodes, setEpisodes] = useState<Episode[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newEpisodeTitle, setNewEpisodeTitle] = useState('')
  const [newEpisodeDescription, setNewEpisodeDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadEpisodes()
  }, [])

  const loadEpisodes = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/studio/episodes')
      setEpisodes(response.data)
    } catch (error) {
      console.error('Error loading episodes:', error)
      toast({
        title: 'Error',
        description: 'Failed to load episodes',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const createEpisode = async () => {
    if (!newEpisodeTitle.trim()) return

    try {
      setCreating(true)
      const response = await apiClient.post('/studio/episodes', {
        title: newEpisodeTitle.trim(),
        description: newEpisodeDescription.trim() || undefined
      })

      const newEpisode = response.data
      setEpisodes(prev => [newEpisode, ...prev])
      onEpisodeChange(newEpisode)
      
      setNewEpisodeTitle('')
      setNewEpisodeDescription('')
      setShowCreateDialog(false)
      
      toast({
        title: 'Success',
        description: 'Episode created successfully'
      })
    } catch (error) {
      console.error('Error creating episode:', error)
      toast({
        title: 'Error',
        description: 'Failed to create episode',
        variant: 'destructive'
      })
    } finally {
      setCreating(false)
    }
  }

  const updateEpisodeStatus = async (episodeId: string, status: string) => {
    try {
      await apiClient.put(`/studio/episodes/${episodeId}/status`, { status })
      
      setEpisodes(prev => prev.map(ep => 
        ep.id === episodeId ? { ...ep, status } : ep
      ))
      
      if (currentEpisode?.id === episodeId) {
        onEpisodeChange({ ...currentEpisode, status })
      }
      
      toast({
        title: 'Success',
        description: `Episode ${status}`
      })
    } catch (error) {
      console.error('Error updating episode status:', error)
      toast({
        title: 'Error',
        description: 'Failed to update episode status',
        variant: 'destructive'
      })
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return Play
      case 'paused': return Pause
      case 'completed': return Square
      default: return MessageSquare
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'paused': return 'bg-yellow-500'
      case 'completed': return 'bg-blue-500'
      case 'archived': return 'bg-gray-500'
      default: return 'bg-gray-400'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-4">
      {/* Current Episode */}
      <div>
        <Label className="text-base font-semibold">Current Episode</Label>
        <p className="text-sm text-muted-foreground mb-3">
          Select or create an episode to organize your conversation
        </p>
        
        {currentEpisode ? (
          <Card className="border-primary">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{currentEpisode.title}</CardTitle>
                  {currentEpisode.description && (
                    <CardDescription className="mt-1">
                      {currentEpisode.description}
                    </CardDescription>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(currentEpisode.status)}`} />
                  <Badge variant="outline" className="capitalize">
                    {currentEpisode.status}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <div className="flex items-center gap-4">
                  <span>{currentEpisode.beat_count} exchanges</span>
                  <span>{currentEpisode.total_citations} citations</span>
                </div>
                <span>{formatDate(currentEpisode.created_at)}</span>
              </div>
              
              <div className="flex gap-2 mt-3">
                {currentEpisode.status === 'active' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => updateEpisodeStatus(currentEpisode.id, 'paused')}
                  >
                    <Pause className="h-3 w-3 mr-1" />
                    Pause
                  </Button>
                )}
                
                {currentEpisode.status === 'paused' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => updateEpisodeStatus(currentEpisode.id, 'active')}
                  >
                    <Play className="h-3 w-3 mr-1" />
                    Resume
                  </Button>
                )}
                
                {(currentEpisode.status === 'active' || currentEpisode.status === 'paused') && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => updateEpisodeStatus(currentEpisode.id, 'completed')}
                  >
                    <Square className="h-3 w-3 mr-1" />
                    Complete
                  </Button>
                )}
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEpisodeChange(null)}
                >
                  Clear
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-8">
              <MessageSquare className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground text-center mb-4">
                No episode selected. Create a new episode or select from existing ones.
              </p>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Episode
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Episode List */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <Label className="text-base font-semibold">Recent Episodes</Label>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCreateDialog(true)}
          >
            <Plus className="h-4 w-4 mr-2" />
            New
          </Button>
        </div>

        <ScrollArea className="h-64">
          <div className="space-y-2">
            {loading ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <Card key={i} className="animate-pulse">
                    <CardContent className="p-3">
                      <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-muted rounded w-1/2"></div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : episodes.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-8">
                  <MessageSquare className="h-8 w-8 text-muted-foreground mb-2" />
                  <p className="text-sm text-muted-foreground">No episodes yet</p>
                </CardContent>
              </Card>
            ) : (
              episodes.map(episode => {
                const StatusIcon = getStatusIcon(episode.status)
                const isSelected = currentEpisode?.id === episode.id
                
                return (
                  <Card
                    key={episode.id}
                    className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                      isSelected ? 'ring-2 ring-primary' : ''
                    }`}
                    onClick={() => onEpisodeChange(episode)}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <StatusIcon className="h-4 w-4 text-muted-foreground" />
                            <h4 className="font-medium truncate">{episode.title}</h4>
                          </div>
                          {episode.description && (
                            <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                              {episode.description}
                            </p>
                          )}
                          <div className="flex items-center gap-3 text-xs text-muted-foreground">
                            <span>{episode.beat_count} exchanges</span>
                            <span>{episode.total_citations} citations</span>
                            <span>{formatDate(episode.created_at)}</span>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <div className={`w-2 h-2 rounded-full ${getStatusColor(episode.status)}`} />
                          <Badge variant="outline" className="text-xs capitalize">
                            {episode.status}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Create Episode Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Episode</DialogTitle>
            <DialogDescription>
              Start a new conversation episode with Abraham Lincoln
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Title *</Label>
              <Input
                id="title"
                placeholder="Enter episode title..."
                value={newEpisodeTitle}
                onChange={(e) => setNewEpisodeTitle(e.target.value)}
              />
            </div>
            
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe the topic or theme of this conversation..."
                value={newEpisodeDescription}
                onChange={(e) => setNewEpisodeDescription(e.target.value)}
                className="min-h-[80px]"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={createEpisode}
              disabled={!newEpisodeTitle.trim() || creating}
            >
              {creating ? 'Creating...' : 'Create Episode'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}