import { render, screen } from '@testing-library/react'
import { ChatMessage } from '@/components/studio/chat-message'

const mockMessage = {
  id: '1',
  content: 'Hello, this is a test message',
  role: 'user' as const,
  timestamp: new Date('2023-01-01T12:00:00Z'),
}

const mockAssistantMessage = {
  id: '2',
  content: 'I appreciate your question about the Union. A house divided against itself cannot stand.',
  role: 'assistant' as const,
  timestamp: new Date('2023-01-01T12:01:00Z'),
  citations: [
    {
      id: 'citation-1',
      citation_text: 'A house divided against itself cannot stand',
      source_title: 'House Divided Speech',
      confidence_score: 0.95,
      context_snippet: 'I believe this government cannot endure permanently half slave and half free.'
    }
  ]
}

describe('ChatMessage Component', () => {
  it('renders user message correctly', () => {
    render(<ChatMessage message={mockMessage} />)
    
    expect(screen.getByText('Hello, this is a test message')).toBeInTheDocument()
    expect(screen.getByText('You')).toBeInTheDocument()
  })

  it('renders assistant message correctly', () => {
    render(<ChatMessage message={mockAssistantMessage} />)
    
    expect(screen.getByText(/I appreciate your question about the Union/)).toBeInTheDocument()
    expect(screen.getByText('Abraham Lincoln')).toBeInTheDocument()
  })

  it('displays citations for assistant messages', () => {
    render(<ChatMessage message={mockAssistantMessage} />)
    
    expect(screen.getByText('House Divided Speech')).toBeInTheDocument()
    expect(screen.getByText('95%')).toBeInTheDocument()
  })

  it('formats timestamp correctly', () => {
    render(<ChatMessage message={mockMessage} />)
    
    // Should display time in format like "12:00 PM"
    expect(screen.getByText(/12:00/)).toBeInTheDocument()
  })

  it('applies correct styling for user messages', () => {
    render(<ChatMessage message={mockMessage} />)
    
    const messageContainer = screen.getByTestId('chat-message')
    expect(messageContainer).toHaveClass('justify-end')
  })

  it('applies correct styling for assistant messages', () => {
    render(<ChatMessage message={mockAssistantMessage} />)
    
    const messageContainer = screen.getByTestId('chat-message')
    expect(messageContainer).toHaveClass('justify-start')
  })

  it('handles messages without citations', () => {
    const messageWithoutCitations = {
      ...mockAssistantMessage,
      citations: undefined
    }
    
    render(<ChatMessage message={messageWithoutCitations} />)
    
    expect(screen.getByText(/I appreciate your question about the Union/)).toBeInTheDocument()
    expect(screen.queryByText('House Divided Speech')).not.toBeInTheDocument()
  })

  it('handles empty citations array', () => {
    const messageWithEmptyCitations = {
      ...mockAssistantMessage,
      citations: []
    }
    
    render(<ChatMessage message={messageWithEmptyCitations} />)
    
    expect(screen.getByText(/I appreciate your question about the Union/)).toBeInTheDocument()
    expect(screen.queryByText('House Divided Speech')).not.toBeInTheDocument()
  })

  it('truncates long messages appropriately', () => {
    const longMessage = {
      ...mockMessage,
      content: 'This is a very long message that should be truncated or handled appropriately by the component to ensure good user experience and proper layout. '.repeat(10)
    }
    
    render(<ChatMessage message={longMessage} />)
    
    // The component should handle long content gracefully
    expect(screen.getByTestId('chat-message')).toBeInTheDocument()
  })
})