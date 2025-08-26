"use client"

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface AccessInstructionsProps {
  shareLink?: string
  shareToken?: string
  accessType?: 'public' | 'private' | 'token'
  instructions?: string[]
}

export default function AccessInstructions({
  shareLink,
  shareToken,
  accessType = 'public',
  instructions = []
}: AccessInstructionsProps) {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // You could add a toast notification here
  }

  const defaultInstructions = [
    "Share this link with authorized users",
    "Link access may be limited by time or usage",
    "Do not share this link publicly unless intended",
    "Contact administrator for access issues"
  ]

  const displayInstructions = instructions.length > 0 ? instructions : defaultInstructions

  return (
    <Card>
      <CardHeader>
        <CardTitle>Access Instructions</CardTitle>
        <CardDescription>
          How to access this shared resource
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {shareLink && (
          <div>
            <label className="text-sm font-medium">Share Link</label>
            <div className="flex gap-2 mt-1">
              <input
                type="text"
                value={shareLink}
                readOnly
                className="flex-1 px-3 py-2 text-sm border rounded-md bg-gray-50"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(shareLink)}
              >
                Copy
              </Button>
            </div>
          </div>
        )}

        {shareToken && (
          <div>
            <label className="text-sm font-medium">Access Token</label>
            <div className="flex gap-2 mt-1">
              <input
                type="text"
                value={shareToken}
                readOnly
                className="flex-1 px-3 py-2 text-sm border rounded-md bg-gray-50 font-mono"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(shareToken)}
              >
                Copy
              </Button>
            </div>
          </div>
        )}


        <div>
          <h4 className="text-sm font-medium mb-2">Access Instructions:</h4>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {displayInstructions.map((instruction, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-primary">•</span>
                {instruction}
              </li>
            ))}
          </ul>
        </div>

        {accessType === 'token' && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-800">
              <strong>Token Required:</strong> Users must include the access token when accessing this resource.
            </p>
          </div>
        )}

        {accessType === 'private' && (
          <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
            <p className="text-sm text-gray-700">
              <strong>Private Access:</strong> Only authorized users can access this resource.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}