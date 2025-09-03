'use client'

import { useState, useEffect } from 'react'
import { Search, Calendar, MessageSquare, Download, Play, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog'
import { useToast } from '@/components/ui/use-toast'
import { apiClient } from '@/lib/api-client'
import { cn } from '@/lib/utils'

interface Episode {
  id: string
  title: string
  description?: string
  status: string
  created_at: string
  beat_count: number
  total_citations: number
  last_activity?: string
}

interface ConversationHistoryProps {
  onEpisodeSelect: (episode: Episode) => void
}

export function ConversationHistory({ onEpisodeSelect }: ConversationHistoryProps) {
  const [episodes, setEpisodes] = useState<Episode[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('recent')
  const { toast } = useToast()

  const statusOptions = [
    { value: 'all', label: 'All Episodes' },
    { value: 'active', label: 'Active' },
    { value: 'paused', label: 'Paused' },
    { value: 'completed', label: 'Completed' },
    { value: 'archived', label: 'Archived' }
  ]

  const sortOptions = [
    { value: 'recent', label: 'Most Recent' },
    { value: 'oldest', label: 'Oldest First' },
    { value: 'title', label: 'Title A-Z' },
    { value: 'beats', label: 'Most Exchanges' },
    { value: 'citations', label: 'Most Citations' }
  ]

  useEffect(() => {
    loadEpisodes()
  }, [])

  const loadEpisodes = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/studio/episodes?limit=100')
      setEpisodes(response.data)
    } catch (error) {
      console.error('Error loading episodes:', error)
      toast({
        title: 'Error',
        description: 'Failed to load conversation history',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const deleteEpisode = async (episodeId: string) => {
    try {
      await apiClient.delete(`/studio/episodes/${episodeId}`)
      setEpisodes(prev => prev.filter(ep => ep.id !== episodeId))
      toast({
        title: 'Success',
        description: 'Episode deleted successfully'
      })
    } catch (error) {
      console.error('Error deleting episode:', error)
      toast({
        title: 'Error',
        description: 'Failed to delete episode',
        variant: 'destructive'
      })
    }
  }

  const exportEpisode = async (episode: Episode) => {
    try {
      const response = await apiClient.get(`/studio/episodes/${episode.id}/export?format=markdown`)
      
      // Create and download file
      const blob = new Blob([response.data.content], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${episode.title.replace(/[^a-z0-9]/gi, '_')}.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast({
        title: 'Success',
        description: 'Episode exported successfully'
      })
    } catch (error) {
      console.error('Error exporting episode:', error)
      toast({
        title: 'Error',
        description: 'Failed to export episode',
        variant: 'destructive'
      })
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
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 1) return 'Today'
    if (diffDays === 2) return 'Yesterday'
    if (diffDays <= 7) return `${diffDays - 1} days ago`
    
    return date.toLocaleDateString([], {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    })
  }

  const filteredAndSortedEpisodes = episodes
    .filter(episode => {
      const matchesSearch = !searchQuery || 
        episode.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        episode.description?.toLowerCase().includes(searchQuery.toLowerCase())

      const matchesStatus = statusFilter === 'all' || episode.status === statusFilter

      return matchesSearch && matchesStatus
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'recent':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        case 'oldest':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        case 'title':
          return a.title.localeCompare(b.title)
        case 'beats':
          return b.beat_count - a.beat_count
        case 'citations':
          return b.total_citations - a.total_citations
        default:
          return 0
      }
    })

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="flex gap-2">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {statusOptions.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {sortOptions.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Episodes List */}
      <ScrollArea className="h-96">
        <div className="space-y-3">
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="p-4">
                    <div className="space-y-2">
                      <div className="h-4 bg-muted rounded w-3/4"></div>
                      <div className="h-3 bg-muted rounded w-1/2"></div>
                      <div className="h-3 bg-muted rounded w-1/4"></div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredAndSortedEpisodes.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <MessageSquare className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No conversations found</h3>
                <p className="text-muted-foreground text-center">
                  {episodes.length === 0 
                    ? "You haven't started any conversations yet"
                    : "Try adjusting your search or filter criteria"
                  }
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredAndSortedEpisodes.map(episode => (
              <Card
                key={episode.id}
                className="cursor-pointer transition-colors hover:bg-muted/50"
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div 
                      className="flex-1 min-w-0"
                      onClick={() => onEpisodeSelect(episode)}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(episode.status)}`} />
                        <h4 className="font-semibold truncate">{episode.title}</h4>
                        <Badge variant="outline" className="text-xs capitalize">
                          {episode.status}
                        </Badge>
                      </div>
                      
                      {episode.description && (
                        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                          {episode.description}
                        </p>
                      )}
                      
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          <span>{episode.beat_count} exchanges</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span>{episode.total_citations} citations</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          <span>{formatDate(episode.created_at)}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-1 ml-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          onEpisodeSelect(episode)
                        }}
                        className="h-8 w-8 p-0"
                      >
                        <Play className="h-3 w-3" />
                      </Button>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          exportEpisode(episode)
                        }}
                        className="h-8 w-8 p-0"
                      >
                        <Download className="h-3 w-3" />
                      </Button>
                      
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => e.stopPropagation()}
                            className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete Episode</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to delete "{episode.title}"? 
                              This will permanently remove the episode and all its conversation history. 
                              This action cannot be undone.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => deleteEpisode(episode.id)}
                              className="bg-red-600 hover:bg-red-700"
                            >
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Summary */}
      <div className="text-xs text-muted-foreground space-y-1 pt-3 border-t">
        <div className="flex justify-between">
          <span>Total Episodes:</span>
          <span>{episodes.length}</span>
        </div>
        <div className="flex justify-between">
          <span>Showing:</span>
          <span>{filteredAndSortedEpisodes.length}</span>
        </div>
        <div className="flex justify-between">
          <span>Total Exchanges:</span>
          <span>{episodes.reduce((sum, ep) => sum + ep.beat_count, 0)}</span>
        </div>
        <div className="flex justify-between">
          <span>Total Citations:</span>
          <span>{episodes.reduce((sum, ep) => sum + ep.total_citations, 0)}</span>
        </div>
      </div>
    </div>
  )
}