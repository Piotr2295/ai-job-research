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
  matchPercentage?: number;
  matchingSkills?: string[];
  totalUserSkills?: number;
}

interface EnhancedJobMatch {
  job_info: {
    id: string;
    title: string;
    company: string;
    location: string;
    remote: boolean;
    experience_level: string;
    url: string;
    salary_from?: number;
    salary_to?: number;
    salary_currency?: string;
  };
  requirements: any;
  skill_match: {
    matching_skills: string[];
    skill_gaps: string[];
    nice_to_have_matches: string[];
    match_percentage: number;
  };
  gap_analysis: string;
  learning_resources: string[];
  recommendation: string;
}

interface EnhancedJobAnalysisResponse {
  user_skills: {
    technical_skills: string[];
    soft_skills: string[];
    tools: string[];
    languages: string[];
  };
  jobs_analyzed: number;
  job_matches: EnhancedJobMatch[];
  overall_recommendations?: {
    summary?: string;
    top_skills_to_learn?: string[];
    career_insights?: string;
    best_match?: any;
    message?: string;  // For error messages
  };
  search_criteria?: {
    location: string;
    experience_level: string | null;
    specific_role: string | null;
  };
  error_message?: string;  // For when search fails
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
  const [cvSkills, setCvSkills] = useState<any>(null);

  // Resume Optimization state
  const [userExperiences, setUserExperiences] = useState<Array<{
    role: string;
    company: string;
    duration: string;
    achievements: string[];
    skills: string[];
  }>>([]);
  const [currentExperience, setCurrentExperience] = useState({
    role: '',
    company: '',
    duration: '',
    achievements: '',
    skills: ''
  });
  const [resumeJobDescription, setResumeJobDescription] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [targetCompany, setTargetCompany] = useState('');
  const [resumeOptimization, setResumeOptimization] = useState<any>(null);

  // PDF Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [parsedResume, setParsedResume] = useState<any>(null);

  // Advanced RAG state
  const [ragQuestion, setRagQuestion] = useState('');
  const [ragResponse, setRagResponse] = useState<any>(null);
  const [ragMetrics, setRagMetrics] = useState<any>(null);
  const [expandedAccordion, setExpandedAccordion] = useState<string | null>('pipeline');
  const [ragLoading, setRagLoading] = useState(false);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [jobSearchLoading, setJobSearchLoading] = useState(false);

