import { test, expect } from '@playwright/test'

test.describe('Studio Mode', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the API responses
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({
        json: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com',
          role: 'host',
          subscription_tier: 'premium'
        }
      })
    })

    await page.route('**/api/studio/episodes', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          json: [
            {
              id: '1',
              title: 'Test Episode',
              description: 'A test conversation',
              status: 'active',
              created_at: '2023-01-01T12:00:00Z'
            }
          ]
        })
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          json: {
            id: '2',
            title: 'New Episode',
            description: 'A new conversation',
            status: 'active',
            created_at: new Date().toISOString()
          }
        })
      }
    })

    await page.route('**/api/studio/conversation', async route => {
      await route.fulfill({
        json: {
          response: 'I appreciate your question about the Union. A house divided against itself cannot stand.',
          citations: [
            {
              id: 'citation-1',
              citation_text: 'A house divided against itself cannot stand',
              source_title: 'House Divided Speech',
              confidence_score: 0.95,
              context_snippet: 'I believe this government cannot endure permanently half slave and half free.'
            }
          ],
          metadata: {
            context_chunks_used: 3,
            model: 'gpt-4',
            response_time_ms: 1500
          }
        }
      })
    })

    // Navigate to studio mode
    await page.goto('/studio')
  })

  test('should display studio mode interface', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Studio Mode')
    await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible()
    await expect(page.locator('[data-testid="episode-selector"]')).toBeVisible()
  })

  test('should load existing episodes', async ({ page }) => {
    await expect(page.locator('[data-testid="episode-item"]')).toHaveCount(1)
    await expect(page.locator('text=Test Episode')).toBeVisible()
  })

  test('should create new episode', async ({ page }) => {
    await page.click('[data-testid="new-episode-button"]')
    
    await page.fill('[data-testid="episode-title-input"]', 'New Test Episode')
    await page.fill('[data-testid="episode-description-input"]', 'Description for new episode')
    
    await page.click('[data-testid="create-episode-button"]')
    
    await expect(page.locator('text=New Episode')).toBeVisible()
  })

  test('should send message and receive response', async ({ page }) => {
    // Select an episode first
    await page.click('[data-testid="episode-item"]:first-child')
    
    // Type a message
    const messageInput = page.locator('[data-testid="message-input"]')
    await messageInput.fill('What are your thoughts on preserving the Union?')
    
    // Send the message
    await page.click('[data-testid="send-button"]')
    
    // Check that user message appears
    await expect(page.locator('[data-testid="chat-message"]').last()).toContainText('What are your thoughts on preserving the Union?')
    
    // Check that assistant response appears
    await expect(page.locator('[data-testid="chat-message"]').last()).toContainText('I appreciate your question about the Union')
    
    // Check that citations are displayed
    await expect(page.locator('[data-testid="citation-panel"]')).toBeVisible()
    await expect(page.locator('text=House Divided Speech')).toBeVisible()
    await expect(page.locator('text=95%')).toBeVisible()
  })

  test('should display conversation history', async ({ page }) => {
    // Select an episode
    await page.click('[data-testid="episode-item"]:first-child')
    
    // Send a message to create history
    await page.fill('[data-testid="message-input"]', 'Hello Lincoln')
    await page.click('[data-testid="send-button"]')
    
    // Check that conversation history is visible
    await expect(page.locator('[data-testid="conversation-history"]')).toBeVisible()
    await expect(page.locator('[data-testid="chat-message"]')).toHaveCount(2) // User + Assistant
  })

  test('should handle empty message input', async ({ page }) => {
    // Select an episode
    await page.click('[data-testid="episode-item"]:first-child')
    
    // Try to send empty message
    await page.click('[data-testid="send-button"]')
    
    // Message should not be sent
    await expect(page.locator('[data-testid="chat-message"]')).toHaveCount(0)
  })

  test('should show loading state during message sending', async ({ page }) => {
    // Select an episode
    await page.click('[data-testid="episode-item"]:first-child')
    
    // Add delay to API response to test loading state
    await page.route('**/api/studio/conversation', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      await route.fulfill({
        json: {
          response: 'Test response',
          citations: [],
          metadata: {}
        }
      })
    })
    
    // Send message
    await page.fill('[data-testid="message-input"]', 'Test message')
    await page.click('[data-testid="send-button"]')
    
    // Check loading state
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible()
    
    // Wait for response
    await expect(page.locator('[data-testid="loading-indicator"]')).not.toBeVisible()
    await expect(page.locator('text=Test response')).toBeVisible()
  })

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/studio/conversation', async route => {
      await route.fulfill({
        status: 500,
        json: { error: 'Internal server error' }
      })
    })
    
    // Select an episode
    await page.click('[data-testid="episode-item"]:first-child')
    
    // Send message
    await page.fill('[data-testid="message-input"]', 'Test message')
    await page.click('[data-testid="send-button"]')
    
    // Check error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('text=Failed to send message')).toBeVisible()
  })

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    // Check that interface adapts to mobile
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible()
    
    // Open mobile menu
    await page.click('[data-testid="mobile-menu-button"]')
    await expect(page.locator('[data-testid="mobile-episode-list"]')).toBeVisible()
  })
})