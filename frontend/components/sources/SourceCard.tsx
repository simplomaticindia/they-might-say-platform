'use client'

import { useState } from 'react'
import { MoreHorizontal, Upload, Edit, Trash2, FileText, Book, File, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog'

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

interface SourceCardProps {
  source: Source
  processingStatus?: ProcessingStatus
  onDelete: () => void
  onUpload: () => void
}

export function SourceCard({ source, processingStatus, onDelete, onUpload }: SourceCardProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

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

  const getReliabilityLabel = (score: number) => {
    if (score >= 0.8) return 'High'
    if (score >= 0.6) return 'Medium'
    return 'Low'
  }

  const getProcessingProgress = () => {
    if (!processingStatus || processingStatus.total_documents === 0) return 100
    
    const completed = processingStatus.indexed + processingStatus.completed
    return (completed / processingStatus.total_documents) * 100
  }

  const getProcessingStatus = () => {
    if (!processingStatus) return { icon: CheckCircle, label: 'Ready', color: 'text-green-500' }
    
    if (processingStatus.error > 0) {
      return { icon: AlertCircle, label: 'Error', color: 'text-red-500' }
    }
    
    if (processingStatus.processing > 0 || processingStatus.chunking > 0) {
      return { icon: Clock, label: 'Processing', color: 'text-yellow-500' }
    }
    
    return { icon: CheckCircle, label: 'Ready', color: 'text-green-500' }
  }

  const Icon = getSourceIcon(source.source_type)
  const status = getProcessingStatus()
  const StatusIcon = status.icon

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-muted rounded-lg">
              <Icon className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <CardTitle className="text-lg truncate">{source.title}</CardTitle>
              <CardDescription className="flex items-center gap-2">
                {source.author && <span>{source.author}</span>}
                <Badge variant="outline" className="text-xs">
                  {source.source_type}
                </Badge>
              </CardDescription>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onUpload}>
                <Upload className="h-4 w-4 mr-2" />
                Upload Document
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Edit className="h-4 w-4 mr-2" />
                Edit Source
              </DropdownMenuItem>
              <DropdownMenuItem 
                className="text-red-600"
                onClick={() => setShowDeleteDialog(true)}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Description */}
        {source.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {source.description}
          </p>
        )}

        {/* Reliability Score */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Reliability</span>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${getReliabilityColor(source.reliability_score)}`} />
            <span className="text-sm">{getReliabilityLabel(source.reliability_score)}</span>
            <span className="text-xs text-muted-foreground">
              ({(source.reliability_score * 100).toFixed(0)}%)
            </span>
          </div>
        </div>

        {/* Processing Status */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <StatusIcon className={`h-4 w-4 ${status.color}`} />
              <span className="text-sm font-medium">{status.label}</span>
            </div>
            <span className="text-xs text-muted-foreground">
              {source.document_count} documents
            </span>
          </div>
          
          {processingStatus && processingStatus.total_documents > 0 && (
            <div className="space-y-1">
              <Progress value={getProcessingProgress()} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>
                  {processingStatus.indexed + processingStatus.completed} / {processingStatus.total_documents} processed
                </span>
                <span>{source.total_chunks} chunks</span>
              </div>
            </div>
          )}
        </div>

        {/* Tags */}
        {source.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
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

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t">
          <span className="text-xs text-muted-foreground">
            Created {new Date(source.created_at).toLocaleDateString()}
          </span>
          <Button variant="outline" size="sm" onClick={onUpload}>
            <Upload className="h-3 w-3 mr-1" />
            Upload
          </Button>
        </div>
      </CardContent>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Source</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{source.title}"? This will permanently remove 
              the source and all associated documents and chunks. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                onDelete()
                setShowDeleteDialog(false)
              }}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  )
}