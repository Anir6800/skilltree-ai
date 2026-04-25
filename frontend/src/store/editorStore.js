/**
 * SkillTree AI - Editor Store
 * Zustand store for persisting editor state per quest
 * @module store/editorStore
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const DEFAULT_TEMPLATES = {
  python: `# Write your solution here\n\ndef solution():\n    pass\n`,
  javascript: `// Write your solution here\n\nfunction solution() {\n  \n}\n`,
  cpp: `// Write your solution here\n#include <iostream>\nusing namespace std;\n\nint main() {\n    \n    return 0;\n}\n`,
  java: `// Write your solution here\npublic class Solution {\n    public static void main(String[] args) {\n        \n    }\n}\n`,
  go: `// Write your solution here\npackage main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("")\n}\n`,
};

const useEditorStore = create(
  persist(
    (set, get) => ({
      // Per-quest code state: { [questId]: { code, language } }
      questStates: {},

      // AI mode toggle
      aiModeEnabled: false,

      // Get code for a specific quest
      getQuestCode: (questId, starterCode, language) => {
        const state = get().questStates[questId];
        if (state?.code !== undefined) return state.code;
        return starterCode || DEFAULT_TEMPLATES[language] || '// Start coding...\n';
      },

      // Get language for a specific quest
      getQuestLanguage: (questId) => {
        return get().questStates[questId]?.language || 'python';
      },

      // Save code for a quest
      setQuestCode: (questId, code) => {
        set((state) => ({
          questStates: {
            ...state.questStates,
            [questId]: {
              ...state.questStates[questId],
              code,
            },
          },
        }));
      },

      // Save language for a quest
      setQuestLanguage: (questId, language) => {
        set((state) => ({
          questStates: {
            ...state.questStates,
            [questId]: {
              ...state.questStates[questId],
              language,
            },
          },
        }));
      },

      // Reset quest code to starter
      resetQuestCode: (questId, starterCode, language) => {
        const resetCode = starterCode || DEFAULT_TEMPLATES[language] || '// Start coding...\n';
        set((state) => ({
          questStates: {
            ...state.questStates,
            [questId]: {
              ...state.questStates[questId],
              code: resetCode,
            },
          },
        }));
        return resetCode;
      },

      // Toggle AI mode
      toggleAiMode: () => set((state) => ({ aiModeEnabled: !state.aiModeEnabled })),
      setAiMode: (enabled) => set({ aiModeEnabled: enabled }),
    }),
    {
      name: 'skilltree-editor-state',
      partialize: (state) => ({
        questStates: state.questStates,
        aiModeEnabled: state.aiModeEnabled,
      }),
    }
  )
);

export { DEFAULT_TEMPLATES };
export default useEditorStore;
