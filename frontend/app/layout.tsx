import type { Metadata } from 'next'
import { Inter, Crimson_Text } from 'next/font/google'
import './globals.css'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

const crimsonText = Crimson_Text({ 
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  style: ['normal', 'italic'],
  variable: '--font-crimson',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'They Might Say - Listening to History through AI',
  description: 'A rigorously sourced conversation system featuring Abraham Lincoln with 100% citation coverage.',
  keywords: ['AI', 'History', 'Abraham Lincoln', 'Conversation', 'Citations', 'Historical Research'],
  authors: [{ name: 'They Might Say Team' }],
  creator: 'They Might Say',
  publisher: 'They Might Say',
  robots: 'index, follow',
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#8b6914',
  colorScheme: 'light dark',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://theymightsay.com',
    title: 'They Might Say - Listening to History through AI',
    description: 'A rigorously sourced conversation system featuring Abraham Lincoln with 100% citation coverage.',
    siteName: 'They Might Say',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'They Might Say - Listening to History through AI',
    description: 'A rigorously sourced conversation system featuring Abraham Lincoln with 100% citation coverage.',
    creator: '@theymightsay',
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${crimsonText.variable}`}>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#8b6914" />
        <meta name="color-scheme" content="light dark" />
        
        {/* Preload critical fonts */}
        <link
          rel="preload"
          href="/fonts/inter-var.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        <link
          rel="preload"
          href="/fonts/crimson-text-var.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        
        {/* Security headers via meta tags */}
        <meta httpEquiv="X-Content-Type-Options" content="nosniff" />
        <meta httpEquiv="X-Frame-Options" content="DENY" />
        <meta httpEquiv="X-XSS-Protection" content="1; mode=block" />
        <meta httpEquiv="Referrer-Policy" content="strict-origin-when-cross-origin" />
        
        {/* Favicon */}
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/site.webmanifest" />
      </head>
      <body className={`${inter.className} antialiased`}>
        <div id="root">
          {children}
        </div>
        
        {/* Portal for modals and overlays */}
        <div id="modal-root" />
        <div id="tooltip-root" />
        <div id="toast-root" />
      </body>
    </html>
  )
}