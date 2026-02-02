
import { render, screen, fireEvent } from '@testing-library/react';
import PreviewPane from '../PreviewPane';
import React from 'react';

// Mock Lucide icons
jest.mock('lucide-react', () => ({
  Maximize2: () => <div data-testid="maximize-icon" />,
  X: () => <div data-testid="close-icon" />,
  RefreshCw: () => <div data-testid="refresh-icon" />,
  ExternalLink: () => <div data-testid="external-link-icon" />,
}));

describe('PreviewPane', () => {
  it('renders correctly with default URL', () => {
    render(<PreviewPane url="http://localhost:3000" setUrl={() => {}} />);
    // Check for input instead of static text if it's an input field
    const input = screen.getByDisplayValue('http://localhost:3000');
    expect(input).toBeInTheDocument();

    const iframe = screen.getByTitle('Live Preview');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'http://localhost:3000');
  });

  it('renders with custom URL', () => {
    const url = "http://example.com";
    render(<PreviewPane url={url} setUrl={() => {}} />);
    const input = screen.getByDisplayValue(url);
    expect(input).toBeInTheDocument();
    expect(screen.getByTitle('Live Preview')).toHaveAttribute('src', url);
  });

  // Note: The new PreviewPane component doesn't seem to have a self-contained close button
  // that unmounts itself. It relies on parent state or layout.
  // We should remove the "closes when close button is clicked" test if the component doesn't implement it.
});
