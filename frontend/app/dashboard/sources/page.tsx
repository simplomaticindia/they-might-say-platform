'use client'

import { useState, useEffect } from 'react'
import { Plus, Upload, Search, Filter, MoreHorizontal, FileText, Book, File } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/components/ui/use-toast'
import { CreateSourceDialog } from '@/components/sources/CreateSourceDialog'
import { UploadDocumentDialog } from '@/components/sources/UploadDocumentDialog'
import { SourceCard } from '@/components/sources/SourceCard'
import { apiClient } from '@/lib/api-client'

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

interface ProcessingStatus {
  total_documents: number
  completed: number
  processing: number
  chunking: number
  indexed: number
  error: number
}

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState<string>('all')
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [selectedSource, setSelectedSource] = useState<Source | null>(null)
  const [processingStatus, setProcessingStatus] = useState<Record<string, ProcessingStatus>>({})
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

  useEffect(() => {
    loadSources()
  }, [searchQuery, selectedType])

  const loadSources = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (searchQuery) params.append('search', searchQuery)
      if (selectedType !== 'all') params.append('source_type', selectedType)
      
      const response = await apiClient.get(`/sources?${params}`)
      setSources(response.data)
      
      // Load processing status for each source
      const statusPromises = response.data.map(async (source: Source) => {
        try {
          const statusResponse = await apiClient.get(`/sources/${source.id}/processing-status`)
          return { sourceId: source.id, status: statusResponse.data }
        } catch (error) {
          return { sourceId: source.id, status: null }
        }
      })
      
      const statuses = await Promise.all(statusPromises)
      const statusMap = statuses.reduce((acc, { sourceId, status }) => {
        if (status) acc[sourceId] = status
        return acc
      }, {} as Record<string, ProcessingStatus>)
      
      setProcessingStatus(statusMap)
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

  const handleSourceCreated = (newSource: Source) => {
    setSources(prev => [newSource, ...prev])
    setShowCreateDialog(false)
    toast({
      title: 'Success',
      description: 'Source created successfully'
    })
  }

  const handleDocumentUploaded = () => {
    loadSources() // Refresh to update document counts
    setShowUploadDialog(false)
    toast({
      title: 'Success',
      description: 'Document uploaded successfully'
    })
  }

  const handleDeleteSource = async (sourceId: string) => {
    try {
      await apiClient.delete(`/sources/${sourceId}`)
      setSources(prev => prev.filter(s => s.id !== sourceId))
      toast({
        title: 'Success',
        description: 'Source deleted successfully'
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete source',
        variant: 'destructive'
      })
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
    if (score >= 0.8) return 'bg-green-500'
    if (score >= 0.6) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const filteredSources = sources.filter(source => {
    const matchesSearch = !searchQuery || 
      source.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      source.author?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      source.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesType = selectedType === 'all' || source.source_type === selectedType
    
    return matchesSearch && matchesType
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Sources</h1>
          <p className="text-muted-foreground">
            Manage historical documents and sources for Lincoln conversations
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setShowUploadDialog(true)}
            disabled={sources.length === 0}
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload Document
          </Button>
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Source
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search sources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              {sourceTypes.find(t => t.value === selectedType)?.label}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {sourceTypes.map(type => (
              <DropdownMenuItem
                key={type.value}
                onClick={() => setSelectedType(type.value)}
              >
                {type.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Sources Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-muted rounded w-3/4"></div>
                <div className="h-3 bg-muted rounded w-1/2"></div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-3 bg-muted rounded"></div>
                  <div className="h-3 bg-muted rounded w-2/3"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredSources.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Book className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No sources found</h3>
            <p className="text-muted-foreground text-center mb-4">
              {sources.length === 0 
                ? "Get started by creating your first historical source"
                : "Try adjusting your search or filter criteria"
              }
            </p>
            {sources.length === 0 && (
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create First Source
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSources.map(source => {
            const Icon = getSourceIcon(source.source_type)
            const status = processingStatus[source.id]
            
            return (
              <SourceCard
                key={source.id}
                source={source}
                processingStatus={status}
                onDelete={() => handleDeleteSource(source.id)}
                onUpload={() => {
                  setSelectedSource(source)
                  setShowUploadDialog(true)
                }}
              />
            )
          })}
        </div>
      )}

      {/* Dialogs */}
      <CreateSourceDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSourceCreated={handleSourceCreated}
      />

      <UploadDocumentDialog
        open={showUploadDialog}
        onOpenChange={setShowUploadDialog}
        source={selectedSource}
        onDocumentUploaded={handleDocumentUploaded}
      />
    </div>
  )
}