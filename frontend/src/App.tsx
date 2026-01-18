import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './App.css';

interface JobAnalysisRequest {
  job_description: string;
  current_skills: string[];
}

interface JobAnalysisResponse {
  skills_required: string[];
  skill_gaps: string[];
  learning_plan: string;
  relevant_resources: string[];
}

function App() {
  const [jobDescription, setJobDescription] = useState('');
  const [currentSkills, setCurrentSkills] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<JobAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const requestData: JobAnalysisRequest = {
        job_description: jobDescription,
        current_skills: currentSkills.split(',').map(skill => skill.trim()).filter(skill => skill.length > 0)
      };

      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: JobAnalysisResponse = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI Job Research & Summary Agent</h1>
        <p>Get personalized learning plans for job requirements</p>
      </header>

      <main className="container">
        <form onSubmit={handleSubmit} className="job-form">
          <div className="form-group">
            <label htmlFor="jobDescription">
              Job Description:
            </label>
            <textarea
              id="jobDescription"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here..."
              required
              rows={6}
            />
          </div>

          <div className="form-group">
            <label htmlFor="currentSkills">
              Current Skills (comma-separated):
            </label>
            <input
              type="text"
              id="currentSkills"
              value={currentSkills}
              onChange={(e) => setCurrentSkills(e.target.value)}
              placeholder="Python, JavaScript, React..."
            />
          </div>

          <button type="submit" disabled={isLoading} className="submit-btn">
            {isLoading ? 'Analyzing...' : 'Analyze Job'}
          </button>
        </form>

        {error && (
          <div className="error-message">
            <h3>Error:</h3>
            <p>{error}</p>
          </div>
        )}

        {result && (
          <div className="results">
            <h2>Analysis Results</h2>

            <div className="result-section">
              <h3>Skills Required:</h3>
              <ul>
                {result.skills_required.map((skill, index) => (
                  <li key={index}>{skill}</li>
                ))}
              </ul>
            </div>

            <div className="result-section">
              <h3>Skill Gaps:</h3>
              <ul>
                {result.skill_gaps.map((gap, index) => (
                  <li key={index}>{gap}</li>
                ))}
              </ul>
            </div>

            <div className="result-section">
              <h3>Learning Plan:</h3>
              <div className="markdown-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {result.learning_plan}
                </ReactMarkdown>
              </div>
            </div>

            <div className="result-section">
              <h3>Relevant Resources:</h3>
              <div className="markdown-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {result.relevant_resources.map((resource, index) => 
                    `${index + 1}. ${resource}`
                  ).join('\n\n')}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
