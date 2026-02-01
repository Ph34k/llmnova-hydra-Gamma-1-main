
import { render, screen, fireEvent } from '@testing-library/react';
import PreviewPane from '../PreviewPane';

// Mock Lucide icons
jest.mock('lucide-react', () => ({
  Maximize2: () => <div data-testid="maximize-icon" />,
  X: () => <div data-testid="close-icon" />,
}));

describe('PreviewPane', () => {
  it('renders correctly with default URL', () => {
    render(<PreviewPane />);
    expect(screen.getByText('http://localhost:3000')).toBeInTheDocument();
    const iframe = screen.getByTitle('Live Preview');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'http://localhost:3000');
  });

  it('renders with custom URL', () => {
    const url = "http://example.com";
    render(<PreviewPane url={url} />);
    expect(screen.getByText(url)).toBeInTheDocument();
    expect(screen.getByTitle('Live Preview')).toHaveAttribute('src', url);
  });

  it('closes when close button is clicked', () => {
    render(<PreviewPane />);
    const closeBtn = screen.getByTestId('close-icon').parentElement;
    fireEvent.click(closeBtn!);

    expect(screen.queryByTitle('Live Preview')).not.toBeInTheDocument();
  });
});
