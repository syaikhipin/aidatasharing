'use client';

import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  // Convert markdown to HTML with proper styling
  const renderMarkdown = (text: string) => {
    let html = text;

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold text-gray-900 mt-4 mb-2">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold text-gray-900 mt-6 mb-3">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-gray-900 mt-6 mb-4">$1</h1>');

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');

    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em class="italic text-gray-700">$1</em>');

    // Code blocks
    html = html.replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-800 text-green-400 p-3 rounded-lg my-2 overflow-x-auto"><code>$1</code></pre>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>');

    // Lists - unordered
    html = html.replace(/^\* (.*$)/gim, '<li class="ml-4 text-gray-700">• $1</li>');
    html = html.replace(/^- (.*$)/gim, '<li class="ml-4 text-gray-700">• $1</li>');

    // Wrap consecutive list items in ul
    html = html.replace(/(<li class="ml-4 text-gray-700">.*<\/li>\n?)+/g, (match) => {
      return '<ul class="space-y-1 my-2">' + match + '</ul>';
    });

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p class="text-gray-700 leading-relaxed mb-2">');
    html = html.replace(/\n/g, '<br/>');

    // Wrap in paragraph if not already wrapped
    if (!html.startsWith('<h') && !html.startsWith('<ul') && !html.startsWith('<pre')) {
      html = '<p class="text-gray-700 leading-relaxed mb-2">' + html + '</p>';
    }

    return html;
  };

  return (
    <div
      className="prose prose-sm max-w-none"
      dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
    />
  );
}
