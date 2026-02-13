
import { render, screen } from '@testing-library/react';
import Page from '../page';

// Mock components
jest.mock('../components/NeuralInterface', () => () => <div data-testid="neural-interface" />);
jest.mock('../components/Workspace', () => () => <div data-testid="workspace" />);
jest.mock('../components/PreviewPane', () => () => <div data-testid="preview-pane" />);
// Mock other components if they are rendered by default
jest.mock('../components/Dashboard', () => () => <div data-testid="dashboard" />);
jest.mock('../components/Terminal', () => () => <div data-testid="terminal" />);
jest.mock('../components/Settings', () => () => <div data-testid="settings" />);
jest.mock('../components/Sidebar', () => ({ activeView, setActiveView }: any) => (
    <div data-testid="sidebar">
        <button onClick={() => setActiveView('chat')}>Chat</button>
        <button onClick={() => setActiveView('code')}>Code</button>
    </div>
));

// Mock WebSocket
global.WebSocket = jest.fn(() => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  close: jest.fn(),
})) as any;

describe('Home Page', () => {
  it('renders all main components', () => {
    // In the advanced layout, NeuralInterface (chat) is active by default.
    // Workspace (code) is also active as a secondary view by default.
    // PreviewPane might be conditionally rendered.

    render(<Page />);

    // Check for Sidebar
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();

    // Check for active views (Chat and Code)
    expect(screen.getByTestId('neural-interface')).toBeInTheDocument();

    // In advanced layout logic: if view is chat, setSecondaryView is 'code'.
    // So both should be present.
    expect(screen.getByTestId('workspace')).toBeInTheDocument();

    // PreviewPane depends on secondaryView state. If it's code, preview pane is hidden.
    // So we shouldn't expect it initially unless we navigate.
    expect(screen.queryByTestId('preview-pane')).not.toBeInTheDocument();
  });
});
