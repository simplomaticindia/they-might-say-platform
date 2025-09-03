'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Mic, MicOff, Settings, History, Download, Play, Pause, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/components/ui/use-toast'
import { ChatMessage } from '@/components/studio/ChatMessage'
import { CitationPanel } from '@/components/studio/CitationPanel'
import { EpisodeSelector } from '@/components/studio/EpisodeSelector'
import { SourceSelector } from '@/components/studio/SourceSelector'
import { ConversationHistory } from '@/components/studio/ConversationHistory'
import { apiClient } from '@/lib/api-client'

interface Message {
  id: string
  type: 'user' | 'lincoln'
  content: string
  timestamp: Date
  citations?: Citation[]
  metadata?: any
}

interface Citation {
  id: string
  citation_text: string
  source_title: string
  source_author?: string
  confidence_score: number
  context_snippet?: string
}

interface Episode {
  id: string
  title: string
  description?: string
  status: string
  created_at: string
  beat_count: number
}

export default function StudioModePage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [currentEpisode, setCurrentEpisode] = useState<Episode | null>(null)
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [citations, setCitations] = useState<Citation[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  useEffect(() => {
    // Initialize WebSocket connection for real-time chat
    initializeWebSocket()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const initializeWebSocket = () => {
    try {
      const ws = apiClient.createWebSocket('/api/studio/ws/user123') // Replace with actual user ID
      
      ws.onopen = () => {
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        handleWebSocketMessage(data)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        // Attempt to reconnect after 3 seconds
        setTimeout(initializeWebSocket, 3000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error)
    }
  }

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'content':
        setStreamingMessage(prev => prev + data.content)
        break
        
      case 'complete':
        // Finalize the streaming message
        const newMessage: Message = {
          id: Date.now().toString(),
          type: 'lincoln',
          content: streamingMessage,
          timestamp: new Date(),
          citations: data.citations || [],
          metadata: data.metadata
        }
        
        setMessages(prev => [...prev, newMessage])
        setCitations(data.citations || [])
        setStreamingMessage('')
        setIsStreaming(false)
        setIsLoading(false)
        break
        
      case 'error':
        toast({
          title: 'Error',
          description: data.error,
          variant: 'destructive'
        })
        setIsStreaming(false)
        setIsLoading(false)
        setStreamingMessage('')
        break
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setIsStreaming(true)
    setStreamingMessage('')

    try {
      // Send message via WebSocket for real-time streaming
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'chat',
          message: inputMessage.trim(),
          episode_id: currentEpisode?.id,
          source_ids: selectedSources,
          history: messages.slice(-10).map(m => ({
            [m.type]: m.content
          }))
        }))
      } else {
        // Fallback to HTTP streaming
        await sendMessageHTTP(inputMessage.trim())
      }

      setInputMessage('')
    } catch (error) {
      console.error('Error sending message:', error)
      toast({
        title: 'Error',
        description: 'Failed to send message',
        variant: 'destructive'
      })
      setIsLoading(false)
      setIsStreaming(false)
    }
  }

  const sendMessageHTTP = async (message: string) => {
    try {
      const response = await fetch('/api/studio/conversation/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          message,
          episode_id: currentEpisode?.id,
          source_ids: selectedSources,
          conversation_history: messages.slice(-10).map(m => ({
            [m.type]: m.content
          }))
        })
      })

      if (!response.body) throw new Error('No response body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              handleWebSocketMessage(data)
            } catch (e) {
              // Ignore malformed JSON
            }
          }
        }
      }
    } catch (error) {
      console.error('HTTP streaming error:', error)
      throw error
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const startRecording = () => {
    // Voice recording implementation would go here
    setIsRecording(true)
    toast({
      title: 'Voice Recording',
      description: 'Voice recording feature coming soon!'
    })
  }

  const stopRecording = () => {
    setIsRecording(false)
  }

  const exportConversation = async () => {
    if (!currentEpisode) {
      toast({
        title: 'No Episode',
        description: 'Please select an episode to export',
        variant: 'destructive'
      })
      return
    }

    try {
      const response = await apiClient.get(`/episodes/${currentEpisode.id}/export?format=markdown`)
      
      // Create and download file
      const blob = new Blob([response.data.content], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${currentEpisode.title.replace(/[^a-z0-9]/gi, '_')}.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast({
        title: 'Success',
        description: 'Conversation exported successfully'
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to export conversation',
        variant: 'destructive'
      })
    }
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold">Studio Mode</h1>
              <p className="text-sm text-muted-foreground">
                Interactive conversation with Abraham Lincoln
              </p>
            </div>
            {currentEpisode && (
              <Badge variant="outline" className="ml-4">
                Episode: {currentEpisode.title}
              </Badge>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowHistory(true)}
            >
              <History className="h-4 w-4 mr-2" />
              History
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={exportConversation}
              disabled={!currentEpisode}
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSettings(true)}
            >
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4 max-w-4xl mx-auto">
              {messages.length === 0 && (
                <Card className="text-center py-12">
                  <CardContent>
                    <div className="text-6xl mb-4">🎩</div>
                    <h3 className="text-xl font-semibold mb-2">
                      Welcome to Studio Mode
                    </h3>
                    <p className="text-muted-foreground mb-4">
                      Start a conversation with Abraham Lincoln. Ask about history, 
                      seek wisdom, or discuss the challenges of leadership.
                    </p>
                    <div className="flex flex-wrap gap-2 justify-center">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setInputMessage("What were your thoughts on the challenges of preserving the Union?")}
                      >
                        Ask about the Union
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setInputMessage("How did you approach difficult decisions during the Civil War?")}
                      >
                        Leadership wisdom
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setInputMessage("What advice would you give to modern leaders?")}
                      >
                        Modern advice
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onCitationClick={(citation) => {
                    // Handle citation click - could open source details
                    console.log('Citation clicked:', citation)
                  }}
                />
              ))}
              
              {/* Streaming message */}
              {isStreaming && streamingMessage && (
                <ChatMessage
                  message={{
                    id: 'streaming',
                    type: 'lincoln',
                    content: streamingMessage,
                    timestamp: new Date()
                  }}
                  isStreaming={true}
                />
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t bg-card p-4">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <Input
                    placeholder="Ask Abraham Lincoln anything..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading}
                    className="min-h-[44px] resize-none"
                  />
                </div>
                
                <Button
                  variant={isRecording ? "destructive" : "outline"}
                  size="sm"
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isLoading}
                >
                  {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                </Button>
                
                <Button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                  size="sm"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              
              {selectedSources.length > 0 && (
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs text-muted-foreground">Sources:</span>
                  <div className="flex flex-wrap gap-1">
                    {selectedSources.slice(0, 3).map(sourceId => (
                      <Badge key={sourceId} variant="secondary" className="text-xs">
                        Source {sourceId.slice(-4)}
                      </Badge>
                    ))}
                    {selectedSources.length > 3 && (
                      <Badge variant="secondary" className="text-xs">
                        +{selectedSources.length - 3} more
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Sidebar - Citations */}
        <div className="w-80 border-l bg-card">
          <CitationPanel
            citations={citations}
            onSourceClick={(sourceId) => {
              // Handle source click - could open source details
              console.log('Source clicked:', sourceId)
            }}
          />
        </div>
      </div>

      {/* Dialogs */}
      <Dialog open={showHistory} onOpenChange={setShowHistory}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Conversation History</DialogTitle>
            <DialogDescription>
              Browse and manage your previous conversations with Lincoln
            </DialogDescription>
          </DialogHeader>
          <ConversationHistory
            onEpisodeSelect={(episode) => {
              setCurrentEpisode(episode)
              setShowHistory(false)
            }}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Studio Mode Settings</DialogTitle>
            <DialogDescription>
              Configure your conversation experience
            </DialogDescription>
          </DialogHeader>
          <Tabs defaultValue="episode" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="episode">Episode</TabsTrigger>
              <TabsTrigger value="sources">Sources</TabsTrigger>
            </TabsList>
            <TabsContent value="episode" className="space-y-4">
              <EpisodeSelector
                currentEpisode={currentEpisode}
                onEpisodeChange={setCurrentEpisode}
              />
            </TabsContent>
            <TabsContent value="sources" className="space-y-4">
              <SourceSelector
                selectedSources={selectedSources}
                onSourcesChange={setSelectedSources}
              />
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </div>
  )
}