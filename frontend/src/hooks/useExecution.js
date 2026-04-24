/**
 * SkillTree AI - Execution Hook
 * Custom hook for code execution with polling and state management
 * @module hooks/useExecution
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import * as executionApi from '../api/executionApi';

/**
 * Execution status states
 * @readonly
 * @enum {string}
 */
const EXECUTION_STATUS = {
  IDLE: 'idle',
  RUNNING: 'running',
  SUCCESS: 'success',
  ERROR: 'error',
  TIMEOUT: 'timeout',
};

/**
 * Custom hook for code execution
 * @param {Object} options - Hook options
 * @param {number} options.pollInterval - Polling interval in ms (default: 1000)
 * @param {number} options.timeout - Execution timeout in ms (default: 30000)
 * @returns {Object} Execution methods and state
 */
export function useExecution(options = {}) {
  const { pollInterval = 1000, timeout = 30000 } = options;

  const [status, setStatus] = useState(EXECUTION_STATUS.IDLE);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [output, setOutput] = useState('');
  const [executionTime, setExecutionTime] = useState(null);

  const pollTimeoutRef = useRef(null);
  const executionStartRef = useRef(null);

  /**
   * Execute code
   * @param {Object} executionData - Code execution data
   * @param {string} executionData.code - Code to execute
   * @param {string} executionData.language - Programming language
   * @param {string} executionData.input - Optional input
   * @param {string} executionData.skillId - Optional skill ID
   * @param {string} executionData.questId - Optional quest ID
   * @returns {Promise<Object>} Execution result
   */
  const execute = useCallback(async (executionData) => {
    // Clear previous state
    setStatus(EXECUTION_STATUS.RUNNING);
    setResult(null);
    setError(null);
    setOutput('');
    setExecutionTime(null);
    
    executionStartRef.current = Date.now();

    try {
      // Submit execution
      const initialResult = await executionApi.executeCode(executionData);
      
      // If execution is synchronous, return result
      if (initialResult.status === 'completed' || initialResult.output !== undefined) {
        const execTime = Date.now() - executionStartRef.current;
        setExecutionTime(execTime);
        setResult(initialResult);
        setOutput(initialResult.output || '');
        setStatus(EXECUTION_STATUS.SUCCESS);
        return initialResult;
      }

      // If async, poll for results
      const executionId = initialResult.id;
      
      const pollForResult = async () => {
        const pollResult = await executionApi.getExecutionStatus(executionId);
        
        if (pollResult.status === 'completed') {
          const execTime = Date.now() - executionStartRef.current;
          setExecutionTime(execTime);
          setResult(pollResult);
          setOutput(pollResult.output || '');
          setStatus(EXECUTION_STATUS.SUCCESS);
          return pollResult;
        }
        
        if (pollResult.status === 'error') {
          setError(pollResult.error || 'Execution failed');
          setStatus(EXECUTION_STATUS.ERROR);
          return pollResult;
        }

        // Continue polling
        pollTimeoutRef.current = setTimeout(pollForResult, pollInterval);
      };

      // Start polling with timeout
      const timeoutId = setTimeout(() => {
        if (pollTimeoutRef.current) {
          clearTimeout(pollTimeoutRef.current);
        }
        setStatus(EXECUTION_STATUS.TIMEOUT);
        setError('Execution timed out');
      }, timeout);

      try {
        return await pollForResult();
      } finally {
        clearTimeout(timeoutId);
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Execution failed';
      setError(errorMessage);
      setStatus(EXECUTION_STATUS.ERROR);
      throw err;
    }
  }, [pollInterval, timeout]);

  /**
   * Cancel running execution
   * @returns {Promise<void>}
   */
  const cancel = useCallback(async () => {
    if (result?.id) {
      try {
        await executionApi.cancelExecution(result.id);
      } catch (e) {
        console.warn('Failed to cancel execution:', e);
      }
    }
    
    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
    }
    
    setStatus(EXECUTION_STATUS.IDLE);
  }, [result]);

  /**
   * Reset execution state
   */
  const reset = useCallback(() => {
    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
    }
    
    setStatus(EXECUTION_STATUS.IDLE);
    setResult(null);
    setError(null);
    setOutput('');
    setExecutionTime(null);
  }, []);

  /**
   * Get supported languages
   * @returns {Promise<Array>} List of supported languages
   */
  const getLanguages = useCallback(async () => {
    try {
      return await executionApi.getSupportedLanguages();
    } catch (e) {
      console.warn('Failed to fetch languages:', e);
      return [];
    }
  }, []);

  /**
   * Get execution history
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Execution history
   */
  const getHistory = useCallback(async (params = {}) => {
    try {
      return await executionApi.getExecutionHistory(params);
    } catch (e) {
      console.warn('Failed to fetch history:', e);
      return { results: [], count: 0 };
    }
  }, []);

  /**
   * Get execution statistics
   * @returns {Promise<Object>} Execution stats
   */
  const getStats = useCallback(async () => {
    try {
      return await executionApi.getExecutionStats();
    } catch (e) {
      console.warn('Failed to fetch stats:', e);
      return null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollTimeoutRef.current) {
        clearTimeout(pollTimeoutRef.current);
      }
    };
  }, []);

  return {
    // State
    status,
    result,
    error,
    output,
    executionTime,
    isRunning: status === EXECUTION_STATUS.RUNNING,
    isSuccess: status === EXECUTION_STATUS.SUCCESS,
    isError: status === EXECUTION_STATUS.ERROR,
    isTimeout: status === EXECUTION_STATUS.TIMEOUT,
    isIdle: status === EXECUTION_STATUS.IDLE,
    
    // Actions
    execute,
    cancel,
    reset,
    
    // Helpers
    getLanguages,
    getHistory,
    getStats,
  };
}

export default useExecution;