#!/bin/bash

# PDF Processing Dependencies Installation Script
# This script installs the required Python packages for PDF processing

echo "🔧 Installing PDF Processing Dependencies..."

# Check if we're in a conda environment
if [[ "$CONDA_DEFAULT_ENV" ]]; then
    echo "📦 Detected conda environment: $CONDA_DEFAULT_ENV"
    
    # Install using conda where possible, pip for others
    echo "Installing PyPDF2..."
    pip install PyPDF2>=3.0.0
    
    echo "Installing PyMuPDF..."
    pip install PyMuPDF>=1.23.0
    
    echo "Installing/Updating Pillow..."
    conda install pillow>=10.0.0 -c conda-forge -y || pip install Pillow>=10.0.0
    
    echo "Installing python-magic..."
    pip install python-magic>=0.4.27
    
    echo "Installing pdfplumber (optional)..."
    pip install pdfplumber>=0.9.0
    
else
    echo "📦 Using pip to install dependencies..."
    
    # Install using pip
    pip install PyPDF2>=3.0.0
    pip install PyMuPDF>=1.23.0
    pip install Pillow>=10.0.0
    pip install python-magic>=0.4.27
    pip install pdfplumber>=0.9.0
fi

echo "✅ PDF processing dependencies installed successfully!"

# Test imports
echo "🧪 Testing imports..."
python -c "
try:
    import PyPDF2
    print('✅ PyPDF2 imported successfully')
except ImportError as e:
    print('❌ PyPDF2 import failed:', e)

try:
    import fitz  # PyMuPDF
    print('✅ PyMuPDF (fitz) imported successfully')
except ImportError as e:
    print('❌ PyMuPDF import failed:', e)

try:
    from PIL import Image
    print('✅ Pillow imported successfully')
except ImportError as e:
    print('❌ Pillow import failed:', e)

try:
    import magic
    print('✅ python-magic imported successfully')
except ImportError as e:
    print('❌ python-magic import failed:', e)

try:
    import pdfplumber
    print('✅ pdfplumber imported successfully')
except ImportError as e:
    print('❌ pdfplumber import failed:', e)
"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📝 Notes:"
echo "   - PyPDF2: Basic PDF reading and metadata extraction"
echo "   - PyMuPDF: Advanced PDF processing and preview generation"
echo "   - Pillow: Image processing for metadata extraction"
echo "   - python-magic: Better MIME type detection"
echo "   - pdfplumber: Alternative PDF text extraction (optional)"
echo ""
echo "🚀 You can now use the PDF processing features in your application!"