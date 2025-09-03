'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/use-toast'
import { apiClient } from '@/lib/api-client'

interface Source {
  id: string
  title: string
  source_type: string
}

interface UploadDocumentDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  source: Source | null
  onDocumentUploaded: () => void
}

interface UploadFile {
  file: File
  id: string
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error'
  progress: number
  error?: string
}

export function UploadDocumentDialog({ 
  open, 
  onOpenChange, 
  source, 
  onDocumentUploaded 
}: UploadDocumentDialogProps) {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [metadata, setMetadata] = useState('')
  const [uploading, setUploading] = useState(false)
  const { toast } = useToast()

  const acceptedFileTypes = {
    'application/pdf': ['.pdf'],
    'text/plain': ['.txt'],
    'text/html': ['.html', '.htm'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
  }

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending' as const,
      progress: 0
    }))
    
    setFiles(prev => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFileTypes,
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: true
  })

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const uploadFiles = async () => {
    if (!source || files.length === 0) return

    setUploading(true)

    try {
      for (const uploadFile of files) {
        if (uploadFile.status !== 'pending') continue

        // Update status to uploading
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { ...f, status: 'uploading', progress: 0 }
            : f
        ))

        try {
          const formData = new FormData()
          formData.append('file', uploadFile.file)
          if (metadata.trim()) {
            formData.append('metadata', metadata.trim())
          }

          // Upload with progress tracking
          const response = await apiClient.post(
            `/sources/${source.id}/upload`,
            formData,
            {
              headers: {
                'Content-Type': 'multipart/form-data'
              },
              onUploadProgress: (progressEvent) => {
                const progress = progressEvent.total 
                  ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
                  : 0
                
                setFiles(prev => prev.map(f => 
                  f.id === uploadFile.id 
                    ? { ...f, progress }
                    : f
                ))
              }
            }
          )

          // Update to processing status
          setFiles(prev => prev.map(f => 
            f.id === uploadFile.id 
              ? { ...f, status: 'processing', progress: 100 }
              : f
          ))

          // Simulate processing time (in real app, you'd poll for status)
          setTimeout(() => {
            setFiles(prev => prev.map(f => 
              f.id === uploadFile.id 
                ? { ...f, status: 'completed' }
                : f
            ))
          }, 2000)

        } catch (error: any) {
          console.error('Upload error:', error)
          setFiles(prev => prev.map(f => 
            f.id === uploadFile.id 
              ? { 
                  ...f, 
                  status: 'error', 
                  error: error.response?.data?.detail || 'Upload failed'
                }
              : f
          ))
        }
      }

      // Check if all uploads completed successfully
      const allCompleted = files.every(f => f.status === 'completed' || f.status === 'error')
      if (allCompleted) {
        const successCount = files.filter(f => f.status === 'completed').length
        if (successCount > 0) {
          toast({
            title: 'Success',
            description: `${successCount} document(s) uploaded successfully`
          })
          onDocumentUploaded()
        }
      }

    } catch (error) {
      console.error('Upload process error:', error)
      toast({
        title: 'Error',
        description: 'Failed to upload documents',
        variant: 'destructive'
      })
    } finally {
      setUploading(false)
    }
  }

  const resetDialog = () => {
    setFiles([])
    setMetadata('')
    setUploading(false)
  }

  const handleClose = () => {
    if (!uploading) {
      resetDialog()
      onOpenChange(false)
    }
  }

  const getFileIcon = (file: File) => {
    if (file.type.includes('pdf')) return '📄'
    if (file.type.includes('word')) return '📝'
    if (file.type.includes('text')) return '📃'
    return '📄'
  }

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'pending': return <File className="h-4 w-4 text-muted-foreground" />
      case 'uploading': return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case 'processing': return <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error': return <AlertCircle className="h-4 w-4 text-red-500" />
    }
  }

  const getStatusLabel = (status: UploadFile['status']) => {
    switch (status) {
      case 'pending': return 'Ready to upload'
      case 'uploading': return 'Uploading...'
      case 'processing': return 'Processing...'
      case 'completed': return 'Completed'
      case 'error': return 'Error'
    }
  }

  const canUpload = files.length > 0 && files.some(f => f.status === 'pending') && !uploading
  const hasCompletedUploads = files.some(f => f.status === 'completed')

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Upload Documents</DialogTitle>
          <DialogDescription>
            {source ? (
              <>Upload documents to <strong>{source.title}</strong></>
            ) : (
              'Select a source first to upload documents'
            )}
          </DialogDescription>
        </DialogHeader>

        {!source ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">Please select a source from the sources page first.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* File Drop Zone */}
            <div
              {...getRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                ${isDragActive 
                  ? 'border-primary bg-primary/5' 
                  : 'border-muted-foreground/25 hover:border-primary/50'
                }
              `}
            >
              <input {...getInputProps()} />
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              {isDragActive ? (
                <p className="text-lg">Drop the files here...</p>
              ) : (
                <div>
                  <p className="text-lg mb-2">Drag & drop files here, or click to select</p>
                  <p className="text-sm text-muted-foreground">
                    Supports PDF, DOC, DOCX, TXT, HTML files up to 100MB each
                  </p>
                </div>
              )}
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="space-y-3">
                <h3 className="font-semibold">Files to Upload</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {files.map(uploadFile => (
                    <div key={uploadFile.id} className="flex items-center gap-3 p-3 border rounded-lg">
                      <div className="text-2xl">{getFileIcon(uploadFile.file)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium truncate">{uploadFile.file.name}</p>
                          <Badge variant="outline" className="text-xs">
                            {(uploadFile.file.size / 1024 / 1024).toFixed(1)} MB
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          {getStatusIcon(uploadFile.status)}
                          <span className="text-sm text-muted-foreground">
                            {getStatusLabel(uploadFile.status)}
                          </span>
                          {uploadFile.error && (
                            <span className="text-sm text-red-500">- {uploadFile.error}</span>
                          )}
                        </div>
                        {(uploadFile.status === 'uploading' || uploadFile.status === 'processing') && (
                          <Progress value={uploadFile.progress} className="mt-2 h-2" />
                        )}
                      </div>
                      {uploadFile.status === 'pending' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(uploadFile.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="space-y-2">
              <Label htmlFor="metadata">Additional Metadata (Optional)</Label>
              <Textarea
                id="metadata"
                placeholder="Add any additional information about these documents..."
                value={metadata}
                onChange={(e) => setMetadata(e.target.value)}
                className="min-h-[80px]"
              />
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={uploading}>
            {hasCompletedUploads ? 'Done' : 'Cancel'}
          </Button>
          {source && (
            <Button 
              onClick={uploadFiles} 
              disabled={!canUpload}
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload {files.filter(f => f.status === 'pending').length} File(s)
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}