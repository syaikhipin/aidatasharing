'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import { Loader2, FileText, Upload, CheckCircle, AlertCircle } from 'lucide-react';

interface DocumentUploaderProps {
  onSuccess?: (datasetId: number) => void;
  onError?: (error: any) => void;
}

export function DocumentUploader({ onSuccess, onError }: DocumentUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [description, setDescription] = useState('');
  const [sharingLevel, setSharingLevel] = useState('PRIVATE');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const supportedFormats = ['pdf', 'docx', 'doc', 'txt', 'rtf', 'odt'];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    const fileExt = selectedFile.name.split('.').pop()?.toLowerCase() || '';
    if (!supportedFormats.includes(fileExt)) {
      setError(`Unsupported file format. Please upload one of: ${supportedFormats.join(', ')}`);
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setError(null);
    
    // Auto-populate dataset name if empty
    if (!datasetName) {
      const baseName = selectedFile.name.split('.')[0];
      setDatasetName(baseName);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);
    setSuccess(false);

    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      formData.append('dataset_name', datasetName || file.name.split('.')[0]);
      formData.append('description', description);
      formData.append('sharing_level', sharingLevel);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 5, 95));
      }, 200);

      // Upload document (this would be replaced with actual API call)
      const response = await fetch('/api/data-connectors/document', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setProgress(100);
      setSuccess(true);

      // Call onSuccess callback if provided
      if (onSuccess && response.ok) {
        const data = await response.json();
        onSuccess(data.dataset_id);
      }
    } catch (err: any) {
      setProgress(0);
      setError(err.message || 'Failed to upload document');
      
      // Call onError callback if provided
      if (onError) {
        onError(err);
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Upload Document</CardTitle>
        <CardDescription>
          Upload PDF, DOCX, DOC, TXT, RTF, or ODT files to create a dataset
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-6">
            <div className="grid gap-2">
              <Label htmlFor="file">Document File</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="file"
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.doc,.txt,.rtf,.odt"
                  disabled={uploading}
                  className="flex-1"
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Supported formats: {supportedFormats.join(', ')}
              </p>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="datasetName">Dataset Name</Label>
              <Input
                id="datasetName"
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                disabled={uploading}
                placeholder="Enter dataset name"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={uploading}
                placeholder="Enter dataset description"
                rows={3}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="sharingLevel">Sharing Level</Label>
              <Select
                value={sharingLevel}
                onValueChange={setSharingLevel}
                disabled={uploading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select sharing level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PRIVATE">Private</SelectItem>
                  <SelectItem value="ORGANIZATION">Organization</SelectItem>
                  <SelectItem value="PUBLIC">Public</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {uploading && (
              <div className="grid gap-2">
                <Label>Upload Progress</Label>
                <Progress value={progress} className="h-2" />
                <p className="text-sm text-muted-foreground text-center">
                  {progress < 100 ? 'Uploading...' : 'Processing document...'}
                </p>
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="bg-green-50 border-green-200">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertTitle className="text-green-800">Success</AlertTitle>
                <AlertDescription className="text-green-700">
                  Document uploaded successfully and is being processed.
                </AlertDescription>
              </Alert>
            )}
          </div>

          <Button
            type="submit"
            className="mt-6 w-full"
            disabled={!file || uploading}
          >
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload Document
              </>
            )}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="flex justify-between text-sm text-muted-foreground">
        <div className="flex items-center">
          <FileText className="mr-2 h-4 w-4" />
          <span>Document datasets support AI chat and text analysis</span>
        </div>
      </CardFooter>
    </Card>
  );
}