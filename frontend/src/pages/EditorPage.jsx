/**
 * SkillTree AI - Editor Page
 * Code editor with execution and AI assistance
 * @module pages/EditorPage
 */

import { useState, useEffect } from 'react';
import useExecution from '../hooks/useExecution';
import * as executionApi from '../api/executionApi';

/**
 * Supported programming languages
 * @typedef {Object} Language
 * @property {string} id - Language ID
 * @property {string} name - Display name
 * @property {string} icon - Icon emoji
 */

/**
 * @type {Language[]}
 */
const LANGUAGES = [
  { id: 'python', name: 'Python', icon: '🐍' },
  { id: 'javascript', name: 'JavaScript', icon: '📜' },
  { id: 'java', name: 'Java', icon: '☕' },
  { id: 'cpp', name: 'C++', icon: '⚡' },
  { id: 'c', name: 'C', icon: '🔧' },
  { id: 'csharp', name: 'C#', icon: '🎯' },
  { id: 'go', name: 'Go', icon: '🐹' },
  { id: 'rust', name: 'Rust', icon: '🦀' },
  { id: 'typescript', name: 'TypeScript', icon: '📘' },
];

/**
 * Default code templates by language
 * @type {Object.<string, string>}
 */
const CODE_TEMPLATES = {
  python: `# Welcome to SkillTree AI Editor\n# Write your code here\n\ndef main():\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()`,
  javascript: `// Welcome to SkillTree AI Editor\n// Write your code here\n\nfunction main() {\n  console.log("Hello, World!");\n}\n\nmain();`,
  java: `// Welcome to SkillTree AI Editor\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}`,
  cpp: `// Welcome to SkillTree AI Editor\n#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}`,
  c: `// Welcome to SkillTree AI Editor\n#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}`,
  csharp: `// Welcome to SkillTree AI Editor\nusing System;\n\nclass Program {\n    static void Main() {\n        Console.WriteLine("Hello, World!");\n    }\n}`,
  go: `// Welcome to SkillTree AI Editor\npackage main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}`,
  rust: `// Welcome to SkillTree AI Editor\nfn main() {\n    println!("Hello, World!");\n}`,
  typescript: `// Welcome to SkillTree AI Editor\nfunction main(): void {\n  console.log("Hello, World!");\n}\n\nmain();`,
};

/**
 * Editor page component
 * @returns {JSX.Element} Editor page
 */
