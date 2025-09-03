'use client'

import { useState } from 'react'
import { Quote, ExternalLink, Book, FileText, Search, Filter } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

interface Citation {
  id: string
  citation_text: string
  source_title: string
  source_author?: string
  confidence_score: number
  context_snippet?: string
  source_type?: string
  page_number?: number
}

interface CitationPanelProps {
  citations: Citation[]
  onSourceClick?: (sourceId: string) => void
}

export function CitationPanel({ citations, onSourceClick }: CitationPanelProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedConfidence, setSelectedConfidence] = useState<'all' | 'high' | 'medium' | 'low'>('all')

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50 border-green-200'
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.8) return 'High'
    if (score >= 0.6) return 'Medium'
    return 'Low'
  }

  const getSourceIcon = (type?: string) => {
    switch (type) {
      case 'book': return Book
      case 'article': return FileText
      case 'document': return FileText
      default: return Quote
    }
  }

  const filteredCitations = citations.filter(citation => {
    const matchesSearch = !searchQuery || 
      citation.source_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      citation.source_author?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      citation.context_snippet?.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesConfidence = selectedConfidence === 'all' || 
      (selectedConfidence === 'high' && citation.confidence_score >= 0.8) ||
      (selectedConfidence === 'medium' && citation.confidence_score >= 0.6 && citation.confidence_score < 0.8) ||
      (selectedConfidence === 'low' && citation.confidence_score < 0.6)

    return matchesSearch && matchesConfidence
  })

  const groupedCitations = filteredCitations.reduce((acc, citation) => {
    const key = citation.source_title
    if (!acc[key]) {
      acc[key] = []
    }
    acc[key].push(citation)
    return acc
  }, {} as Record<string, Citation[]>)

  const confidenceStats = {
    high: citations.filter(c => c.confidence_score >= 0.8).length,
    medium: citations.filter(c => c.confidence_score >= 0.6 && c.confidence_score < 0.8).length,
    low: citations.filter(c => c.confidence_score < 0.6).length
  }

  if (citations.length === 0) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b">
          <h3 className="font-semibold flex items-center gap-2">
            <Quote className="h-5 w-5" />
            Citations
          </h3>
          <p className="text-sm text-muted-foreground">
            Source references will appear here
          </p>
        </div>
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center">
            <Quote className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              Start a conversation to see citations
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold flex items-center gap-2">
            <Quote className="h-5 w-5" />
            Citations ({citations.length})
          </h3>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search citations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 h-8"
          />
        </div>

        {/* Confidence Filter */}
        <div className="flex gap-1">
          {[
            { key: 'all', label: 'All', count: citations.length },
            { key: 'high', label: 'High', count: confidenceStats.high },
            { key: 'medium', label: 'Medium', count: confidenceStats.medium },
            { key: 'low', label: 'Low', count: confidenceStats.low }
          ].map(filter => (
            <Button
              key={filter.key}
              variant={selectedConfidence === filter.key ? 'default' : 'outline'}
              size="sm"
              className="text-xs h-7"
              onClick={() => setSelectedConfidence(filter.key as any)}
            >
              {filter.label} ({filter.count})
            </Button>
          ))}
        </div>
      </div>

      {/* Citations List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {Object.entries(groupedCitations).map(([sourceTitle, sourceCitations]) => {
            const firstCitation = sourceCitations[0]
            const Icon = getSourceIcon(firstCitation.source_type)

            return (
              <Card key={sourceTitle} className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-muted rounded-lg shrink-0">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-sm leading-tight">
                        {sourceTitle}
                      </CardTitle>
                      {firstCitation.source_author && (
                        <CardDescription className="text-xs">
                          by {firstCitation.source_author}
                        </CardDescription>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 shrink-0"
                      onClick={() => onSourceClick?.(firstCitation.id)}
                    >
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                </CardHeader>

                <CardContent className="pt-0 space-y-3">
                  {sourceCitations.map((citation, index) => (
                    <div key={citation.id} className="space-y-2">
                      {index > 0 && <Separator />}
                      
                      <div className="flex items-start gap-2">
                        <Badge variant="outline" className="text-xs shrink-0 mt-0.5">
                          {index + 1}
                        </Badge>
                        <div className="flex-1 min-w-0">
                          {citation.context_snippet && (
                            <blockquote className="text-sm italic text-muted-foreground border-l-2 border-muted pl-3 mb-2">
                              "{citation.context_snippet}"
                            </blockquote>
                          )}
                          
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Badge 
                                variant="outline" 
                                className={cn(
                                  "text-xs border",
                                  getConfidenceColor(citation.confidence_score)
                                )}
                              >
                                {getConfidenceLabel(citation.confidence_score)} 
                                ({(citation.confidence_score * 100).toFixed(0)}%)
                              </Badge>
                              
                              {citation.page_number && (
                                <span className="text-xs text-muted-foreground">
                                  p. {citation.page_number}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )
          })}

          {filteredCitations.length === 0 && (
            <div className="text-center py-8">
              <Search className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                No citations match your search
              </p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Footer Stats */}
      <div className="p-4 border-t bg-muted/30">
        <div className="text-xs text-muted-foreground space-y-1">
          <div className="flex justify-between">
            <span>Total Citations:</span>
            <span className="font-medium">{citations.length}</span>
          </div>
          <div className="flex justify-between">
            <span>Unique Sources:</span>
            <span className="font-medium">{Object.keys(groupedCitations).length}</span>
          </div>
          <div className="flex justify-between">
            <span>Avg. Confidence:</span>
            <span className="font-medium">
              {citations.length > 0 
                ? (citations.reduce((sum, c) => sum + c.confidence_score, 0) / citations.length * 100).toFixed(0)
                : 0}%
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}