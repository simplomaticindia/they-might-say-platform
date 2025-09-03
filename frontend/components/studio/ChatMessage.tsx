'use client'

import { useState } from 'react'
import { User, Quote, ExternalLink, Copy, Check } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface Citation {
  id: string
  citation_text: string
  source_title: string
  source_author?: string
  confidence_score: number
  context_snippet?: string
}

interface Message {
  id: string
  type: 'user' | 'lincoln'
  content: string
  timestamp: Date
  citations?: Citation[]
  metadata?: any
}

interface ChatMessageProps {
  message: Message
  isStreaming?: boolean
  onCitationClick?: (citation: Citation) => void
}

export function ChatMessage({ message, isStreaming = false, onCitationClick }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const isLincoln = message.type === 'lincoln'

  return (
    <div className={cn(
      "flex gap-4 group",
      isLincoln ? "justify-start" : "justify-end"
    )}>
      {isLincoln && (
        <Avatar className="w-10 h-10 border-2 border-amber-200">
          <AvatarImage src="/lincoln-avatar.jpg" alt="Abraham Lincoln" />
          <AvatarFallback className="bg-amber-100 text-amber-800 font-bold">
            AL
          </AvatarFallback>
        </Avatar>
      )}

      <div className={cn(
        "flex flex-col max-w-[80%]",
        !isLincoln && "items-end"
      )}>
        {/* Message Header */}
        <div className={cn(
          "flex items-center gap-2 mb-1",
          !isLincoln && "flex-row-reverse"
        )}>
          <span className="text-sm font-medium">
            {isLincoln ? 'Abraham Lincoln' : 'You'}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatTimestamp(message.timestamp)}
          </span>
          {isStreaming && (
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs text-green-600">Speaking...</span>
            </div>
          )}
        </div>

        {/* Message Content */}
        <Card className={cn(
          "relative",
          isLincoln 
            ? "bg-card border-amber-200" 
            : "bg-primary text-primary-foreground border-primary"
        )}>
          <CardContent className="p-4">
            <div className="prose prose-sm max-w-none">
              <p className="whitespace-pre-wrap leading-relaxed">
                {message.content}
              </p>
            </div>

            {/* Citations */}
            {message.citations && message.citations.length > 0 && (
              <div className="mt-4 pt-3 border-t border-amber-100">
                <div className="flex items-center gap-2 mb-2">
                  <Quote className="h-4 w-4 text-amber-600" />
                  <span className="text-sm font-medium text-amber-800">
                    Sources ({message.citations.length})
                  </span>
                </div>
                <div className="space-y-2">
                  {message.citations.map((citation, index) => (
                    <div
                      key={citation.id}
                      className="flex items-start gap-2 p-2 bg-amber-50 rounded-md cursor-pointer hover:bg-amber-100 transition-colors"
                      onClick={() => onCitationClick?.(citation)}
                    >
                      <Badge variant="outline" className="text-xs shrink-0">
                        {index + 1}
                      </Badge>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {citation.source_title}
                        </p>
                        {citation.source_author && (
                          <p className="text-xs text-muted-foreground">
                            by {citation.source_author}
                          </p>
                        )}
                        {citation.context_snippet && (
                          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                            "{citation.context_snippet}"
                          </p>
                        )}
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex items-center gap-1">
                            <div className={cn(
                              "w-2 h-2 rounded-full",
                              citation.confidence_score >= 0.8 ? "bg-green-500" :
                              citation.confidence_score >= 0.6 ? "bg-yellow-500" : "bg-red-500"
                            )} />
                            <span className="text-xs text-muted-foreground">
                              {(citation.confidence_score * 100).toFixed(0)}% confidence
                            </span>
                          </div>
                        </div>
                      </div>
                      <ExternalLink className="h-3 w-3 text-muted-foreground shrink-0" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Message Actions */}
            <div className={cn(
              "absolute top-2 opacity-0 group-hover:opacity-100 transition-opacity",
              isLincoln ? "right-2" : "left-2"
            )}>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={copyToClipboard}
                      className="h-6 w-6 p-0"
                    >
                      {copied ? (
                        <Check className="h-3 w-3 text-green-600" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {copied ? 'Copied!' : 'Copy message'}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </CardContent>
        </Card>

        {/* Metadata */}
        {message.metadata && (
          <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
            {message.metadata.context_chunks_used && (
              <span>{message.metadata.context_chunks_used} sources consulted</span>
            )}
            {message.metadata.model && (
              <span>• {message.metadata.model}</span>
            )}
          </div>
        )}
      </div>

      {!isLincoln && (
        <Avatar className="w-10 h-10">
          <AvatarFallback className="bg-primary text-primary-foreground">
            <User className="h-5 w-5" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}