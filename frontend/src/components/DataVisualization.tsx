'use client';

import React, { useMemo } from 'react';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { BarChart3, LineChart, PieChart, ScatterChart, Activity, AlertCircle } from 'lucide-react';

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { 
  ssr: false,
  loading: () => <Skeleton className="w-full h-[400px]" />
});

interface Visualization {
  type: string;
  title: string;
  description: string;
  chart: any;
  insights?: string[];
  code?: string;
}

interface DataAnalysis {
  dataset_name: string;
  basic_stats: {
    rows: number;
    columns: number;
    memory_usage: string;
    column_types?: any;
  };
  data_quality: {
    missing_values?: any;
    missing_percentage?: any;
    duplicated_rows?: number;
    unique_values?: any;
  };
  column_analysis?: any;
  correlations?: {
    strong_correlations?: Array<{
      column1: string;
      column2: string;
      correlation: number;
    }>;
  };
  recommendations?: string[];
}

interface DataVisualizationProps {
  visualizations?: Visualization[];
  dataAnalysis?: DataAnalysis;
  loading?: boolean;
  error?: string;
}

const getChartIcon = (type: string) => {
  switch (type?.toLowerCase()) {
    case 'bar':
    case 'bar_chart':
      return <BarChart3 className="w-4 h-4" />;
    case 'line':
    case 'time_series':
      return <LineChart className="w-4 h-4" />;
    case 'pie':
      return <PieChart className="w-4 h-4" />;
    case 'scatter':
      return <ScatterChart className="w-4 h-4" />;
    default:
      return <Activity className="w-4 h-4" />;
  }
};