function EditorPage() {
  const { execute, status, output, error, executionTime, isRunning, reset } = useExecution();

  const [code, setCode] = useState(CODE_TEMPLATES.python);
  const [language, setLanguage] = useState('python');
  const [input, setInput] = useState('');
  const [showInput, setShowInput] = useState(false);
  const [languages, setLanguages] = useState(LANGUAGES);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  // Load supported languages on mount
  useEffect(() => {
    const loadLanguages = async () => {
      try {
        const supported = await executionApi.getSupportedLanguages();
        if (supported?.length) {
          const langMap = LANGUAGES.reduce((acc, l) => ({ ...acc, [l.id]: l }), {});
          const filtered = supported.map(id => langMap[id] || { id, name: id, icon: '📄' });
          setLanguages(filtered);
        }
      } catch (e) {
        console.warn('Failed to load languages, using defaults');
      }
    };
    loadLanguages();
  }, []);

  /**
   * Handle language change
   * @param {string} newLang - New language ID
   */
  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    if (!code || code === CODE_TEMPLATES[language]) {
      setCode(CODE_TEMPLATES[newLang] || '// Start coding...');
    }
  };

  /**
   * Handle code execution
   */
  const handleRun = async () => {
    try {
      const result = await execute({
        code,
        language,
        input: showInput ? input : undefined,
      });
      
      // Add to history
      setHistory(prev => [{
        id: Date.now(),
        code,
        language,
        output: result?.output || '',
        status: result?.status,
        timestamp: new Date().toISOString(),
      }, ...prev.slice(0, 19)]);
    } catch (e) {
      // Error handled by hook
    }
  };

  /**
   * Handle code reset
   */
  const handleReset = () => {
    setCode(CODE_TEMPLATES[language] || '');
    setInput('');
    reset();
  };

  /**
   * Load code from history
   * @param {Object} item - History item
   */
  const loadFromHistory = (item) => {
    setCode(item.code);
    setLanguage(item.language);
    setShowHistory(false);
  };

  /**
   * Get status indicator
   * @returns {string} Status text
   */
  const getStatusText = () => {
    if (isRunning) return 'Running...';
    if (status === 'success') return 'Completed';
    if (status === 'error') return 'Error';
    if (status === 'timeout') return 'Timeout';
    return 'Ready';
  };

  return (
    <div className="editor-page">
      <div className="editor-header">
        <div className="header-left">
          <h1>Code Editor</h1>
          <span className={`status-indicator ${status}`}>{getStatusText()}</span>
        </div>
        <div className="header-right">
          <button
            className="icon-button"
            onClick={() => setShowHistory(!showHistory)}
            title="History"
          >
            🕐
          </button>
        </div>
      </div>

      <div className="editor-container">
        {/* Sidebar */}
        <div className="editor-sidebar glass-panel">
          <div className="sidebar-section">
            <h3>Language</h3>
            <select
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value)}
              className="language-select"
            >
              {languages.map((lang) => (
                <option key={lang.id} value={lang.id}>
                  {lang.icon} {lang.name}
                </option>
              ))}
            </select>
          </div>

          <div className="sidebar-section">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showInput}
                onChange={(e) => setShowInput(e.target.checked)}
              />
              Show Input
            </label>
          </div>

          {showInput && (
            <div className="sidebar-section">
              <h3>Input</h3>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="input-textarea"
                placeholder="Enter input for your program..."
              />
            </div>
          )}

          <div className="sidebar-actions">
            <button
              onClick={handleRun}
              disabled={isRunning || !code.trim()}
              className="run-button primary-cta"
            >
              {isRunning ? 'Running...' : '▶ Run'}
            </button>
            <button onClick={handleReset} className="reset-button secondary-cta">
              ↺ Reset
            </button>
          </div>

          {executionTime && (
            <div className="execution-time">
              Executed in {executionTime}ms
            </div>
          )}
        </div>

        {/* Main Editor */}
        <div className="editor-main">
          <div className="code-editor glass-panel">
            <div className="editor-toolbar">
              <span className="file-name">{language.toUpperCase()}</span>
              <span className="line-count">{code.split('\n').length} lines</span>
            </div>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="code-textarea"
              placeholder="Write your code here..."
              spellCheck={false}
              autoCapitalize="off"
              autoComplete="off"
            />
          </div>

          {/* Output Panel */}
          <div className="output-panel glass-panel">
            <div className="output-header">
              <h3>Output</h3>
              {output && (
                <button
                  onClick={() => navigator.clipboard.writeText(output)}
                  className="copy-button"
                >
                  📋 Copy
                </button>
              )}
            </div>
            <div className="output-content">
              {error && <div className="output-error">{error}</div>}
              {output && <pre className="output-text">{output}</pre>}
              {!output && !error && <div className="output-placeholder">Run your code to see output</div>}
            </div>
          </div>
        </div>

        {/* History Panel */}
        {showHistory && (
          <div className="history-panel glass-panel">
            <div className="history-header">
              <h3>History</h3>
              <button onClick={() => setShowHistory(false)}>×</button>
            </div>
            <div className="history-list">
              {history.length === 0 ? (
                <div className="history-empty">No history yet</div>
              ) : (
                history.map((item) => (
                  <div
                    key={item.id}
                    className="history-item"
                    onClick={() => loadFromHistory(item)}
                  >
                    <div className="history-lang">{item.language}</div>
                    <div className="history-preview">
                      {item.code.split('\n')[0].slice(0, 50)}...
                    </div>
                    <div className="history-time">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default EditorPage;