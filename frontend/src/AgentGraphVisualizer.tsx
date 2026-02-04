import React, { useEffect, useState, useCallback, useRef } from 'react';

/**
 * AgentGraphVisualizer - Real-time visualization of the agent workflow
 * Displays nodes, edges, and execution status dynamically
 */

interface Node {
  id: string;
  label: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  x?: number;
  y?: number;
}

interface Edge {
  from: string;
  to: string;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
  session_id?: string;
  total_events?: number;
}

interface AgentGraphVisualizerProps {
  sessionId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const AgentGraphVisualizer: React.FC<AgentGraphVisualizerProps> = ({
  sessionId,
  autoRefresh = true,
  refreshInterval = 1000,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Calculate node positions in a linear flow
  const calculateNodePositions = (nodes: Node[]): Node[] => {
    const padding = 80;
    const nodeWidth = 140;
    const nodeHeight = 80;
    const canvasWidth = 1000;
    const canvasHeight = 400;

    const startX = 50;
    const startY = canvasHeight / 2;
    const spacing = (canvasWidth - 100) / Math.max(nodes.length - 1, 1);

    return nodes.map((node, index) => ({
      ...node,
      x: startX + index * spacing,
      y: startY,
    }));
  };

  // Fetch graph visualization data
  const fetchGraphData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/agent/graph');
      if (!response.ok) throw new Error('Failed to fetch graph data');
      const data = await response.json();
      
      const positionedData = {
        ...data,
        nodes: calculateNodePositions(data.nodes),
      };
      
      setGraphData(positionedData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch events
  const fetchEvents = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/agent/events');
      if (!response.ok) throw new Error('Failed to fetch events');
      const data = await response.json();
      setEvents(data.events || []);
    } catch (err) {
      console.error('Error fetching events:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchGraphData();
    fetchEvents();
  }, [fetchGraphData, fetchEvents]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchGraphData();
      fetchEvents();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchGraphData, fetchEvents]);

  // Draw graph
  useEffect(() => {
    if (!graphData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw edges (arrows)
    graphData.edges.forEach((edge) => {
      const fromNode = graphData.nodes.find((n) => n.id === edge.from);
      const toNode = graphData.nodes.find((n) => n.id === edge.to);

      if (fromNode?.x && fromNode?.y && toNode?.x && toNode?.y) {
        ctx.strokeStyle = '#888';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(fromNode.x + 70, fromNode.y);
        ctx.lineTo(toNode.x - 70, toNode.y);
        ctx.stroke();

        // Draw arrowhead
        const angle = Math.atan2(toNode.y - fromNode.y, toNode.x - fromNode.x);
        ctx.fillStyle = '#888';
        ctx.beginPath();
        ctx.moveTo(toNode.x - 70, toNode.y);
        ctx.lineTo(
          toNode.x - 70 - 10 * Math.cos(angle - Math.PI / 6),
          toNode.y - 10 * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          toNode.x - 70 - 10 * Math.cos(angle + Math.PI / 6),
          toNode.y - 10 * Math.sin(angle + Math.PI / 6)
        );
        ctx.fill();
      }
    });

    // Draw nodes
    graphData.nodes.forEach((node) => {
      if (!node.x || !node.y) return;

      const statusColors: Record<string, string> = {
        pending: '#e0e0e0',
        processing: '#ffeb3b',
        completed: '#4caf50',
        error: '#f44336',
      };

      const statusBorderColors: Record<string, string> = {
        pending: '#999',
        processing: '#ff9800',
        completed: '#2e7d32',
        error: '#c62828',
      };

      const x = node.x;
      const y = node.y;

      // Draw node circle
      ctx.fillStyle = statusColors[node.status] || '#e0e0e0';
      ctx.strokeStyle = statusBorderColors[node.status] || '#999';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(x, y, 60, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      // Draw text
      ctx.fillStyle = '#000';
      ctx.font = 'bold 12px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      const lines = node.label.split(' ');
      const lineHeight = 15;
      const startY = y - (lines.length - 1) * lineHeight / 2;
      
      lines.forEach((line, idx) => {
        ctx.fillText(line, x, startY + idx * lineHeight);
      });

      // Draw status indicator
      const statusText = node.status.charAt(0).toUpperCase() + node.status.slice(1);
      ctx.font = 'normal 10px Arial';
      ctx.fillStyle = '#666';
      ctx.fillText(statusText, x, y + 75);
    });
  }, [graphData]);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2>Agent Graph Visualization</h2>
        <button
          onClick={() => {
            fetchGraphData();
            fetchEvents();
          }}
          style={styles.button}
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && <div style={styles.error}>Error: {error}</div>}

      <div style={styles.canvasContainer}>
        <canvas
          ref={canvasRef}
          width={1000}
          height={400}
          style={styles.canvas}
        />
      </div>

      <div style={styles.infoSection}>
        <h3>Graph Info</h3>
        <p>Total Events: {graphData?.total_events || 0}</p>
        <p>Session ID: {graphData?.session_id || 'N/A'}</p>
        <p>Nodes: {graphData?.nodes.length || 0}</p>
      </div>

      <div style={styles.eventsSection}>
        <h3>Recent Events ({events.length})</h3>
        <div style={styles.eventsList}>
          {events.slice(-10).reverse().map((event, idx) => (
            <div key={idx} style={styles.eventItem}>
              <span style={styles.eventType}>{event.type}</span>
              <span style={styles.eventNode}>
                {event.node_name || event.tool_name || '-'}
              </span>
              <span style={styles.eventTime}>
                {new Date(event.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    padding: '20px',
    backgroundColor: '#fff',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
  } as React.CSSProperties,
  
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  } as React.CSSProperties,
  
  button: {
    padding: '8px 16px',
    backgroundColor: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  } as React.CSSProperties,
  
  canvasContainer: {
    border: '1px solid #ddd',
    borderRadius: '4px',
    marginBottom: '20px',
    overflow: 'auto',
  } as React.CSSProperties,
  
  canvas: {
    display: 'block',
    backgroundColor: '#f8f9fa',
  } as React.CSSProperties,
  
  infoSection: {
    backgroundColor: '#f5f5f5',
    padding: '12px',
    borderRadius: '4px',
    marginBottom: '16px',
  } as React.CSSProperties,
  
  eventsSection: {
    backgroundColor: '#f5f5f5',
    padding: '12px',
    borderRadius: '4px',
  } as React.CSSProperties,
  
  eventsList: {
    maxHeight: '300px',
    overflowY: 'auto',
  } as React.CSSProperties,
  
  eventItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px',
    backgroundColor: '#fff',
    borderBottom: '1px solid #eee',
    fontSize: '12px',
  } as React.CSSProperties,
  
  eventType: {
    fontWeight: 'bold',
    color: '#2196F3',
    flex: 1,
  } as React.CSSProperties,
  
  eventNode: {
    color: '#666',
    flex: 1,
  } as React.CSSProperties,
  
  eventTime: {
    color: '#999',
    flex: 1,
    textAlign: 'right',
  } as React.CSSProperties,
  
  error: {
    color: '#f44336',
    padding: '12px',
    backgroundColor: '#ffebee',
    borderRadius: '4px',
    marginBottom: '16px',
  } as React.CSSProperties,
};

export default AgentGraphVisualizer;
