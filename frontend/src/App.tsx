import React, { useState, useEffect, useCallback } from 'react';
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

interface SavedAnalysis {
  id: number;
  job_title: string;
  company: string;
  skills_required: string[];
  skill_gaps: string[];
  learning_plan: string;
  analysis_date: string;
}

interface GitHubAnalysis {
  username: string;
  profile_summary: {
    public_repos: number;
    followers: number;
    following: number;
  };
  top_languages: Array<{language: string; count: number}>;
  inferred_skills: string[];
  suggested_roles: string[];
}

interface JobPosting {
  title: string;
  company: string;
  location: string;
  description: string;
  url: string;
}

function App() {
  // Job Analysis state
  const [jobDescription, setJobDescription] = useState('');
  const [currentSkills, setCurrentSkills] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<JobAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Navigation state
  const [activeTab, setActiveTab] = useState('analyze');

  // Saved Analyses state
  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([]);
  const [userId, setUserId] = useState('demo-user');

  // Learning Progress state
  const [skillName, setSkillName] = useState('');
  const [progressPercentage, setProgressPercentage] = useState(0);
  const [completedModules, setCompletedModules] = useState('');

  // GitHub Analysis state
  const [githubUsername, setGithubUsername] = useState('');
  const [githubAnalysis, setGithubAnalysis] = useState<GitHubAnalysis | null>(null);

  // Job Search state
  const [jobKeyword, setJobKeyword] = useState('');
  const [jobLocation, setJobLocation] = useState('');
  const [jobResults, setJobResults] = useState<JobPosting[]>([]);

  // File Management state
  const [fileName, setFileName] = useState('');
  const [fileContent, setFileContent] = useState('');
  const [readFileName, setReadFileName] = useState('');
  const [readFileContent, setReadFileContent] = useState('');

  const loadSavedAnalyses = useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/user-analyses/${userId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSavedAnalyses(data.analyses);
    } catch (err) {
      console.error('Error loading analyses:', err);
    }
  }, [userId]);

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

  // Load saved analyses on component mount
  useEffect(() => {
    if (activeTab === 'saved') {
      loadSavedAnalyses();
    }
  }, [activeTab, loadSavedAnalyses]);

  const saveCurrentAnalysis = async () => {
    if (!result) return;

    try {
      const response = await fetch('http://localhost:8000/api/save-job-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          job_title: jobDescription.split('\n')[0].substring(0, 100), // First line as title
          company: 'Unknown', // Could be extracted from job description
          skills_required: result.skills_required,
          skill_gaps: result.skill_gaps,
          learning_plan: result.learning_plan
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      alert(data.message);
      loadSavedAnalyses(); // Refresh the list
    } catch (err) {
      alert('Error saving analysis: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };


  const updateLearningProgress = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/update-learning-progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          skill: skillName,
          progress_percentage: progressPercentage,
          completed_modules: completedModules.split(',').map(module => module.trim()).filter(module => module.length > 0)
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      alert(data.message);
    } catch (err) {
      alert('Error updating progress: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const analyzeGithubProfile = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/analyze-github/${githubUsername}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setGithubAnalysis(data);
    } catch (err) {
      alert('Error analyzing GitHub profile: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const searchJobs = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/search-jobs?keyword=${encodeURIComponent(jobKeyword)}&location=${encodeURIComponent(jobLocation)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setJobResults(data.jobs || []);
    } catch (err) {
      alert('Error searching jobs: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const saveFile = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/save-file', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: fileName,
          content: fileContent
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      alert(data.message);
    } catch (err) {
      alert('Error saving file: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const readFile = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/read-file?filename=${encodeURIComponent(readFileName)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setReadFileContent(data.content);
    } catch (err) {
      alert('Error reading file: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI Job Research & Career Development Platform</h1>
        <p>Comprehensive job analysis, skill tracking, and career development tools</p>
      </header>

      <nav className="navigation">
        <button
          className={activeTab === 'analyze' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setActiveTab('analyze')}
        >
          Job Analysis
        </button>
        <button
          className={activeTab === 'saved' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setActiveTab('saved')}
        >
          Saved Analyses
        </button>
        <button
          className={activeTab === 'progress' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setActiveTab('progress')}
        >
          Learning Progress
        </button>
        <button
          className={activeTab === 'github' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setActiveTab('github')}
        >
          GitHub Analysis
        </button>
        <button
          className={activeTab === 'jobs' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setActiveTab('jobs')}
        >
          Job Search
        </button>
        <button
          className={activeTab === 'files' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setActiveTab('files')}
        >
          File Manager
        </button>
      </nav>

      <main className="container">
        {activeTab === 'analyze' && (
          <>
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
                <div className="result-header">
                  <h2>Analysis Results</h2>
                  <button onClick={saveCurrentAnalysis} className="save-btn">
                    Save Analysis
                  </button>
                </div>

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
          </>
        )}

        {activeTab === 'saved' && (
          <div className="saved-analyses">
            <h2>Your Saved Job Analyses</h2>
            <div className="user-id-input">
              <label>User ID: </label>
              <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="Enter your user ID"
              />
              <button onClick={loadSavedAnalyses}>Load Analyses</button>
            </div>

            {savedAnalyses.length === 0 ? (
              <p>No saved analyses found.</p>
            ) : (
              <div className="analyses-list">
                {savedAnalyses.map((analysis) => (
                  <div key={analysis.id} className="analysis-card">
                    <h3>{analysis.job_title}</h3>
                    <p><strong>Company:</strong> {analysis.company}</p>
                    <p><strong>Date:</strong> {new Date(analysis.analysis_date).toLocaleDateString()}</p>
                    <details>
                      <summary>View Details</summary>
                      <div className="analysis-details">
                        <h4>Skills Required:</h4>
                        <ul>
                          {analysis.skills_required.map((skill, index) => (
                            <li key={index}>{skill}</li>
                          ))}
                        </ul>
                        <h4>Skill Gaps:</h4>
                        <ul>
                          {analysis.skill_gaps.map((gap, index) => (
                            <li key={index}>{gap}</li>
                          ))}
                        </ul>
                        <h4>Learning Plan:</h4>
                        <div className="markdown-content">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {analysis.learning_plan}
                          </ReactMarkdown>
                        </div>
                      </div>
                    </details>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'progress' && (
          <div className="learning-progress">
            <h2>Track Your Learning Progress</h2>
            <div className="progress-form">
              <div className="form-group">
                <label>Skill Name:</label>
                <input
                  type="text"
                  value={skillName}
                  onChange={(e) => setSkillName(e.target.value)}
                  placeholder="e.g., Python, React, Machine Learning"
                />
              </div>
              <div className="form-group">
                <label>Progress Percentage:</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={progressPercentage}
                  onChange={(e) => setProgressPercentage(Number(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label>Completed Modules (comma-separated):</label>
                <input
                  type="text"
                  value={completedModules}
                  onChange={(e) => setCompletedModules(e.target.value)}
                  placeholder="Module 1, Module 2, Module 3"
                />
              </div>
              <button onClick={updateLearningProgress} className="submit-btn">
                Update Progress
              </button>
            </div>
          </div>
        )}

        {activeTab === 'github' && (
          <div className="github-analysis">
            <h2>GitHub Profile Analysis</h2>
            <div className="github-form">
              <div className="form-group">
                <label>GitHub Username:</label>
                <input
                  type="text"
                  value={githubUsername}
                  onChange={(e) => setGithubUsername(e.target.value)}
                  placeholder="e.g., octocat"
                />
              </div>
              <button onClick={analyzeGithubProfile} className="submit-btn">
                Analyze Profile
              </button>
            </div>

            {githubAnalysis && (
              <div className="github-results">
                <h3>Analysis for @{githubAnalysis.username}</h3>
                
                <div className="profile-summary">
                  <h4>Profile Summary:</h4>
                  <ul>
                    <li>Public Repositories: {githubAnalysis.profile_summary.public_repos}</li>
                    <li>Followers: {githubAnalysis.profile_summary.followers}</li>
                    <li>Following: {githubAnalysis.profile_summary.following}</li>
                  </ul>
                </div>

                <div className="languages">
                  <h4>Top Programming Languages:</h4>
                  <ul>
                    {githubAnalysis.top_languages.map((lang, index) => (
                      <li key={index}>{lang.language}: {lang.count} repositories</li>
                    ))}
                  </ul>
                </div>

                <div className="skills">
                  <h4>Inferred Skills:</h4>
                  <ul>
                    {githubAnalysis.inferred_skills.map((skill, index) => (
                      <li key={index}>{skill}</li>
                    ))}
                  </ul>
                </div>

                <div className="roles">
                  <h4>Suggested Job Roles:</h4>
                  <ul>
                    {githubAnalysis.suggested_roles.map((role, index) => (
                      <li key={index}>{role}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'jobs' && (
          <div className="job-search">
            <h2>Job Search</h2>
            <div className="job-search-form">
              <div className="form-group">
                <label>Job Keyword:</label>
                <input
                  type="text"
                  value={jobKeyword}
                  onChange={(e) => setJobKeyword(e.target.value)}
                  placeholder="e.g., Python Developer"
                />
              </div>
              <div className="form-group">
                <label>Location:</label>
                <input
                  type="text"
                  value={jobLocation}
                  onChange={(e) => setJobLocation(e.target.value)}
                  placeholder="e.g., San Francisco"
                />
              </div>
              <button onClick={searchJobs} className="submit-btn">
                Search Jobs
              </button>
            </div>

            {jobResults.length > 0 && (
              <div className="job-results">
                <h3>Job Results:</h3>
                {jobResults.map((job, index) => (
                  <div key={index} className="job-card">
                    <h4>{job.title}</h4>
                    <p><strong>Company:</strong> {job.company}</p>
                    <p><strong>Location:</strong> {job.location}</p>
                    <p>{job.description}</p>
                    {job.url && (
                      <a href={job.url} target="_blank" rel="noopener noreferrer">
                        Apply Here
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'files' && (
          <div className="file-manager">
            <h2>File Manager</h2>
            
            <div className="file-section">
              <h3>Save File</h3>
              <div className="form-group">
                <label>Filename:</label>
                <input
                  type="text"
                  value={fileName}
                  onChange={(e) => setFileName(e.target.value)}
                  placeholder="e.g., my-analysis.md"
                />
              </div>
              <div className="form-group">
                <label>Content:</label>
                <textarea
                  value={fileContent}
                  onChange={(e) => setFileContent(e.target.value)}
                  placeholder="Enter file content..."
                  rows={6}
                />
              </div>
              <button onClick={saveFile} className="submit-btn">
                Save File
              </button>
            </div>

            <div className="file-section">
              <h3>Read File</h3>
              <div className="form-group">
                <label>Filename:</label>
                <input
                  type="text"
                  value={readFileName}
                  onChange={(e) => setReadFileName(e.target.value)}
                  placeholder="e.g., my-analysis.md"
                />
              </div>
              <button onClick={readFile} className="submit-btn">
                Read File
              </button>
              
              {readFileContent && (
                <div className="file-content">
                  <h4>File Content:</h4>
                  <pre>{readFileContent}</pre>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
