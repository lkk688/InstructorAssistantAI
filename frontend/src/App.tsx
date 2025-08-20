import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

interface Course {
  id: number;
  name: string;
  course_code: string;
}

interface UploadProgress {
  status: 'idle' | 'uploading' | 'success' | 'error';
  message: string;
  progress: number;
}

function App() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [quizTitle, setQuizTitle] = useState('');
  const [timeLimit, setTimeLimit] = useState<number>(30);
  const [published, setPublished] = useState<boolean>(false);
  const [coursePrefix, setCoursePrefix] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    status: 'idle',
    message: '',
    progress: 0
  });
  const [loadingCourses, setLoadingCourses] = useState<boolean>(false);

  // Fetch courses on component mount
  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async (prefix?: string) => {
    setLoadingCourses(true);
    try {
      const params = prefix ? { course_prefix: prefix } : {};
      const response = await axios.get('http://localhost:8000/courses', { params });
      setCourses(response.data);
    } catch (error) {
      console.error('Failed to fetch courses:', error);
      setUploadProgress({
        status: 'error',
        message: 'Failed to fetch courses. Make sure the backend is running.',
        progress: 0
      });
    } finally {
      setLoadingCourses(false);
    }
  };

  const handleCourseFilter = () => {
    fetchCourses(coursePrefix || undefined);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    if (selectedFile && !quizTitle) {
      // Auto-generate quiz title from filename
      const nameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, "");
      setQuizTitle(nameWithoutExt.replace(/[_-]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()));
    }
  };

  const handleUpload = async () => {
    if (!file || !selectedCourse || !quizTitle.trim()) {
      setUploadProgress({
        status: 'error',
        message: 'Please select a course, enter a quiz title, and choose a file.',
        progress: 0
      });
      return;
    }

    setUploadProgress({ status: 'uploading', message: 'Uploading quiz...', progress: 25 });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('course_id', selectedCourse);
      formData.append('quiz_title', quizTitle);
      formData.append('time_limit', timeLimit.toString());
      formData.append('published', published.toString());

      setUploadProgress({ status: 'uploading', message: 'Processing questions...', progress: 50 });

      const response = await axios.post('http://localhost:8000/upload-quiz', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadProgress({ status: 'uploading', message: 'Finalizing quiz...', progress: 75 });

      setTimeout(() => {
        setUploadProgress({
          status: 'success',
          message: `Quiz "${response.data.quiz_title}" created successfully! ${response.data.successful_uploads}/${response.data.total_questions} questions uploaded.`,
          progress: 100
        });
      }, 500);

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to upload quiz. Please try again.';
      setUploadProgress({
        status: 'error',
        message: errorMessage,
        progress: 0
      });
    }
  };

  const resetForm = () => {
    setFile(null);
    setQuizTitle('');
    setTimeLimit(30);
    setPublished(false);
    setUploadProgress({ status: 'idle', message: '', progress: 0 });
  };

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>📚 Instructor Assistant</h1>
          <p>Upload quiz questions to Canvas with ease</p>
        </header>

        <div className="form-section">
          <h2>🎯 Select Course</h2>
          <div className="course-filter">
            <input
              type="text"
              placeholder="Filter courses by prefix (e.g., SP25, CMPE)"
              value={coursePrefix}
              onChange={(e) => setCoursePrefix(e.target.value)}
              className="input"
            />
            <button onClick={handleCourseFilter} className="btn btn-secondary" disabled={loadingCourses}>
              {loadingCourses ? 'Loading...' : 'Filter'}
            </button>
          </div>
          
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="select"
            disabled={loadingCourses}
          >
            <option value="">Select a course...</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id.toString()}>
                {course.course_code} - {course.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-section">
          <h2>📝 Quiz Configuration</h2>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="quizTitle">Quiz Title</label>
              <input
                id="quizTitle"
                type="text"
                placeholder="Enter quiz title"
                value={quizTitle}
                onChange={(e) => setQuizTitle(e.target.value)}
                className="input"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="timeLimit">Time Limit (minutes)</label>
              <input
                id="timeLimit"
                type="number"
                min="1"
                max="300"
                value={timeLimit}
                onChange={(e) => setTimeLimit(parseInt(e.target.value) || 30)}
                className="input"
              />
            </div>
          </div>
          
          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={published}
                onChange={(e) => setPublished(e.target.checked)}
              />
              <span className="checkmark"></span>
              Publish quiz immediately
            </label>
          </div>
        </div>

        <div className="form-section">
          <h2>📄 Upload Questions</h2>
          <div className="file-upload">
            <input
              type="file"
              accept=".md,.txt"
              onChange={handleFileChange}
              className="file-input"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="file-label">
              {file ? `📎 ${file.name}` : '📁 Choose markdown or text file'}
            </label>
          </div>
          {file && (
            <div className="file-info">
              <p>File: {file.name} ({(file.size / 1024).toFixed(1)} KB)</p>
            </div>
          )}
        </div>

        {uploadProgress.status !== 'idle' && (
          <div className="progress-section">
            <div className={`progress-bar ${uploadProgress.status}`}>
              <div 
                className="progress-fill" 
                style={{ width: `${uploadProgress.progress}%` }}
              ></div>
            </div>
            <p className={`status-message ${uploadProgress.status}`}>
              {uploadProgress.message}
            </p>
          </div>
        )}

        <div className="actions">
          <button
            onClick={handleUpload}
            disabled={!file || !selectedCourse || !quizTitle.trim() || uploadProgress.status === 'uploading'}
            className="btn btn-primary"
          >
            {uploadProgress.status === 'uploading' ? '⏳ Uploading...' : '🚀 Upload Quiz'}
          </button>
          
          {uploadProgress.status === 'success' && (
            <button onClick={resetForm} className="btn btn-secondary">
              📝 Create Another Quiz
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
