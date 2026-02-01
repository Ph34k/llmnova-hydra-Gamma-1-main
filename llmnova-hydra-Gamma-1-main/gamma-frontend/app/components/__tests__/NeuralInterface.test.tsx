
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NeuralInterface from '../NeuralInterface';
import React from 'react';

// Mock Lucide icons
jest.mock('lucide-react', () => ({
  Send: () => <div data-testid="send-icon" />,
  Terminal: () => <div data-testid="terminal-icon" />,
  Cpu: () => <div data-testid="cpu-icon" />,
  Sparkles: () => <div data-testid="sparkles-icon" />,
  Download: () => <div data-testid="download-icon" />,
  User: () => <div data-testid="user-icon" />,
  Bot: () => <div data-testid="bot-icon" />,
  Wrench: () => <div data-testid="wrench-icon" />,
  Paperclip: () => <div data-testid="paperclip-icon" />,
  File: () => <div data-testid="file-icon" />,
}));

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ filename: 'test.pdf' }),
    blob: () => Promise.resolve(new Blob(['pdf content'])),
  })
) as jest.Mock;

global.URL.createObjectURL = jest.fn();
global.URL.revokeObjectURL = jest.fn();

describe('NeuralInterface', () => {
  let mockWs: any;

  beforeEach(() => {
    mockWs = {
      send: jest.fn(),
      addEventListener: jest.fn((event: string, cb: any) => {
          if (event === 'open') {
              // Immediately simulate open to ready state
              setTimeout(() => cb(), 0);
          }
      }),
      removeEventListener: jest.fn(),
      readyState: 1, // OPEN
    };
  });

  it('renders initial state correctly', () => {
    render(<NeuralInterface ws={mockWs} />);
    expect(screen.getByText('GAMMA ENGINE')).toBeInTheDocument();
    expect(screen.getByText('System Status')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask Gamma anything/i)).toBeInTheDocument();
  });

  it('handles sending messages', async () => {
    render(<NeuralInterface ws={mockWs} />);

    // Wait for effect to trigger and enable button
    await waitFor(() => expect(screen.getByText(/ready/i)).toBeInTheDocument());

    const input = screen.getByPlaceholderText(/Ask Gamma anything/i);

    // Simulate user typing
    fireEvent.change(input, { target: { value: 'Hello Gamma' } });
    expect(input).toHaveValue('Hello Gamma');

    // Click send
    const sendBtn = screen.getByTestId('send-icon').parentElement;

    // Ensure the button is enabled and clickable
    expect(sendBtn).not.toBeDisabled();

    fireEvent.click(sendBtn!);

    // Since mockWs is a fresh mock in beforeEach, checking it directly should work
    // However, if the component logic is complex, it might be missed.
    // Let's verify the input value is what we expect.
    // waitFor is needed because state updates might be async
    await waitFor(() => {
        expect(mockWs.send).toHaveBeenCalledWith(JSON.stringify({ message: 'Hello Gamma' }));
    });
    expect(input).toHaveValue(''); // Should clear input
  });

  it('displays incoming messages', () => {
    let messageCallback: any;
    // Capture the callback on initial render
    mockWs.addEventListener.mockImplementation((event: string, cb: any) => {
      if (event === 'message') messageCallback = cb;
    });

    render(<NeuralInterface ws={mockWs} />);

    // Trigger incoming message
    React.act(() => {
        if (messageCallback) {
            messageCallback({ data: JSON.stringify({ type: 'message', content: 'Hello User' }) });
        }
    });

    // Use getAllByText and check if at least one exists, or target specific structure
    const messages = screen.getAllByText('Hello User');
    expect(messages.length).toBeGreaterThan(0);
  });

  it('handles file uploads', async () => {
    const { container } = render(<NeuralInterface ws={mockWs} />);

    // Wait for ready
    await waitFor(() => expect(screen.getByText(/ready/i)).toBeInTheDocument());

    const file = new File(['dummy content'], 'test.txt', { type: 'text/plain' });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;

    expect(input).toBeInTheDocument();

    // Mock fetch response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ filename: 'uploaded_test.txt' })
    });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/files/upload'),
            expect.objectContaining({
                method: 'POST',
                body: expect.any(FormData)
            })
        );
    });

    // Check if the file upload message appears
    await waitFor(() => {
         const msgs = screen.getAllByText(/File uploaded: uploaded_test.txt/i);
         expect(msgs.length).toBeGreaterThan(0);
    });
  });

  it('handles tool calls and results', async () => {
    render(<NeuralInterface ws={mockWs} />);

    let messageCallback: any;
    mockWs.addEventListener.mockImplementation((event: string, cb: any) => {
      if (event === 'message') messageCallback = cb;
    });

    // Simulate tool call
    // Note: The NeuralInterface component might filter unknown types or handle tool calls differently than 'message'.
    // Looking at the code in NeuralInterface.tsx:
    // } else if (data.type === 'tool_call') {
    //    setMessages(prev => [...prev, { role: 'tool-call', content: `Executing ${data.tool}...`, details: data.args }]);

    React.act(() => {
        if (messageCallback) {
            messageCallback({ data: JSON.stringify({
                type: 'tool_call',
                tool: 'read_file',
                args: { path: 'test.txt' }
            })});
        }
    });

    // Wait for the update
    // We expect the message to be added to the state.
    // However, the test environment seems to have trouble finding the update in the DOM despite act() and waitFor().
    // This might be due to how state updates are batched or key conflicts in the list if any.
    // For now, let's verify that the callback (if any logic depends on it) was called or check message length.

    // We can't easily check internal state 'messages'.
    // Let's try one more time to find by generic text match, ignoring role/structure issues.
    await waitFor(() => {
         const elements = screen.getAllByText((content) => content.includes("Executing read_file"));
         expect(elements.length).toBeGreaterThan(0);
    });

    // Simulate tool result
    React.act(() => {
        if (messageCallback) {
            messageCallback({ data: JSON.stringify({
                type: 'tool_result',
                tool: 'read_file',
                result: 'File content here'
            })});
        }
    });

    expect(screen.getByText(/Result from read_file/i)).toBeInTheDocument();
  });
});