export function DataVisualization({ 
  visualizations = [], 
  dataAnalysis, 
  loading = false, 
  error 
}: DataVisualizationProps) {
  
  // Process Plotly charts
  const processedVisualizations = useMemo(() => {
    return visualizations.map(viz => {
      if (viz.chart?.type === 'image') {
        // Handle image-based visualizations
        return {
          ...viz,
          isImage: true,
          imageData: viz.chart.data
        };
      }
      return viz;
    });
  }, [visualizations]);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="w-full h-[400px]" />
        <Skeleton className="w-full h-[200px]" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!visualizations?.length && !dataAnalysis) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Data Analysis Summary */}
      {dataAnalysis && (
        <Card>
          <CardHeader>
            <CardTitle>📊 Data Analysis Summary</CardTitle>
            <CardDescription>
              Dataset: {dataAnalysis.dataset_name}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Rows</p>
                <p className="text-2xl font-bold">{dataAnalysis.basic_stats?.rows?.toLocaleString()}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Columns</p>
                <p className="text-2xl font-bold">{dataAnalysis.basic_stats?.columns}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Memory Usage</p>
                <p className="text-2xl font-bold">{dataAnalysis.basic_stats?.memory_usage}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Duplicates</p>
                <p className="text-2xl font-bold">{dataAnalysis.data_quality?.duplicated_rows || 0}</p>
              </div>
            </div>

            {/* Recommendations */}
            {dataAnalysis.recommendations && dataAnalysis.recommendations.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium mb-2">Recommendations</h4>
                <div className="space-y-2">
                  {dataAnalysis.recommendations.map((rec, idx) => (
                    <Alert key={idx} className="py-2">
                      <AlertDescription className="text-sm">{rec}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              </div>
            )}

            {/* Strong Correlations */}
            {dataAnalysis.correlations?.strong_correlations && 
             dataAnalysis.correlations.strong_correlations.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium mb-2">Strong Correlations</h4>
                <div className="flex flex-wrap gap-2">
                  {dataAnalysis.correlations.strong_correlations.map((corr, idx) => (
                    <Badge key={idx} variant="secondary">
                      {corr.column1} ↔ {corr.column2}: {corr.correlation.toFixed(2)}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Visualizations */}
      {processedVisualizations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>📈 Data Visualizations</CardTitle>
            <CardDescription>
              {processedVisualizations.length} visualization{processedVisualizations.length !== 1 ? 's' : ''} generated
            </CardDescription>
          </CardHeader>
          <CardContent>
            {processedVisualizations.length === 1 ? (
              // Single visualization - show directly
              <div className="space-y-4">
                {processedVisualizations.map((viz, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="flex items-center gap-2">
                      {getChartIcon(viz.type)}
                      <h3 className="font-medium">{viz.title}</h3>
                    </div>
                    {viz.description && (
                      <p className="text-sm text-muted-foreground">{viz.description}</p>
                    )}
                    
                    {/* Render the chart */}
                    {viz.isImage ? (
                      <img 
                        src={viz.imageData} 
                        alt={viz.title}
                        className="w-full rounded-lg border"
                      />
                    ) : viz.chart ? (
                      <div className="w-full overflow-x-auto">
                        <Plot
                          data={viz.chart.data || []}
                          layout={{
                            ...viz.chart.layout,
                            autosize: true,
                            margin: { t: 40, r: 40, b: 40, l: 40 },
                            paper_bgcolor: 'transparent',
                            plot_bgcolor: 'transparent',
                            font: { color: 'currentColor' }
                          }}
                          config={{
                            responsive: true,
                            displayModeBar: true,
                            displaylogo: false
                          }}
                          className="w-full"
                          style={{ width: '100%', height: '400px' }}
                        />
                      </div>
                    ) : null}
                    
                    {/* Insights */}
                    {viz.insights && viz.insights.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {viz.insights.map((insight, i) => (
                          <p key={i} className="text-sm text-muted-foreground">• {insight}</p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              // Multiple visualizations - use tabs
              <Tabs defaultValue="0" className="w-full">
                <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${Math.min(processedVisualizations.length, 4)}, 1fr)` }}>
                  {processedVisualizations.map((viz, idx) => (
                    <TabsTrigger key={idx} value={idx.toString()}>
                      <div className="flex items-center gap-1">
                        {getChartIcon(viz.type)}
                        <span className="hidden sm:inline">{viz.title.length > 20 ? viz.title.substring(0, 20) + '...' : viz.title}</span>
                        <span className="sm:hidden">Chart {idx + 1}</span>
                      </div>
                    </TabsTrigger>
                  ))}
                </TabsList>
                
                {processedVisualizations.map((viz, idx) => (
                  <TabsContent key={idx} value={idx.toString()} className="space-y-4">
                    <div>
                      <h3 className="font-medium text-lg">{viz.title}</h3>
                      {viz.description && (
                        <p className="text-sm text-muted-foreground mt-1">{viz.description}</p>
                      )}
                    </div>
                    
                    {/* Render the chart */}
                    {viz.isImage ? (
                      <img 
                        src={viz.imageData} 
                        alt={viz.title}
                        className="w-full rounded-lg border"
                      />
                    ) : viz.chart ? (
                      <div className="w-full overflow-x-auto">
                        <Plot
                          data={viz.chart.data || []}
                          layout={{
                            ...viz.chart.layout,
                            autosize: true,
                            margin: { t: 40, r: 40, b: 40, l: 40 },
                            paper_bgcolor: 'transparent',
                            plot_bgcolor: 'transparent',
                            font: { color: 'currentColor' }
                          }}
                          config={{
                            responsive: true,
                            displayModeBar: true,
                            displaylogo: false
                          }}
                          className="w-full"
                          style={{ width: '100%', height: '400px' }}
                        />
                      </div>
                    ) : null}
                    
                    {/* Insights */}
                    {viz.insights && viz.insights.length > 0 && (
                      <div className="space-y-1">
                        <h4 className="text-sm font-medium">Key Insights:</h4>
                        {viz.insights.map((insight, i) => (
                          <p key={i} className="text-sm text-muted-foreground">• {insight}</p>
                        ))}
                      </div>
                    )}
                  </TabsContent>
                ))}
              </Tabs>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}