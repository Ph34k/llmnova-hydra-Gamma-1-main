
import { render, screen } from '@testing-library/react';
import Workspace from '../Workspace';

// Mock Lucide icons
jest.mock('lucide-react', () => ({
  Folder: () => <div data-testid="folder-icon" />,
  FileCode: () => <div data-testid="file-code-icon" />,
  ChevronRight: () => <div data-testid="chevron-right-icon" />,
  ChevronDown: () => <div data-testid="chevron-down-icon" />,
  RefreshCw: () => <div data-testid="refresh-icon" />,
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
  });

  it('renders workspace structure', () => {
    render(<Workspace ws={mockWs} />);
    expect(screen.getByText('Workspace')).toBeInTheDocument();
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    // Check mock tree items
    expect(screen.getByText('src')).toBeInTheDocument();
    expect(screen.getByText('main.py')).toBeInTheDocument();
  });

  it('shows no file selected initially', () => {
    render(<Workspace ws={mockWs} />);
    expect(screen.getByText('No file selected')).toBeInTheDocument();
  });
});
