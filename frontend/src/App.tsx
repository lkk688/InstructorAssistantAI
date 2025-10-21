import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

interface Course {
  id: number;
  name: string;
  course_code: string;
}

interface Student {
  id: number;
  name: string;
  email: string;
  sis_user_id: string;
}

interface Assignment {
  id: number;
  name: string;
  points_possible: number;
  due_at: string;
  submission_types: string[];
}

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const API_BASE_URL = 'http://localhost:8000';

function App() {
  // Tab state
  const [activeTab, setActiveTab] = useState<'connection' | 'upload'>('connection');
  
  // Connection tab state
  const [canvasUrl, setCanvasUrl] = useState('');
  const [canvasToken, setCanvasToken] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connected' | 'testing'>('disconnected');
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [courseFilter, setCourseFilter] = useState('');
  const [students, setStudents] = useState<Student[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  
  // Upload tab state
  const [file, setFile] = useState<File | null>(null);
  const [quizTitle, setQuizTitle] = useState('');
  const [quizDescription, setQuizDescription] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  
  // Chatbot state
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I\'m your AI assistant. I can help you with Canvas operations, quiz creation, and answer questions about your courses.',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const testConnection = async () => {
    if (!canvasUrl || !canvasToken) {
      alert('Please enter both Canvas URL and API token');
      return;
    }

    setConnectionStatus('testing');
    try {
      const response = await axios.get(`${API_BASE_URL}/test-api`, {
        params: { canvas_url: canvasUrl, canvas_token: canvasToken }
      });
      
      if (response.data.success) {
        setConnectionStatus('connected');
        loadCourses();
      } else {
        setConnectionStatus('disconnected');
        alert('Connection failed: ' + response.data.message);
      }
    } catch (error) {
      setConnectionStatus('disconnected');
      alert('Connection failed: ' + (error as Error).message);
    }
  };

  const loadCourses = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/courses`, {
        params: { 
          canvas_url: canvasUrl, 
          canvas_token: canvasToken,
          prefix_filter: courseFilter || undefined
        }
      });
      setCourses(response.data);
    } catch (error) {
      console.error('Failed to load courses:', error);
    }
  };

  const selectCourse = async (course: Course) => {
    setSelectedCourse(course);
    
    // Load students and assignments for the selected course
    try {
      const [studentsResponse, assignmentsResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/courses/${course.id}/students`, {
          params: { canvas_url: canvasUrl, canvas_token: canvasToken }
        }),
        axios.get(`${API_BASE_URL}/courses/${course.id}/assignments`, {
          params: { canvas_url: canvasUrl, canvas_token: canvasToken }
        })
      ]);
      
      setStudents(studentsResponse.data);
      setAssignments(assignmentsResponse.data);
    } catch (error) {
      console.error('Failed to load course data:', error);
    }
  };

  const downloadStudents = async () => {
    if (!selectedCourse) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/courses/${selectedCourse.id}/students/export`, {
        params: { canvas_url: canvasUrl, canvas_token: canvasToken },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${selectedCourse.course_code}_students.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to download students:', error);
    }
  };

  const downloadAssignments = async () => {
    if (!selectedCourse) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/courses/${selectedCourse.id}/assignments/export`, {
        params: { canvas_url: canvasUrl, canvas_token: canvasToken },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${selectedCourse.course_code}_assignments.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to download assignments:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      // Call the actual LLM backend
      const response = await axios.post(`${API_BASE_URL}/chat/completions`, {
        messages: [
          {
            role: 'user',
            content: userMessage.content
          }
        ],
        model: 'gpt-3.5-turbo',
        max_tokens: 500,
        temperature: 0.7
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.data.choices[0].message.content,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    } catch (error: any) {
      setIsTyping(false);
      console.error('Failed to send message:', error);
      
      // Show error message to user
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message || 'Unknown error'}. Please make sure your OpenAI API key is configured or try using a local Ollama model.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const uploadQuiz = async () => {
    if (!file || !selectedCourse || !quizTitle) {
      alert('Please select a file, course, and enter a quiz title');
      return;
    }

    setIsUploading(true);
    setUploadStatus('Uploading quiz...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('course_id', selectedCourse.id.toString());
    formData.append('quiz_title', quizTitle);
    formData.append('quiz_description', quizDescription);
    formData.append('canvas_url', canvasUrl);
    formData.append('canvas_token', canvasToken);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload-quiz`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        setUploadStatus('Quiz uploaded successfully!');
        setFile(null);
        setQuizTitle('');
        setQuizDescription('');
      } else {
        setUploadStatus('Upload failed: ' + response.data.message);
      }
    } catch (error) {
      setUploadStatus('Upload failed: ' + (error as Error).message);
    } finally {
      setIsUploading(false);
    }
  };

  const renderConnectionTab = () => (
    <div className="tab-content">
      <div className="connection-grid">
        {/* Canvas Setup */}
        <div className="connection-section">
          <h3>Canvas Setup</h3>
          <div className="form-group">
            <label>Canvas URL</label>
            <input
              type="text"
              className="input"
              placeholder="https://your-institution.instructure.com"
              value={canvasUrl}
              onChange={(e) => setCanvasUrl(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>API Token</label>
            <input
              type="password"
              className="input"
              placeholder="Your Canvas API token"
              value={canvasToken}
              onChange={(e) => setCanvasToken(e.target.value)}
            />
          </div>
          <button className="button button-primary" onClick={testConnection}>
            Test Connection
          </button>
          <div className="status-indicator-container" style={{ marginTop: '16px' }}>
            <span className={`status-indicator ${connectionStatus}`}>
              <span className="status-dot"></span>
              {connectionStatus === 'connected' && 'Connected'}
              {connectionStatus === 'disconnected' && 'Disconnected'}
              {connectionStatus === 'testing' && 'Testing...'}
            </span>
          </div>
        </div>

        {/* Course Search */}
        <div className="connection-section">
          <h3>Course Search</h3>
          <div className="form-group">
            <label>Filter Courses</label>
            <div className="course-filter">
              <input
                type="text"
                className="input"
                placeholder="Enter course prefix (e.g., CS, MATH)"
                value={courseFilter}
                onChange={(e) => setCourseFilter(e.target.value)}
              />
              <button className="button" onClick={loadCourses}>
                Search
              </button>
            </div>
          </div>
          {courses.length > 0 && (
            <div className="course-list">
              {courses.map((course) => (
                <div
                  key={course.id}
                  className={`course-item ${selectedCourse?.id === course.id ? 'selected' : ''}`}
                  onClick={() => selectCourse(course)}
                >
                  <div className="course-name">{course.name}</div>
                  <div className="course-code">{course.course_code}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Download Functions */}
        {selectedCourse && (
          <div className="connection-section">
            <h3>Download Data</h3>
            <p>Selected Course: <strong>{selectedCourse.name}</strong></p>
            <div className="download-actions">
              <button className="download-button" onClick={downloadStudents}>
                📥 Download Students ({students.length})
              </button>
              <button className="download-button" onClick={downloadAssignments}>
                📋 Download Assignments ({assignments.length})
              </button>
            </div>
          </div>
        )}

        {/* AI Chatbot */}
        <div className="chatbot-container">
          <div className="chatbot-header">
            🤖 AI Assistant
          </div>
          <div className="chatbot-messages">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.type}`}>
                <div className="message-avatar">
                  {message.type === 'user' ? 'U' : 'AI'}
                </div>
                <div className="message-content">
                  {message.content}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="message assistant">
                <div className="message-avatar">AI</div>
                <div className="message-content">Typing...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="chatbot-input">
            <input
              type="text"
              placeholder="Ask me anything about Canvas or your courses..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              disabled={isTyping}
            />
            <button
              className="send-button"
              onClick={sendMessage}
              disabled={isTyping || !inputMessage.trim()}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderUploadTab = () => (
    <div className="tab-content">
      <div className="form-section">
        <h2>Upload Quiz to Canvas</h2>
        
        {!selectedCourse && (
          <div className="alert alert-warning">
            Please select a course in the Connection tab first.
          </div>
        )}

        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="quiz-title">Quiz Title *</label>
            <input
              id="quiz-title"
              type="text"
              className="input"
              placeholder="Enter quiz title"
              value={quizTitle}
              onChange={(e) => setQuizTitle(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="quiz-file">Quiz File *</label>
            <input
              id="quiz-file"
              type="file"
              className="input"
              accept=".md,.txt"
              onChange={handleFileChange}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="quiz-description">Quiz Description</label>
          <textarea
            id="quiz-description"
            className="input"
            rows={4}
            placeholder="Enter quiz description (optional)"
            value={quizDescription}
            onChange={(e) => setQuizDescription(e.target.value)}
          />
        </div>

        {selectedCourse && (
          <div className="selected-course">
            <strong>Selected Course:</strong> {selectedCourse.name} ({selectedCourse.course_code})
          </div>
        )}

        <button
          className="button button-primary"
          onClick={uploadQuiz}
          disabled={isUploading || !file || !quizTitle || !selectedCourse}
        >
          {isUploading ? 'Uploading...' : 'Upload Quiz'}
        </button>

        {uploadStatus && (
          <div className={`status-message ${uploadStatus.includes('success') ? 'success' : 'error'}`}>
            {uploadStatus}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <h1>Instructor Assistant AI</h1>
          <p>Manage your Canvas courses and upload quizzes with AI assistance</p>
        </div>

        <div className="tab-navigation">
          <button
            className={`tab-button ${activeTab === 'connection' ? 'active' : ''}`}
            onClick={() => setActiveTab('connection')}
          >
            🔗 Connection & AI
          </button>
          <button
            className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            📤 Upload Quiz
          </button>
        </div>

        {activeTab === 'connection' && renderConnectionTab()}
        {activeTab === 'upload' && renderUploadTab()}
      </div>
    </div>
  );
}

export default App;
