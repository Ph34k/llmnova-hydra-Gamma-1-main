# Phase 4: Multimedia Generation - Implementation Plan

## Overview

This plan outlines the implementation of Phase 4 multimedia generation capabilities for the Gamma Engine. The goal is to add three new tool categories that enable the AI agent to generate visual and presentation content:

1. **Image Generation** - Generate images using OpenAI's DALL-E API
2. **Slide Generation** - Create presentation slides in PDF and PPTX formats
3. **Diagram Generation** - Generate technical diagrams using Mermaid.js and PlantUML

These tools will follow the exact same patterns established in Phase 2, including:
- Inheriting from the `Tool` base class
- Using Google Style docstrings
- Comprehensive parameter validation
- Proper error handling
- Full test coverage

## User Review Required

> [!IMPORTANT]
> **API Key Dependencies**: Image generation requires an OpenAI API key (already configured). Slide generation will use python-pptx and reportlab (open source). Diagram generation requires graphviz for PlantUML rendering.

> [!IMPORTANT]
> **New Dependencies**: This implementation will add the following dependencies:
> - `python-pptx>=0.6.23` - For PowerPoint generation
> - `reportlab>=4.0.0` - For PDF generation  
> - `Pillow>=10.0.0` - For image manipulation
> - `plantuml` - For PlantUML diagram rendering (command-line tool)

## Proposed Changes

### Multimedia Tools

#### [NEW] [multimodal_tools.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/gamma_engine/tools/multimodal_tools.py)

Create a new module containing three tool classes:

**1. ImageGenerationTool**
- Uses OpenAI DALL-E API to generate images from text prompts
- Parameters:
  - `prompt` (str): Description of the image to generate
  - `size` (str): Image size - "1024x1024", "1792x1024", or "1024x1792"
  - `quality` (str): "standard" or "hd"
  - `output_path` (str): Where to save the generated image
- Returns: Path to saved image or error message
- Integrates with existing `LLMProvider` OpenAI client

**2. SlideGenerationTool**
- Generates presentation slides from structured content
- Parameters:
  - `title` (str): Presentation title
  - `slides` (list): Array of slide objects with title and content
  - `output_path` (str): Where to save the presentation
  - `format` (str): Output format - "pptx" or "pdf"
  - `theme` (str): Optional theme - "default", "dark", or "minimal"
- Returns: Path to generated presentation or error message
- Uses python-pptx for PPTX, reportlab for PDF

**3. DiagramGenerationTool**
- Generates technical diagrams from markup languages
- Parameters:
  - `content` (str): Diagram definition in Mermaid or PlantUML syntax
  - `diagram_type` (str): "mermaid" or "plantuml"
  - `output_path` (str): Where to save the diagram
  - `format` (str): Output format - "png" or "svg"
- Returns: Path to generated diagram or error message
- Uses mermaid-cli for Mermaid (via subprocess), plantuml JAR for PlantUML

---

### Integration Updates

#### [MODIFY] [tools/__init__.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/gamma_engine/tools/__init__.py)

Update the exports to include the new multimodal tools:
```python
from .multimodal_tools import (
    ImageGenerationTool,
    SlideGenerationTool, 
    DiagramGenerationTool
)

__all__ = [
    # ... existing exports ...
    # Multimodal
    'ImageGenerationTool',
    'SlideGenerationTool',
    'DiagramGenerationTool',
]
```

#### [MODIFY] [requirements.txt](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/requirements.txt)

Add new dependencies:
```
python-pptx>=0.6.23
reportlab>=4.0.0
Pillow>=10.0.0
```

#### [MODIFY] [pyproject.toml](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/pyproject.toml)

Add the same dependencies to the project configuration.

---

### Testing

#### [NEW] [test_phase4_multimodal.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/tests/test_phase4_multimodal.py)

Comprehensive test suite for all multimodal tools following the pattern from `test_phase2_tools.py`:

**TestImageGenerationTool**:
- Test successful image generation (mocked API)
- Test parameter validation
- Test error handling for API failures
- Test output file creation

**TestSlideGenerationTool**:
- Test PPTX generation
- Test PDF generation
- Test different themes
- Test multi-slide presentations
- Test error handling

**TestDiagramGenerationTool**:
- Test Mermaid diagram generation
- Test PlantUML diagram generation
- Test different output formats (PNG, SVG)
- Test syntax validation
- Test error handling

**TestMultimodalIntegration**:
- Verify all tools have valid schemas
- Verify tools are properly exported

---

### Documentation

#### [MODIFY] [TOOLS.md](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/docs/TOOLS.md)

Add a new "Multimodal Generation" section documenting:
- Each tool's purpose and capabilities
- Parameter descriptions and examples
- Usage examples for each tool
- Requirements and setup (API keys, external tools)

#### [MODIFY] [PROGRESSO.md](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/docs/PROGRESSO.md)

Update Phase 4 status to mark items complete after implementation and testing.

## Verification Plan

### Automated Tests

Run the comprehensive test suite with:
```bash
cd c:\Users\henri_6m1hz7q\Downloads\llmnova-hydra-Gamma-1
python -m pytest tests/test_phase4_multimodal.py -v
```

This will verify:
- All tools initialize correctly with proper schemas
- Parameter validation works as expected
- Error handling is robust
- Each tool's core functionality works (with mocked external dependencies)

### Integration Tests

Verify tools are properly integrated:
```bash
python -m pytest tests/test_phase2_tools.py::TestToolIntegration::test_all_tools_have_schemas -v
```

This should now include the 3 new multimodal tools in the count.

### Manual Verification

> [!WARNING]
> **Manual Testing Required**: Some features require real API keys and external tools to fully test. Please confirm:

1. **Image Generation**: 
   - Set `OPENAI_API_KEY` environment variable
   - Run a test script to generate a sample image
   - Verify the image file is created and viewable

2. **Slide Generation**:
   - Generate a sample PPTX presentation
   - Open in PowerPoint/LibreOffice to verify formatting
   - Generate a sample PDF presentation  
   - Open in PDF viewer to verify content

3. **Diagram Generation**:
   - For Mermaid: Install mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`)
   - For PlantUML: Ensure Java is installed and plantuml.jar is available
   - Generate sample diagrams in both formats
   - Verify SVG and PNG outputs are correct

**Suggested Manual Test Script** (will be created as `examples/test_multimodal.py`):
```python
# This script will demonstrate each tool
from gamma_engine.tools import (
    ImageGenerationTool,
    SlideGenerationTool,
    DiagramGenerationTool
)

# Test image generation
# Test slide generation
# Test diagram generation
```

Would you like me to proceed with this implementation plan, or would you like to modify any aspects?
