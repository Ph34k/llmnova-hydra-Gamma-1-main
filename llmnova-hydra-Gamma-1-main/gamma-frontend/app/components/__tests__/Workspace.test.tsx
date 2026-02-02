
import { render, screen, waitFor } from '@testing-library/react';
import Workspace from '../Workspace';
import React from 'react';

// Mock Lucide icons
jest.mock('lucide-react', () => ({
  Folder: () => <div data-testid="folder-icon" />,
  FileCode: () => <div data-testid="file-code-icon" />,
  ChevronRight: () => <div data-testid="chevron-right-icon" />,
  ChevronDown: () => <div data-testid="chevron-down-icon" />,
  RefreshCw: () => <div data-testid="refresh-icon" />,
  Save: () => <div data-testid="save-icon" />,
  Loader2: () => <div data-testid="loader-icon" />,
}));

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: () => <div data-testid="monaco-editor" />,
}));

describe('Workspace', () => {
  let mockWs: any;

  beforeEach(() => {
    mockWs = {
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    };

    global.fetch = jest.fn(() =>
        Promise.resolve({
            ok: true,
            json: () => Promise.resolve([
                { name: 'src', type: 'directory', path: '/src', children: [
                    { name: 'main.py', type: 'file', path: '/src/main.py' }
                ]},
                { name: 'README.md', type: 'file', path: '/README.md' }
            ])
        })
    ) as jest.Mock;
  });

  it('renders workspace structure', async () => {
    render(<Workspace ws={mockWs} sessionId="test-session" />);
    expect(screen.getByText('Workspace')).toBeInTheDocument();
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();

    // Wait for file fetch
    await waitFor(() => {
        expect(screen.getByText('src')).toBeInTheDocument();
        // main.py is nested and folder closed by default
        expect(screen.getByText('README.md')).toBeInTheDocument();
    });
  });

  it('shows no file selected initially', () => {
    render(<Workspace ws={mockWs} sessionId="test-session" />);
    expect(screen.getByText('No file selected')).toBeInTheDocument();
  });
});
