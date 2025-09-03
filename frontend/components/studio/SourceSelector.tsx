'use client'

import { useState, useEffect } from 'react'
import { Search, Book, FileText, File, Check, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/components/ui/use-toast'
import { apiClient } from '@/lib/api-client'
import { cn } from '@/lib/utils'

interface Source {
  id: string
  title: string
  description?: string
  source_type: string
  author?: string
  reliability_score: number
  tags: string[]
  document_count: number
  total_chunks: number
  created_at: string
}

interface SourceSelectorProps {
  selectedSources: string[]
  onSourcesChange: (sourceIds: string[]) => void
}

export function SourceSelector({ selectedSources, onSourcesChange }: SourceSelectorProps) {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [reliabilityFilter, setReliabilityFilter] = useState<string>('all')
  const { toast } = useToast()

  const sourceTypes = [
    { value: 'all', label: 'All Types' },
    { value: 'book', label: 'Books' },
    { value: 'article', label: 'Articles' },
    { value: 'document', label: 'Documents' },
    { value: 'letter', label: 'Letters' },
    { value: 'speech', label: 'Speeches' },
    { value: 'manuscript', label: 'Manuscripts' },
    { value: 'other', label: 'Other' }
  ]

  const reliabilityLevels = [
    { value: 'all', label: 'All Reliability' },
    { value: 'high', label: 'High (80%+)' },
    { value: 'medium', label: 'Medium (60-79%)' },
    { value: 'low', label: 'Low (<60%)' }
  ]

  useEffect(() => {
    loadSources()
  }, [])

  const loadSources = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/sources')
      setSources(response.data)
    } catch (error) {
      console.error('Error loading sources:', error)
      toast({
        title: 'Error',
        description: 'Failed to load sources',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'book': return Book
      case 'article': return FileText
      case 'document': return File
      case 'letter': return FileText
      case 'speech': return FileText
      case 'manuscript': return File
      default: return File
    }
  }

  const getReliabilityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50 border-green-200'
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  const getReliabilityLabel = (score: number) => {
    if (score >= 0.8) return 'High'
    if (score >= 0.6) return 'Medium'
    return 'Low'
  }

  const filteredSources = sources.filter(source => {
    const matchesSearch = !searchQuery || 
      source.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      source.author?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      source.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesType = typeFilter === 'all' || source.source_type === typeFilter

    const matchesReliability = reliabilityFilter === 'all' ||
      (reliabilityFilter === 'high' && source.reliability_score >= 0.8) ||
      (reliabilityFilter === 'medium' && source.reliability_score >= 0.6 && source.reliability_score < 0.8) ||
      (reliabilityFilter === 'low' && source.reliability_score < 0.6)

    return matchesSearch && matchesType && matchesReliability
  })

  const toggleSource = (sourceId: string) => {
    if (selectedSources.includes(sourceId)) {
      onSourcesChange(selectedSources.filter(id => id !== sourceId))
    } else {
      onSourcesChange([...selectedSources, sourceId])
    }
  }

  const selectAll = () => {
    onSourcesChange(filteredSources.map(s => s.id))
  }

  const clearAll = () => {
    onSourcesChange([])
  }

  const selectedCount = selectedSources.length
  const totalChunks = sources
    .filter(s => selectedSources.includes(s.id))
    .reduce((sum, s) => sum + s.total_chunks, 0)

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <Label className="text-base font-semibold">Source Selection</Label>
        <p className="text-sm text-muted-foreground">
          Choose which sources Lincoln can reference in conversations
        </p>
      </div>

      {/* Selection Summary */}
      {selectedCount > 0 && (
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">
                  {selectedCount} source{selectedCount !== 1 ? 's' : ''} selected
                </p>
                <p className="text-sm text-muted-foreground">
                  {totalChunks.toLocaleString()} total chunks available
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={clearAll}>
                <X className="h-4 w-4 mr-2" />
                Clear All
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search sources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="flex gap-2">
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {sourceTypes.map(type => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={reliabilityFilter} onValueChange={setReliabilityFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {reliabilityLevels.map(level => (
                <SelectItem key={level.value} value={level.value}>
                  {level.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button variant="outline" size="sm" onClick={selectAll}>
            Select All ({filteredSources.length})
          </Button>
        </div>
      </div>

      {/* Sources List */}
      <ScrollArea className="h-96">
        <div className="space-y-2">
          {loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-4 h-4 bg-muted rounded"></div>
                      <div className="flex-1">
                        <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                        <div className="h-3 bg-muted rounded w-1/2"></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredSources.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-8">
                <Search className="h-8 w-8 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">
                  No sources match your criteria
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredSources.map(source => {
              const Icon = getSourceIcon(source.source_type)
              const isSelected = selectedSources.includes(source.id)
              
              return (
                <Card
                  key={source.id}
                  className={cn(
                    "cursor-pointer transition-colors hover:bg-muted/50",
                    isSelected && "ring-2 ring-primary bg-primary/5"
                  )}
                  onClick={() => toggleSource(source.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <Checkbox
                        checked={isSelected}
                        onChange={() => toggleSource(source.id)}
                        className="mt-1"
                      />
                      
                      <div className="p-2 bg-muted rounded-lg">
                        <Icon className="h-4 w-4" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium truncate">{source.title}</h4>
                            {source.author && (
                              <p className="text-sm text-muted-foreground">
                                by {source.author}
                              </p>
                            )}
                          </div>
                          <div className="flex items-center gap-2 ml-2">
                            <Badge variant="outline" className="text-xs">
                              {source.source_type}
                            </Badge>
                            <Badge 
                              variant="outline" 
                              className={cn(
                                "text-xs border",
                                getReliabilityColor(source.reliability_score)
                              )}
                            >
                              {getReliabilityLabel(source.reliability_score)}
                            </Badge>
                          </div>
                        </div>
                        
                        {source.description && (
                          <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                            {source.description}
                          </p>
                        )}
                        
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <div className="flex items-center gap-3">
                            <span>{source.document_count} documents</span>
                            <span>{source.total_chunks.toLocaleString()} chunks</span>
                          </div>
                          <span>
                            {new Date(source.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        
                        {source.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {source.tags.slice(0, 3).map(tag => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                            {source.tags.length > 3 && (
                              <Badge variant="secondary" className="text-xs">
                                +{source.tags.length - 3} more
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                      
                      {isSelected && (
                        <Check className="h-5 w-5 text-primary mt-1" />
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t">
        <div className="flex justify-between">
          <span>Available Sources:</span>
          <span>{sources.length}</span>
        </div>
        <div className="flex justify-between">
          <span>Filtered Results:</span>
          <span>{filteredSources.length}</span>
        </div>
        <div className="flex justify-between">
          <span>Selected:</span>
          <span>{selectedCount}</span>
        </div>
      </div>
    </div>
  )
}