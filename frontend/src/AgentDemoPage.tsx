import React, { useState, useEffect } from 'react';
import AgentGraphVisualizer from './AgentGraphVisualizer';

/**
 * AgentDemoPage - Interactive demonstration of the AI Agent's capabilities
 * Shows real-time visualization of agent workflow and analysis
 */

interface DemoState {
  activeTab: 'demo' | 'visualization' | 'info';
  isAnalyzing: boolean;
  analysisResult: any | null;
  error: string | null;
}

const AgentDemoPage: React.FC = () => {
  const [state, setState] = useState<DemoState>({
    activeTab: 'demo',
    isAnalyzing: false,
    analysisResult: null,
    error: null,
  });

  const [formData, setFormData] = useState({
    job_description: `Senior Backend Engineer

Company: TechCorp
Location: San Francisco, CA

We're looking for an experienced backend engineer to join our growing team. You'll be responsible for:

- Designing and implementing scalable REST APIs
- Optimizing database performance
- Building microservices architecture
- Mentoring junior developers
- Leading technical design discussions

Requirements:
- 5+ years of experience with Python or Java
- Strong understanding of database design and optimization
- Experience with Docker and Kubernetes
- Knowledge of AWS or similar cloud platforms
- Excellent communication skills`,
    current_skills: 'Python, JavaScript, React, PostgreSQL, Docker, REST APIs, AWS',
    job_title: 'Senior Backend Engineer',
    location: 'San Francisco, CA',
    github_username: '',
  });

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAnalyze = async () => {
    if (!formData.job_description.trim() || !formData.current_skills.trim()) {
      setState((prev) => ({
        ...prev,
        error: 'Please fill in all required fields',
      }));
      return;
    }

    setState((prev) => ({
      ...prev,
      isAnalyzing: true,
      error: null,
    }));

    try {
      const response = await fetch('/api/agent/analyze-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_description: formData.job_description,
          current_skills: formData.current_skills
            .split(',')
            .map((s) => s.trim())
            .filter((s) => s),
          job_title: formData.job_title,
          location: formData.location,
          github_username: formData.github_username || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const result = await response.json();
      setState((prev) => ({
        ...prev,
        analysisResult: result,
        activeTab: 'visualization',
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : 'Unknown error occurred',
      }));
    } finally {
      setState((prev) => ({
        ...prev,
        isAnalyzing: false,
      }));
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1>🤖 AI Job Research Agent - Demo</h1>
        <p>Experience real-time visualization of our intelligent agent analyzing job opportunities</p>
      </div>

      <div style={styles.tabBar}>
        <button
          style={{
            ...styles.tab,
            ...(state.activeTab === 'demo' ? styles.activeTab : {}),
          }}
          onClick={() => setState((prev) => ({ ...prev, activeTab: 'demo' }))}
        >
          Input & Analysis
        </button>
        <button
          style={{
            ...styles.tab,
            ...(state.activeTab === 'visualization' ? styles.activeTab : {}),
          }}
          onClick={() => setState((prev) => ({ ...prev, activeTab: 'visualization' }))}
        >
          Real-Time Graph
        </button>
        <button
          style={{
            ...styles.tab,
            ...(state.activeTab === 'info' ? styles.activeTab : {}),
          }}
          onClick={() => setState((prev) => ({ ...prev, activeTab: 'info' }))}
        >
          About Agent
        </button>
      </div>

      {state.error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong> {state.error}
        </div>
      )}

      {state.activeTab === 'demo' && (
        <div style={styles.demoSection}>
          <div style={styles.formGrid}>
            <div style={styles.formGroup}>
              <label>Job Title</label>
              <input
                type="text"
                name="job_title"
                value={formData.job_title}
                onChange={handleInputChange}
                placeholder="e.g., Senior Backend Engineer"
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label>Location</label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleInputChange}
                placeholder="e.g., San Francisco, CA"
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label>GitHub Username (Optional)</label>
              <input
                type="text"
                name="github_username"
                value={formData.github_username}
                onChange={handleInputChange}
                placeholder="your-github-username"
                style={styles.input}
              />
            </div>
          </div>

          <div style={styles.formGroup}>
            <label>Job Description</label>
            <textarea
              name="job_description"
              value={formData.job_description}
              onChange={handleInputChange}
              placeholder="Paste the complete job description..."
              style={{...styles.textarea, height: '250px'}}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Your Current Skills (comma-separated)</label>
            <textarea
              name="current_skills"
              value={formData.current_skills}
              onChange={handleInputChange}
              placeholder="Python, JavaScript, React, ..."
              style={{...styles.textarea, height: '100px'}}
            />
          </div>

          <button
            onClick={handleAnalyze}
            disabled={state.isAnalyzing}
            style={{
              ...styles.analyzeButton,
              ...(state.isAnalyzing ? styles.analyzeButtonDisabled : {}),
            }}
          >
            {state.isAnalyzing ? 'Analyzing... 🔄' : 'Analyze Job & Watch Agent 🚀'}
          </button>

          {state.analysisResult && (
            <div style={styles.resultsBox}>
              <h3>Analysis Results</h3>
              
              <div style={styles.resultSection}>
                <h4>Skills Required ({state.analysisResult.skills_required?.length || 0})</h4>
                <div style={styles.skillsList}>
                  {state.analysisResult.skills_required?.map((skill: string, idx: number) => (
                    <span key={idx} style={styles.skillBadge}>{skill}</span>
                  ))}
                </div>
              </div>

              <div style={styles.resultSection}>
                <h4>Skill Gaps ({state.analysisResult.skill_gaps?.length || 0})</h4>
                <div style={styles.skillsList}>
                  {state.analysisResult.skill_gaps?.map((skill: string, idx: number) => (
                    <span key={idx} style={{...styles.skillBadge, backgroundColor: '#ff6b6b'}}>{skill}</span>
                  ))}
                </div>
              </div>

              <div style={styles.resultSection}>
                <h4>Learning Plan</h4>
                <div style={styles.planText}>
                  {state.analysisResult.learning_plan?.substring(0, 500) || 'Plan generation in progress...'}
                  ...
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {state.activeTab === 'visualization' && (
        <div style={styles.visualizationSection}>
          <AgentGraphVisualizer autoRefresh={true} refreshInterval={2000} />
        </div>
      )}

      {state.activeTab === 'info' && (
        <div style={styles.infoSection}>
          <h2>About the AI Job Research Agent</h2>
          
          <div style={styles.infoBox}>
            <h3>🧠 How It Works</h3>
            <p>
              The agent uses a multi-step reasoning process to analyze job opportunities:
            </p>
            <ol style={styles.infoList}>
              <li><strong>Extract Skills:</strong> Identifies all required skills from job description</li>
              <li><strong>Think:</strong> LLM decides which analysis tools to use</li>
              <li><strong>Execute Tools:</strong> Runs specialized analysis (RAG, validation, gap analysis, GitHub analysis)</li>
              <li><strong>Reflect:</strong> Evaluates information quality and decides if more analysis needed</li>
              <li><strong>Generate Plan:</strong> Creates personalized learning plan based on findings</li>
              <li><strong>Validate:</strong> Self-validates analysis quality and provides recommendations</li>
            </ol>
          </div>

          <div style={styles.infoBox}>
            <h3>🔧 Agent Capabilities</h3>
            <ul style={styles.featureList}>
              <li>✅ Real-time skill gap analysis</li>
              <li>✅ Learning path generation</li>
              <li>✅ GitHub profile analysis (if provided)</li>
              <li>✅ Market research and salary insights</li>
              <li>✅ Skill validation and prerequisites</li>
              <li>✅ RAG-based resource recommendations</li>
              <li>✅ Self-validation with quality scoring</li>
            </ul>
          </div>

          <div style={styles.infoBox}>
            <h3>📊 Visualization Features</h3>
            <p>
              The real-time graph shows:
            </p>
            <ul style={styles.featureList}>
              <li>🔷 <strong>Pending (Gray):</strong> Awaiting execution</li>
              <li>🟨 <strong>Processing (Yellow):</strong> Currently executing</li>
              <li>🟢 <strong>Completed (Green):</strong> Successfully finished</li>
              <li>🔴 <strong>Error (Red):</strong> Encountered an issue</li>
            </ul>
          </div>

          <div style={styles.demoBox}>
            <h3>💡 Try It Now</h3>
            <p>
              Go back to the "Input & Analysis" tab to analyze a job opportunity and watch the agent work in real-time!
            </p>
            <button
              onClick={() => setState((prev) => ({ ...prev, activeTab: 'demo' }))}
              style={styles.tryButton}
            >
              Start Analysis →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
  } as React.CSSProperties,

  header: {
    textAlign: 'center' as const,
    marginBottom: '30px',
  } as React.CSSProperties,

  tabBar: {
    display: 'flex',
    gap: '10px',
    marginBottom: '30px',
    borderBottom: '2px solid #e0e0e0',
  } as React.CSSProperties,

  tab: {
    padding: '12px 24px',
    border: 'none',
    backgroundColor: 'transparent',
    cursor: 'pointer',
    fontSize: '16px',
    borderBottom: '3px solid transparent',
    transition: 'all 0.3s ease',
  } as React.CSSProperties,

  activeTab: {
    borderBottomColor: '#2196F3',
    color: '#2196F3',
    fontWeight: 'bold',
  } as React.CSSProperties,

  demoSection: {
    backgroundColor: '#fff',
    padding: '30px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
  } as React.CSSProperties,

  formGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '20px',
    marginBottom: '20px',
  } as React.CSSProperties,

  formGroup: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  } as React.CSSProperties,

  input: {
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
  } as React.CSSProperties,

  textarea: {
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    fontFamily: 'monospace',
    resize: 'vertical' as const,
  } as React.CSSProperties,

  analyzeButton: {
    padding: '12px 30px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    cursor: 'pointer',
    fontWeight: 'bold',
    transition: 'background-color 0.3s ease',
  } as React.CSSProperties,

  analyzeButtonDisabled: {
    backgroundColor: '#cccccc',
    cursor: 'not-allowed',
  } as React.CSSProperties,

  errorBox: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '16px',
    borderRadius: '4px',
    marginBottom: '20px',
    border: '1px solid #ef5350',
  } as React.CSSProperties,

  resultsBox: {
    marginTop: '30px',
    backgroundColor: '#f5f5f5',
    padding: '20px',
    borderRadius: '4px',
  } as React.CSSProperties,

  resultSection: {
    marginBottom: '20px',
  } as React.CSSProperties,

  skillsList: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '8px',
  } as React.CSSProperties,

  skillBadge: {
    display: 'inline-block',
    padding: '6px 12px',
    backgroundColor: '#2196F3',
    color: 'white',
    borderRadius: '20px',
    fontSize: '12px',
  } as React.CSSProperties,

  planText: {
    backgroundColor: 'white',
    padding: '12px',
    borderRadius: '4px',
    lineHeight: '1.6',
  } as React.CSSProperties,

  visualizationSection: {
    backgroundColor: '#fff',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
  } as React.CSSProperties,

  infoSection: {
    backgroundColor: '#fff',
    padding: '30px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
  } as React.CSSProperties,

  infoBox: {
    marginBottom: '30px',
    padding: '20px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
    borderLeft: '4px solid #2196F3',
  } as React.CSSProperties,

  infoList: {
    lineHeight: '2',
  } as React.CSSProperties,

  featureList: {
    listStyle: 'none' as const,
    padding: 0,
    lineHeight: '1.8',
  } as React.CSSProperties,

  demoBox: {
    backgroundColor: '#e3f2fd',
    padding: '20px',
    borderRadius: '4px',
    textAlign: 'center' as const,
    border: '2px dashed #2196F3',
  } as React.CSSProperties,

  tryButton: {
    marginTop: '16px',
    padding: '12px 30px',
    backgroundColor: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    cursor: 'pointer',
    fontWeight: 'bold',
  } as React.CSSProperties,
};

export default AgentDemoPage;
