
import { render, screen } from '@testing-library/react';
import Page from '../page';

// Mock components
jest.mock('../components/NeuralInterface', () => () => <div data-testid="neural-interface" />);
jest.mock('../components/Workspace', () => () => <div data-testid="workspace" />);
jest.mock('../components/PreviewPane', () => () => <div data-testid="preview-pane" />);

// Mock WebSocket
global.WebSocket = jest.fn(() => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  close: jest.fn(),
})) as any;

describe('Home Page', () => {
  it('renders all main components', () => {
    render(<Page />);
    expect(screen.getByTestId('neural-interface')).toBeInTheDocument();
    expect(screen.getByTestId('workspace')).toBeInTheDocument();
    expect(screen.getByTestId('preview-pane')).toBeInTheDocument();
  });
});