  // Enhanced Job Analysis state
  const [uploadedResumeId, setUploadedResumeId] = useState<number | null>(null);
  const [suggestedRoles, setSuggestedRoles] = useState<string[]>([]);
  const [expandedJobDescriptions, setExpandedJobDescriptions] = useState<Set<string>>(new Set());

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
    setJobSearchLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/search-jobs?keyword=${encodeURIComponent(jobKeyword)}&location=${encodeURIComponent(jobLocation)}`);
      const data = await response.json();

      // Check if the response contains an error
      if (data.error) {
        let errorMessage = data.message || 'An error occurred';
        const reason = data.reason ? `(${data.reason})` : '';
        const details = data.details ? `\n\n${data.details}` : '';
        alert(`${errorMessage} ${reason}${details}`);
        setJobResults([]);
        return;
      }

      // Success case
      if (data.jobs && data.jobs.length > 0) {
        let jobs = data.jobs;
        
        // If CV skills are available, analyze each job and calculate match
        if (cvSkills) {
          jobs = await Promise.all(data.jobs.map(async (job: any) => {
            try {
              // Extract skills from job description using simple keyword matching
              const allUserSkills = [
                ...(cvSkills.technical_skills || []),
                ...(cvSkills.tools || []),
                ...(cvSkills.languages || [])
              ].map((s: string) => s.toLowerCase());
              
              const jobDesc = (job.description || '').toLowerCase();
              
              // Find matching skills
              const matchingSkills = allUserSkills.filter((skill: string) => 
                jobDesc.includes(skill.toLowerCase())
              );
              
              // Simple match percentage calculation
              const matchPercentage = allUserSkills.length > 0 
                ? Math.round((matchingSkills.length / Math.min(allUserSkills.length, 15)) * 100)
                : 0;
              
              return {
                ...job,
                matchPercentage,
                matchingSkills,
                totalUserSkills: allUserSkills.length
              };
            } catch (err) {
              console.error('Error analyzing job:', err);
              return { ...job, matchPercentage: 0, matchingSkills: [] };
            }
          }));
          
          // Sort jobs by match percentage (highest first)
          jobs.sort((a: any, b: any) => (b.matchPercentage || 0) - (a.matchPercentage || 0));
        }
        
        setJobResults(jobs);
        const matchInfo = cvSkills ? ' (sorted by match with your CV)' : '';
        alert(`Found ${jobs.length} job(s) matching your search!${matchInfo}`);
      } else {
        setJobResults([]);
        alert(data.details || 'No jobs found matching your search criteria.');
      }
    } catch (err) {
      alert('Error searching jobs: ' + (err instanceof Error ? err.message : 'Unknown error'));
      setJobResults([]);
    } finally {
      setJobSearchLoading(false);
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

  const addUserExperience = async () => {
    if (!currentExperience.role || !currentExperience.company) {
      alert('Please fill in role and company');
      return;
    }

    const experience = {
      role: currentExperience.role,
      company: currentExperience.company,
      duration: currentExperience.duration,
      achievements: currentExperience.achievements.split('\n').filter(a => a.trim()),
      skills: currentExperience.skills.split(',').map(s => s.trim()).filter(s => s)
    };

    try {
      const response = await fetch('http://localhost:8000/api/add-user-experience', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          experiences: [experience]
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      alert(data.message);

      // Add to local state
      setUserExperiences([...userExperiences, experience]);

      // Reset form
      setCurrentExperience({
        role: '',
        company: '',
        duration: '',
        achievements: '',
        skills: ''
      });
    } catch (err) {
      alert('Error adding experience: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const optimizeResume = async () => {
    if (!resumeJobDescription || !targetRole) {
      alert('Please fill in job description and target role');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/optimize-resume', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          job_description: resumeJobDescription,
          target_role: targetRole,
          target_company: targetCompany
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResumeOptimization(data);
    } catch (err) {
      alert('Error optimizing resume: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const toggleJobDescription = (jobId: string) => {
    const newExpanded = new Set(expandedJobDescriptions);
    if (newExpanded.has(jobId)) {
      newExpanded.delete(jobId);
    } else {
      newExpanded.add(jobId);
    }
    setExpandedJobDescriptions(newExpanded);
  };

  const uploadResume = async () => {
    if (!selectedFile) {
      alert('Please select a PDF file first');
      return;
    }

    setUploadStatus('Uploading...');
    setSuggestedRoles([]);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('user_id', userId);

      const response = await fetch('http://localhost:8000/api/upload-resume', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setParsedResume(data.parsed_resume);
      setUploadedResumeId(data.resume_id); // Store resume ID for enhanced analysis
      setUploadStatus(`✓ ${data.message}`);
      
      // Display suggested roles
      if (data.suggested_roles && data.suggested_roles.length > 0) {
        setSuggestedRoles(data.suggested_roles);
      }
      
      // Extract and store skills from CV for job matching
      if (data.resume_id) {
        try {
          const skillsResponse = await fetch(`http://localhost:8000/api/extract-skills/${data.resume_id}?user_id=${userId}`);
          if (skillsResponse.ok) {
            const skillsData = await skillsResponse.json();
            setCvSkills(skillsData.skills);
          }
        } catch (err) {
          console.error('Error extracting skills:', err);
        }
      }
      
    } catch (err) {
      setUploadStatus('Error: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setUploadStatus('');
    } else {
      alert('Please select a valid PDF file');
      setSelectedFile(null);
    }
  };

  const queryAdvancedRAG = async () => {
    if (!ragQuestion.trim()) {
      alert('Please enter a question');
      return;
    }

    setRagLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/advanced-rag-query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: ragQuestion
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setRagResponse(data);
      setExpandedAccordion('evaluation');
    } catch (err) {
      alert('Error querying RAG: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setRagLoading(false);
    }
  };

  const loadRAGMetrics = async () => {
    setMetricsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/rag-performance-metrics');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setRagMetrics(data);
    } catch (err) {
      console.error('Error loading RAG metrics:', err);
    } finally {
      setMetricsLoading(false);
    }
  };

  // Load RAG metrics on component mount
  useEffect(() => {
    if (activeTab === 'rag') {
      loadRAGMetrics();
    }
  }, [activeTab]);

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
          className={activeTab === 'resume' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setActiveTab('resume')}
        >
          Resume Optimizer
        </button>
        <button
          className={activeTab === 'rag' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setActiveTab('rag')}
        >
          Advanced RAG
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
                  <div className="save-btn-container">
                    <button onClick={saveCurrentAnalysis} className="save-btn">
                      Save Analysis
                    </button>
                  </div>
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
            
            {/* Resume Upload Section */}
            <div className="job-search-form">
              <div style={{marginBottom: '2rem', padding: '1.5rem', backgroundColor: '#f8f9fa', borderRadius: '8px'}}>
                <h3 style={{marginTop: 0}}>📄 Upload Your Resume (Optional)</h3>
                <p style={{color: '#666', marginBottom: '1rem'}}>Upload your CV to help match relevant jobs</p>
                <div className="form-group">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="file-input"
                  />
                  {selectedFile && <p className="file-name">Selected: {selectedFile.name}</p>}
                  <button onClick={uploadResume} className="submit-btn" disabled={!selectedFile}>
                    Upload Resume
                  </button>
                  {uploadStatus && <p className={`upload-status ${uploadStatus.includes('Error') ? 'error' : 'success'}`}>
                    {uploadStatus}
                  </p>}
                </div>
              </div>

              {/* Suggested Roles Based on CV */}
              {suggestedRoles.length > 0 && (
                <div style={{padding: '1.5rem', backgroundColor: '#e8f5e9', borderRadius: '8px', marginBottom: '1.5rem'}}>
                  <h4 style={{marginTop: 0, color: '#2e7d32'}}>🎯 Recommended Roles Based on Your CV:</h4>
                  <div style={{display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem'}}>
                    {suggestedRoles.map((role, idx) => (
                      <button
                        key={idx}
                        onClick={() => setJobKeyword(role)}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: jobKeyword === role ? '#4caf50' : 'white',
                          color: jobKeyword === role ? 'white' : '#4caf50',
                          border: '2px solid #4caf50',
                          borderRadius: '20px',
                          cursor: 'pointer',
                          fontSize: '0.9em',
                          fontWeight: '500',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          if (jobKeyword !== role) {
                            e.currentTarget.style.backgroundColor = '#f1f8e9';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (jobKeyword !== role) {
                            e.currentTarget.style.backgroundColor = 'white';
                          }
                        }}
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                  <p style={{fontSize: '0.85em', color: '#558b2f', margin: 0, fontStyle: 'italic'}}>
                    Click any role to auto-fill the job keyword search
                  </p>
                </div>
              )}

              {/* Job Search Form */}
              <div style={{padding: '1.5rem', backgroundColor: '#f8f9fa', borderRadius: '8px'}}>
                <h3 style={{marginTop: 0}}>🔍 Search for Jobs</h3>
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
                <button onClick={searchJobs} className="submit-btn" disabled={jobSearchLoading}>
                  {jobSearchLoading ? (
                    <>
                      <span className="spinner"></span>
                      Searching...
                    </>
                  ) : (
                    'Search Jobs'
                  )}
                </button>
              </div>
            </div>

            {jobSearchLoading && (
              <div className="loading-container">
                <div className="spinner-large"></div>
                <p>Searching for job opportunities...</p>
              </div>
            )}

            {jobResults.length > 0 && (
              <div className="job-results">
                <h3>Job Results ({jobResults.length}):</h3>
                {jobResults.map((job, index) => {
                  const isExpanded = expandedJobDescriptions.has(`job-search-${index}`);
                  const description = job.description || '';
                  // Show button if description would be truncated by 150px max-height
                  // Approximate: ~4 lines of text = ~100px at lineHeight 1.5, so if longer than ~200 chars, likely truncated
                  const shouldTruncate = description.length > 150;
                  
                  return (
                    <div key={index} className="job-card" style={{position: 'relative'}}>
                      {/* Match Badge */}
                      {job.matchPercentage !== undefined && (
                        <div style={{
                          position: 'absolute',
                          top: '1rem',
                          right: '1rem',
                          backgroundColor: job.matchPercentage >= 70 ? '#4caf50' : job.matchPercentage >= 40 ? '#ff9800' : '#f44336',
                          color: 'white',
                          padding: '0.5rem 1rem',
                          borderRadius: '20px',
                          fontWeight: 'bold',
                          fontSize: '0.9em',
                          boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                        }}>
                          {job.matchPercentage}% Match
                        </div>
                      )}
                      
                      <h4>{job.title}</h4>
                      <p><strong>Company:</strong> {job.company}</p>
                      <p><strong>Location:</strong> {job.location}</p>
                      
                      {/* Matching Skills Section */}
                      {job.matchingSkills && job.matchingSkills.length > 0 && (
                        <div style={{marginTop: '1rem', padding: '1rem', backgroundColor: '#e8f5e9', borderRadius: '8px', borderLeft: '4px solid #4caf50'}}>
                          <strong style={{color: '#2e7d32', display: 'block', marginBottom: '0.5rem'}}>
                            ✓ Your Matching Skills ({job.matchingSkills.length}):
                          </strong>
                          <div style={{display: 'flex', gap: '0.5rem', flexWrap: 'wrap'}}>
                            {job.matchingSkills.slice(0, 10).map((skill: string, idx: number) => (
                              <span key={idx} style={{
                                padding: '0.25rem 0.75rem',
                                backgroundColor: '#4caf50',
                                color: 'white',
                                borderRadius: '12px',
                                fontSize: '0.85em',
                                fontWeight: '500'
                              }}>
                                {skill}
                              </span>
                            ))}
                            {job.matchingSkills.length > 10 && (
                              <span style={{
                                padding: '0.25rem 0.75rem',
                                color: '#2e7d32',
                                fontSize: '0.85em',
                                fontStyle: 'italic'
                              }}>
                                +{job.matchingSkills.length - 10} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                      
                      <div style={{marginTop: '1rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '4px'}}>
                        <strong>Description:</strong>
                        <p style={{
                          margin: '0.5rem 0 0 0',
                          whiteSpace: 'pre-wrap',
                          wordWrap: 'break-word',
                          lineHeight: '1.5',
                          maxHeight: isExpanded ? 'none' : '150px',
                          overflow: isExpanded ? 'visible' : 'hidden',
                          transition: 'max-height 0.3s ease'
                        }}>
                          {description}
                        </p>
                        {shouldTruncate && (
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              toggleJobDescription(`job-search-${index}`);
                            }}
                            style={{
                              marginTop: '0.75rem',
                              padding: '0.5rem 1.25rem',
                              backgroundColor: '#61dafb',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '0.95em',
                              fontWeight: '600',
                              transition: 'all 0.2s ease',
                              display: 'block'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.backgroundColor = '#4db8d8';
                              e.currentTarget.style.transform = 'scale(1.05)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.backgroundColor = '#61dafb';
                              e.currentTarget.style.transform = 'scale(1)';
                            }}
                          >
                            {isExpanded ? '▲ Show Less' : '▼ View More'}
                          </button>
                        )}
                      </div>
                      {job.url && (
                        <a href={job.url} target="_blank" rel="noopener noreferrer" style={{display: 'inline-block', marginTop: '1rem'}}>
                          Apply Here
                        </a>
                      )}
                    </div>
                  );
                })}
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

        {activeTab === 'resume' && (
          <>
            <div className="resume-optimizer">
              <h2>Resume Optimizer</h2>
            
            <div className="resume-section">
              <h3>Upload Your Resume (PDF)</h3>
              <div className="upload-section">
                <div className="form-group">
                  <label>Upload PDF Resume:</label>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                  />
                  {selectedFile && (
                    <p className="file-info">Selected: {selectedFile.name}</p>
                  )}
                </div>
                <button 
                  onClick={uploadResume} 
                  className="submit-btn"
                  disabled={!selectedFile}
                >
                  Upload & Parse Resume
                </button>
                {uploadStatus && (
                  <p className={`upload-status ${uploadStatus.includes('Error') ? 'error' : 'success'}`}>
                    {uploadStatus}
                  </p>
                )}
              </div>

              {parsedResume && (
                <div className="parsed-resume-preview">
                  <h4>Resume Parsed Successfully!</h4>
                  <p><strong>File:</strong> {parsedResume.filename}</p>
                  
                  <div className="parsed-sections">
                    <h5>Extracted Sections:</h5>
                    {Object.entries(parsedResume.sections).map(([section, content]: [string, any]) => {
                      const isExpanded = expandedJobDescriptions.has(`resume-${section}`);
                      const charLimit = 200;
                      const shouldTruncate = content.length > charLimit;
                      
                      return (
                        <div key={section} className="section-preview">
                          <h6>{section.charAt(0).toUpperCase() + section.slice(1)}:</h6>
                          <p>
                            {isExpanded ? content : content.substring(0, charLimit)}
                            {shouldTruncate && !isExpanded && '...'}
                          </p>
                          {shouldTruncate && (
                            <button
                              onClick={() => toggleJobDescription(`resume-${section}`)}
                              style={{
                                marginTop: '0.5rem',
                                padding: '0.25rem 0.75rem',
                                backgroundColor: '#61dafb',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '0.85em',
                                fontWeight: '500'
                              }}
                            >
                              {isExpanded ? 'Show Less' : 'View More'}
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {parsedResume.extracted_experiences && parsedResume.extracted_experiences.length > 0 && (
                    <div className="extracted-experiences">
                      <h5>Extracted Experiences:</h5>
                      <ul>
                        {parsedResume.extracted_experiences.map((exp: any, index: number) => (
                          <li key={index}>
                            <strong>{exp.role}</strong> at {exp.company} ({exp.duration})
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
              </div>
            </div>
    
            <div className="resume-section">
              <div className="section-header">
                <h3>Add Your Experience (Manual)</h3>
              </div>
              <div className="experience-form">
                <div className="form-row">
                  <div className="form-group">
                    <div className="label-container">
                      <label>Role/Position:</label>
                    </div>
                    <div className="input-container">
                      <input
                        type="text"
                        value={currentExperience.role}
                        onChange={(e) => setCurrentExperience({...currentExperience, role: e.target.value})}
                        placeholder="e.g., Senior Python Developer"
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Company:</label>
                    <input
                      type="text"
                      value={currentExperience.company}
                      onChange={(e) => setCurrentExperience({...currentExperience, company: e.target.value})}
                      placeholder="e.g., Tech Corp"
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Duration:</label>
                  <input
                    type="text"
                    value={currentExperience.duration}
                    onChange={(e) => setCurrentExperience({...currentExperience, duration: e.target.value})}
                    placeholder="e.g., 2020-2023"
                  />
                </div>
                <div className="form-group">
                  <label>Achievements (one per line):</label>
                  <textarea
                    value={currentExperience.achievements}
                    onChange={(e) => setCurrentExperience({...currentExperience, achievements: e.target.value})}
                    placeholder="• Increased system performance by 40%
• Led team of 5 developers
• Implemented CI/CD pipeline"
                    rows={4}
                  />
                </div>
                <div className="form-group">
                  <label>Skills (comma-separated):</label>
                  <input
                    type="text"
                    value={currentExperience.skills}
                    onChange={(e) => setCurrentExperience({...currentExperience, skills: e.target.value})}
                    placeholder="Python, FastAPI, React, Docker"
                  />
                </div>
                <div className="button-container">
                  <button onClick={addUserExperience} className="submit-btn">
                    Add Experience
                  </button>
                </div>
              </div>

              {userExperiences.length > 0 && (
                <div className="experiences-list">
                  <h4>Your Experiences:</h4>
                  {userExperiences.map((exp, index) => (
                    <div key={index} className="experience-card">
                      <h5>{exp.role} at {exp.company}</h5>
                      <p><strong>Duration:</strong> {exp.duration}</p>
                      <p><strong>Skills:</strong> {exp.skills.join(', ')}</p>
                      <details>
                        <summary>Achievements</summary>
                        <ul>
                          {exp.achievements.map((achievement, i) => (
                            <li key={i}>{achievement}</li>
                          ))}
                        </ul>
                      </details>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="resume-section">
              <div className="section-header">
                <h3>Optimize Resume for Job</h3>
              </div>
              <div className="optimization-form">
                <div className="form-group">
                  <label>Job Description:</label>
                  <textarea
                    value={resumeJobDescription}
                    onChange={(e) => setResumeJobDescription(e.target.value)}
                    placeholder="Paste the job description here..."
                    rows={6}
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Target Role:</label>
                    <input
                      type="text"
                      value={targetRole}
                      onChange={(e) => setTargetRole(e.target.value)}
                      placeholder="e.g., Senior Python Developer"
                    />
                  </div>
                  <div className="form-group">
                    <label>Target Company:</label>
                    <input
                      type="text"
                      value={targetCompany}
                      onChange={(e) => setTargetCompany(e.target.value)}
                      placeholder="e.g., Google"
                    />
                  </div>
                </div>
                <div className="button-container">
                  <button onClick={optimizeResume} className="submit-btn">
                    Optimize Resume
                  </button>
                </div>
              </div>

              <div className="optimization-container">
              {resumeOptimization && (
                <div className="optimization-results">
                  <div className="results-header">
                    <h4>Resume Optimization Suggestions</h4>
                  </div>
                  
                  <div className="result-section">
                    <h5>Key Skills & Keywords to Highlight:</h5>
                    <div className="keyword-tags">
                      {resumeOptimization.keyword_suggestions?.map((keyword: string, index: number) => (
                        <span key={index} className="keyword-tag">{keyword}</span>
                      ))}
                    </div>
                  </div>

                  <div className="result-section">
                    <h5>Resume Sections to Focus On:</h5>
                    <ul>
                      {resumeOptimization.optimized_resume_sections?.map((section: string, index: number) => (
                        <li key={index}>{section}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="result-section">
                    <h5>Tailoring Recommendations:</h5>
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {resumeOptimization.tailoring_recommendations?.join('\n\n')}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {resumeOptimization.experience_matches && resumeOptimization.experience_matches.length > 0 && (
                    <div className="result-section">
                      <h5>Relevant Experience Matches:</h5>
                      <ul>
                        {resumeOptimization.experience_matches.map((match: string, index: number) => (
                          <li key={index}>{match.substring(0, 100)}...</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          </>
        )}
        {activeTab === 'rag' && (
            <div className="advanced-rag">
              <h2>Advanced RAG Pipeline Demo</h2>
              <p className="rag-description">
                Experience cutting-edge LangChain RAG capabilities including query expansion, re-ranking, and performance evaluation.
              </p>

              <div className="rag-section">
                <h3>Query Advanced RAG</h3>
                  <div className="rag-query-form">
                  <div className="form-group">
                    <label>Ask a complex question about career development:</label>
                    <textarea
                      value={ragQuestion}
                      onChange={(e) => setRagQuestion(e.target.value)}
                      placeholder="e.g., What are the best strategies for learning advanced LangChain techniques for production RAG systems?"
                      rows={3}
                    />
                  </div>
                  <button onClick={queryAdvancedRAG} className="submit-btn" disabled={ragLoading}>
                    {ragLoading ? (
                      <>
                        <span className="spinner"></span>
                        Processing Query...
                      </>
                    ) : (
                      'Query Advanced RAG'
                    )}
                  </button>
                  <div className="info-hint">
                    <p><strong>Tip:</strong> After running a query, check the "Performance Evaluation & Quality Metrics" section below to see detailed analytics about the RAG pipeline's performance!</p>
                  </div>
                </div>

                {ragLoading && (
                  <div className="loading-container">
                    <div className="spinner-large"></div>
                    <p>Processing your query with advanced RAG pipeline...</p>
                    <p className="loading-sub">This includes query expansion, semantic search, and AI re-ranking</p>
                  </div>
                )}

                {ragResponse && (
                  <div className="rag-results">
                    <h4>Advanced RAG Response</h4>

                    <div className="result-section">
                      <h5>Question:</h5>
                      <p>{ragResponse.question}</p>
                    </div>

                    <div className="result-section">
                      <h5>Answer:</h5>
                      <div className="markdown-content">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {ragResponse.answer}
                        </ReactMarkdown>
                      </div>
                    </div>

                    <div className="result-section">
                      <h5>Pipeline Used:</h5>
                      <p>{ragResponse.pipeline_used}</p>
                    </div>

                    {ragResponse.evaluation && (
                      <div className="accordion-item">
                        <div className="accordion-header" onClick={() => setExpandedAccordion(expandedAccordion === 'evaluation' ? null : 'evaluation')}>
                          <span className="accordion-title">
                            {expandedAccordion === 'evaluation' ? '▼' : '▶'} Performance Evaluation & Quality Metrics
                          </span>
                        </div>
                        {expandedAccordion === 'evaluation' && (
                          <div className="accordion-content">
                            <div className="evaluation-grid">
                              {ragResponse.evaluation.generation_metrics && (
                                <div className="metric-box">
                                  <div className="metric-label">Generation Metrics</div>
                                  <div className="metric-content">
                                    <div className="metric-item">
                                      <span className="metric-name">Response Length:</span>
                                      <span className="metric-value">{ragResponse.evaluation.generation_metrics.response_length} characters</span>
                                    </div>
                                    <div className="metric-item">
                                      <span className="metric-name">Context Docs Used:</span>
                                      <span className="metric-value">{ragResponse.evaluation.generation_metrics.context_docs_used}</span>
                                    </div>
                                  </div>
                                </div>
                              )}
                              <div className="metric-box">
                                <div className="metric-label">LLM Quality Evaluation</div>
                                <div className="llm-evaluation">
                                  {ragResponse.evaluation.generation_metrics?.evaluation || 'Evaluation in progress...'}
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="rag-section">
                <div className="accordion-item">
                  <div className="accordion-header" onClick={() => setExpandedAccordion(expandedAccordion === 'pipeline' ? null : 'pipeline')}>
                    <span className="accordion-title">
                      {expandedAccordion === 'pipeline' ? '▼' : '▶'} For Developers - Pipeline Status & Architecture
                    </span>
                  </div>
                  {expandedAccordion === 'pipeline' && (
                    <div className="accordion-content">
                      {metricsLoading ? (
                        <div className="loading-container">
                          <div className="spinner-large"></div>
                          <p>Loading pipeline information...</p>
                        </div>
                      ) : ragMetrics ? (
                        <div className="pipeline-status-grid">
                          <div className="status-box">
                            <div className="status-label">Pipeline Status</div>
                            <span className={`status-badge ${ragMetrics.pipeline_status === 'active' ? 'active' : 'inactive'}`}>
                              {ragMetrics.pipeline_status === 'active' ? 'ACTIVE' : 'INACTIVE'}
                            </span>
                          </div>

                          <div className="info-box">
                            <div className="section-label">Advanced Components</div>
                            <ul className="component-list">
                              {ragMetrics.components?.map((component: string, index: number) => (
                                <li key={index}><code>{component}</code></li>
                              ))}
                            </ul>
                          </div>

                          <div className="info-box">
                            <div className="section-label">Key Capabilities</div>
                            <ul className="capabilities-list">
                              {ragMetrics.capabilities?.map((capability: string, index: number) => (
                                <li key={index}>{capability}</li>
                              ))}
                            </ul>
                          </div>

                          {ragMetrics.test_results && (
                            <div className="info-box">
                              <div className="section-label">Pipeline Test Results</div>
                              <ul className="test-results-list">
                                <li><strong>Query Expansion:</strong> {ragMetrics.test_results.expanded_results_count} results</li>
                                <li><strong>Re-ranking:</strong> {ragMetrics.test_results.reranked_results_count} results</li>
                                <li><strong>Answer Preview:</strong> {ragMetrics.test_results.answer_preview}</li>
                              </ul>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="info-box">
                          <p style={{margin: 0, color: '#666'}}>Unable to load pipeline information. Please try refreshing or contact support.</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
      </main>
    </div>
  );
}

export default App;
